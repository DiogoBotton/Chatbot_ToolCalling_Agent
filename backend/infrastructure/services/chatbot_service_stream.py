import time
from typing import List, Literal
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, ToolMessage
from domains.enums.message_type import MessageType
from domains.conversation_history import ConversationHistory
from infrastructure.tools.process_tools import create_process_tool, get_process_tool, update_process_status_tool

class ChatbotService:
    def __init__(self):
        self.sys_prompt = """
            Você é um assistente especializado em processos de visto.
    
            Você pode:
            - Criar processo de visto
            - Consultar processo de visto
            - Atualizar status de processo de visto
    
            Sempre utilize as ferramentas disponíveis para executar ações.
            Nunca invente respostas.
            Pode responder outras perguntas também.
            """
        self.llm, self.llm_with_tools = self.model_openai()
        
        # Mapeia manualmente todas as ferramentas disponíveis para poder chamá-las dinamicamente depois
        self.tool_map = {
                "create_process_tool": create_process_tool,
                "get_process_tool": get_process_tool,
                "update_process_status_tool": update_process_status_tool
            }

    def model_openai(self, model_name = "gpt-5.4-mini", temperature = 0, reasoning_effort: Literal["none", "low", "medium", "high", "xhigh"] = "high"):
        """
        Acessa o modelo do Chat GPT pela API.
        Retorna o modelo normal e o modelo com as ferramentas acopladas (bind_tools).
            - O modelo normal é utilizado para responder perguntas simples, que não precisam de ferramentas.
            - O modelo com ferramentas acopladas é utilizado para identificar quando o modelo precisa chamar uma ferramenta e qual ferramenta chamar.
        """
        llm = AzureChatOpenAI(model_name=model_name,
                              temperature=temperature,
                              api_version="2025-04-01-preview",
                              reasoning_effort=reasoning_effort,
                              output_version="responses/v1",
                              max_retries=2)
        
        # llm = ChatOpenAI(model = model_name, temperature = temperature, reasoning_effort=reasoning_effort, max_retries=2, output_version="responses/v1")
        llm_with_tools = llm.bind_tools([create_process_tool, get_process_tool, update_process_status_tool],
                                        parallel_tool_calls=False) # -> Força chamadas sequenciais, isto pois temos apenas um ciclo de chamada de ferramentas (não é necessário caso for um agente)
        return llm, llm_with_tools

    def build_messages(self, user_query: str, chat_history: List[BaseMessage]):
        """
        Gera a lista de mensagens para passar como contexto para o modelo. A lista é composta por:
        - SystemMessage: mensagem de sistema (prompt) para orientar o comportamento do modelo
        - BaseMessage: mensagens anteriores da conversa (chat_history)
        - HumanMessage: mensagem atual do usuário (user_query)
        """
        system = SystemMessage(content=self.sys_prompt)

        return [system] + chat_history + [HumanMessage(content=user_query)]
    
    def execute_llm_with_tools(self, messages: List[BaseMessage], new_messages: List[ConversationHistory]):
        # Identifica se o modelo precisa chamar uma ferramenta ou não
        response = self.llm_with_tools.invoke(messages)
        
        # Mensagem da resposta final do modelo, sem chamar a ferramenta
        if not response.tool_calls:
            return response, messages
        
        # Mensagem de chamada de ferramentas
        new_messages.append(ConversationHistory(
            role=MessageType.ASSISTANT,
            tool_calls=response.tool_calls))
        
        # Adiciona o response a lista de mensagens para o modelo saber que houve necessidade de chamar uma ferramenta
        messages.append(response)
        
        # Caso o modelo precise chamar uma ferramenta
        for tool_call in response.tool_calls:
            
            # Busca a função do tool_map (dicionário) pelo nome da ferramenta
            tool_func = self.tool_map.get(tool_call["name"])
            if tool_func:
                try:
                    # Caso achar a ferramenta, chama a função passando os parâmetros (args) necessários
                    tool_response = tool_func.invoke(tool_call["args"])
                except Exception as e:
                    tool_response = {"error": str(e)}
                    
                # Adiciona o resultado da ferramenta como um ToolMessage para o modelo usar como contexto para responder a pergunta
                messages.append(ToolMessage(
                    content=str(tool_response),
                    tool_call_id=tool_call["id"])) # Necessário o tool_call_id para o modelo entender de qual chamada de ferramenta aquela resposta se refere
                
                # Mensagem de resultado da ferramenta
                new_messages.append(ConversationHistory(
                    role=MessageType.TOOL,
                    content=str(tool_response),
                    tool_call_id=tool_call["id"]))
        
        return None, messages
    
    def execute_streaming(self, messages: List[BaseMessage], new_messages: List[ConversationHistory]):
        full_content = ""
        
        # Finalmente, chama o modelo novamente (sem tools) passando toda a conversa (requisição para ferramenta + resposta) para gerar a resposta final
        for chunk in self.llm.stream(messages):
            for block in chunk.content:
                if block['type'] == 'reasoning':
                    for summary in block["summary"]:
                        full_content += summary
                        yield summary
                elif block['type'] == 'text':
                    for chunk_txt in block["text"]:
                        full_content += chunk_txt
                        yield chunk_txt
        
        # Salva mensagem final do modelo
        new_messages.append(ConversationHistory(
            role=MessageType.ASSISTANT,
            content=full_content))

    def _extract_text(self, content) -> str:
        """Extrai só o texto da resposta, ignorando blocos de raciocínio.
        Necessário pois a Responses API retorna content como lista de blocos."""
        if isinstance(content, list):
            return "".join(block["text"] for block in content if block.get("type") == "text")
        return content or ""

    def get_response_stream(self, user_query: str, chat_history: List[BaseMessage]) -> tuple[str, List[ConversationHistory]]:
        # A edição de new_messages ocorre com referência de memória
        new_messages = []
        messages = self.build_messages(user_query, chat_history)

        response, messages = self.execute_llm_with_tools(messages, new_messages)
        
        if response:
            def generator():
                for block in response.content:
                    if block['type'] == 'reasoning':
                        for summary in block["summary"]:
                            time.sleep(0.005) # Simula delay de streaming
                            yield summary
                    elif block['type'] == 'text':
                        for chunk_txt in block["text"]:
                            time.sleep(0.005) # Simula delay de streaming
                            yield chunk_txt
                                
            new_messages.append(ConversationHistory(
                role=MessageType.ASSISTANT,
                content=self._extract_text(response.content)))
            
            return generator(), new_messages
        
        # Caso precise de chamar uma ferramenta, gera a resposta final com o contexto atualizado (mensagem do modelo + resposta da ferramenta)
        return self.execute_streaming(messages, new_messages), new_messages