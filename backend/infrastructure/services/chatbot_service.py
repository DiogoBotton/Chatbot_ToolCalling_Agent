from typing import List
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, ToolMessage
from domains.enums.message_type import MessageType
from domains.conversation_history import ConversationHistory
from infrastructure.tools.process_tools import create_process_tool, get_process_tool, update_process_status_tool

class ChatbotService:
    def __init__(self):
        self.sys_prompt = """
            Você é um assistente especializado em processos de visto.
    
            Você só pode:
            - Criar processo de visto
            - Consultar processo de visto
            - Atualizar status de processo de visto
    
            Sempre utilize as ferramentas disponíveis para executar ações.
            Nunca invente respostas.
            Se a pergunta não estiver relacionada a processos de visto,
            responda: "Só posso ajudar com processos de visto." e diga que tipo de processos que você pode fazer.
            """
        self.llm, self.llm_with_tools = self.model_openai()
        
        # Mapeia manualmente todas as ferramentas disponíveis para poder chamá-las dinamicamente depois
        self.tool_map = {
                "create_process_tool": create_process_tool,
                "get_process_tool": get_process_tool,
                "update_process_status_tool": update_process_status_tool
            }

    def model_openai(self, model_name = "gpt-4o-mini", temperature = 0):
        """
        Acessa o modelo do Chat GPT pela API.
        Retorna o modelo normal e o modelo com as ferramentas acopladas (bind_tools).
            - O modelo normal é utilizado para responder perguntas simples, que não precisam de ferramentas.
            - O modelo com ferramentas acopladas é utilizado para identificar quando o modelo precisa chamar uma ferramenta e qual ferramenta chamar.
        """
        llm = ChatOpenAI(model = model_name, temperature = temperature)
        llm_with_tools = llm.bind_tools([create_process_tool, get_process_tool, update_process_status_tool])
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
        
        # Caso o modelo precise chamar uma ferramenta
        for tool_call in response.tool_calls:
            # Adiciona o response a lista de mensagens para o modelo saber que houve necessidade de chamar uma ferramenta
            messages.append(response) # TODO: N seria melhor adicionar um AIMessage?
            
            # Busca a função do tool_map (dicionário) pelo nome da ferramenta
            tool_func = self.tool_map.get(tool_call["name"])
            if tool_func:
                # Mensagem de chamada de ferramenta
                new_messages.append(ConversationHistory(
                    role=MessageType.ASSISTANT,
                    tool_calls=[tool_call])) # Sempre salva tool_calls como uma lista
                
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
            if chunk.content:
                full_content += chunk.content
                yield chunk.content
        
        # Salva mensagem final do modelo
        new_messages.append(ConversationHistory(
            role=MessageType.ASSISTANT,
            content=full_content))

    def get_response_stream(self, user_query: str, chat_history: List[BaseMessage]) -> tuple[str, List[ConversationHistory]]:
        # A edição de new_messages ocorre com referência de memória
        new_messages = []
        messages = self.build_messages(user_query, chat_history)

        response, messages = self.execute_llm_with_tools(messages, new_messages)
        
        if response:
            def generator(): # TODO: Simular streaming mesmo quando não tem chamada de ferramenta, para não perder a experiência de streaming (for char in response.content)?
                yield response.content
                                
            new_messages.append(ConversationHistory(
                role=MessageType.ASSISTANT,
                content=response.content))
            
            return generator(), new_messages
        
        # Caso precise de chamar uma ferramenta, gera a resposta final com o contexto atualizado (mensagem do modelo + resposta da ferramenta)
        return self.execute_streaming(messages, new_messages), new_messages