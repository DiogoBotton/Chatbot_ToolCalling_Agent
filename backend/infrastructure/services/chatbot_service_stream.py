import json
import time
from typing import List, Literal
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, ToolMessage
from domains.enums.message_type import MessageType
from domains.conversation_history import ConversationHistory
from infrastructure.tools.process_tools import create_process_tool, get_process_tool, update_process_status_tool

class ChatbotService:
    def __init__(self):
        # OBS. Mesmo especificando no prompt, alguns modelos não raciocinam em português, isso depende do modelo utilizado. 
        # O gpt-5.4-mini por exemplo, não segue essa orientação do prompt.
        self.sys_prompt = """
            Você é um assistente especializado em processos de visto.
    
            Você pode:
            - Criar processo de visto
            - Consultar processo de visto
            - Atualizar status de processo de visto
    
            Sempre utilize as ferramentas disponíveis para executar ações.
            Nunca invente respostas.
            Pode responder outras perguntas também.

            IMPORTANTE: Você DEVE raciocinar, pensar e escrever seu raciocínio EXCLUSIVAMENTE em português brasileiro.
            Isso inclui todo o processo de pensamento, análise e conclusões intermediárias.
            NUNCA use inglês no raciocínio, mesmo que a pergunta seja em outro idioma.
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
            
        Para raciocínio é necessário configurar o parâmetro reasoning (ou reasoning_effort) para que o modelo envie blocos 
        de raciocínio durante a resposta.
        
        O parâmetro output_version="responses/v1" é necessário para acessar a Responses API, que é a única que atualmente 
        suporta o raciocínio em blocos.
        
        O paramêtro summary dentro de reasoning é para configurar o nível de detalhamento do raciocínio, pode ser auto, detailed ou none. 
        O auto é o padrão e o modelo decide o quanto de raciocínio enviar, o detailed força o modelo a enviar todo o raciocínio em blocos separados 
        e o none desativa o envio de blocos de raciocínio.
        """
        llm = AzureChatOpenAI(model_name=model_name,
                              temperature=temperature,
                              api_version="2025-04-01-preview",
                              #reasoning_effort=reasoning_effort,
                              reasoning={
                                  "effort": reasoning_effort,
                                  "summary": "auto" # none | auto | detailed
                              },
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
        
        if not response.tool_calls:
            # Exibe uso de tokens 
            # Exemplo: {'input_tokens': 347, 'output_tokens': 137, 'total_tokens': 484, 'input_token_details': {'cache_read': 0}, 'output_token_details': {'reasoning': 79}})
            print(response.usage_metadata)
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

    def _chunk(self, chunk_type: str, content: str) -> str:
        """Serializa um chunk como JSON line para o frontend."""
        return json.dumps({"type": chunk_type, "content": content}, ensure_ascii=False) + "\n"

    # Aqui acontece streaming real, de raciocinio e resposta final do modelo.
    def execute_streaming(self, messages: List[BaseMessage], new_messages: List[ConversationHistory]):
        full_content = ""

        for chunk in self.llm.stream(messages):
            if not chunk.content:
                continue
            if isinstance(chunk.content, str):
                full_content += chunk.content
                yield self._chunk("text", chunk.content)
            else:
                for block in chunk.content:
                    if not isinstance(block, dict):
                        continue
                    if block.get("type") == "reasoning":
                        for summary in block.get("summary", []):
                            text = summary.get("text", "") if isinstance(summary, dict) else str(summary)
                            if text:
                                yield self._chunk("reasoning", text)
                    elif block.get("type") == "text":
                        text = block.get("text", "")
                        if text:
                            full_content += text
                            yield self._chunk("text", text)

        new_messages.append(ConversationHistory(
            role=MessageType.ASSISTANT,
            content=full_content))

    # Função utilizada pela simulação de streaming
    def _extract_text(self, content) -> str:
        """Extrai só o texto da resposta, ignorando blocos de raciocínio.
        Necessário pois a Responses API retorna content como lista de blocos."""
        if isinstance(content, list):
            return "".join(block["text"] for block in content if block.get("type") == "text")
        return content or ""
    
    # Função utilizada pela simulação de streaming
    def _extract_reasoning(self, content) -> str:
        """Extrai o texto de raciocínio dos blocos da Responses API."""
        if not isinstance(content, list):
            return ""
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "reasoning":
                for summary in block.get("summary", []):
                    text = summary.get("text", "") if isinstance(summary, dict) else str(summary)
                    if text:
                        parts.append(text)
        return "".join(parts)

    def get_response_stream(self, user_query: str, chat_history: List[BaseMessage]) -> tuple[str, List[ConversationHistory]]:
        # A edição de new_messages ocorre com referência de memória
        new_messages = []
        messages = self.build_messages(user_query, chat_history)

        response, messages = self.execute_llm_with_tools(messages, new_messages)
        
        if response:
            def generator():
                """
                Esta função generator apenas simula o streaming, pega o texto inteiro e retorna palavra por palavra com yield.
                """
                for word in self._extract_reasoning(response.content).split():
                    time.sleep(0.015)
                    yield self._chunk("reasoning", word + " ")

                for char in self._extract_text(response.content):
                    time.sleep(0.005)
                    yield self._chunk("text", char)

            new_messages.append(ConversationHistory(
                role=MessageType.ASSISTANT,
                content=self._extract_text(response.content)))

            return generator(), new_messages
        
        # Caso precise de chamar uma ferramenta, gera a resposta final com o contexto atualizado (mensagem do modelo + resposta da ferramenta)
        return self.execute_streaming(messages, new_messages), new_messages