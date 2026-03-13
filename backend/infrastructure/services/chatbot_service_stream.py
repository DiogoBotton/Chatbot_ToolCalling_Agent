import json
import time
from typing import Generator, List, Tuple

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, ToolCall, ToolMessage
from langchain_openai import ChatOpenAI

from domains.enums.message_type import MessageType
from domains.conversation_history import ConversationHistory
from infrastructure.tools.process_tools import create_process_tool, get_process_tool, update_process_status_tool
from infrastructure.tools.rag_tools import search_documents_tool

class ChatbotService:
    def __init__(self):
        self.sys_prompt = """
            Você é um assistente virtual inteligente e versátil.

            Você possui as seguintes capacidades:
            1. **Gerenciamento de processos de visto** — criar, consultar e atualizar status de processos usando as ferramentas de processo.
            2. **Consulta a documentos** — buscar informações nos documentos enviados pelos usuários usando a ferramenta search_documents_tool.

            Regras de decisão:
            - Se o usuário pedir para CRIAR, CONSULTAR ou ATUALIZAR um processo de visto, use as ferramentas de processo.
            - Se o usuário fizer uma PERGUNTA, DÚVIDA ou pedir informações sobre qualquer assunto, SEMPRE use search_documents_tool para buscar a resposta nos documentos disponíveis.
            - Nunca recuse uma pergunta. Se não encontrar a resposta nos documentos, diga que não encontrou informações relevantes nos documentos disponíveis.
            - Nunca invente respostas. Baseie-se sempre no resultado das ferramentas.
            - Quando usar informações dos documentos, cite as fontes na sua resposta.
            """
        self.llm, self.llm_with_tools = self._model_openai()
        
        # Mapeia manualmente todas as ferramentas disponíveis para poder chamá-las dinamicamente depois
        self.tool_map = {
                "create_process_tool": create_process_tool,
                "get_process_tool": get_process_tool,
                "update_process_status_tool": update_process_status_tool,
                "search_documents_tool": search_documents_tool,
            }

    def _model_openai(self, model_name = "gpt-4o-mini", temperature = 0):
        """
        Acessa o modelo do Chat GPT pela API.
        Retorna o modelo normal e o modelo com as ferramentas acopladas (bind_tools).
            - O modelo normal é utilizado para responder perguntas simples, que não precisam de ferramentas.
            - O modelo com ferramentas acopladas é utilizado para identificar quando o modelo precisa chamar uma ferramenta e qual ferramenta chamar.
        """
        llm = ChatOpenAI(model = model_name, temperature = temperature)
        llm_with_tools = llm.bind_tools([
            create_process_tool,
            get_process_tool,
            update_process_status_tool,
            search_documents_tool,
        ])
        return llm, llm_with_tools

    def _build_messages(self, user_query: str, chat_history: List[BaseMessage]):
        """
        Gera a lista de mensagens para passar como contexto para o modelo. A lista é composta por:
        - SystemMessage: mensagem de sistema (prompt) para orientar o comportamento do modelo
        - BaseMessage: mensagens anteriores da conversa (chat_history)
        - HumanMessage: mensagem atual do usuário (user_query)
        """
        system = SystemMessage(content=self.sys_prompt)

        return [system] + chat_history + [HumanMessage(content=user_query)]
    
    def _process_tool_calls(self, tool_calls: List[ToolCall], new_messages: List[ConversationHistory], sources: List[dict], messages: List[BaseMessage]) -> List[str]:
        # Caso o modelo precise chamar uma ferramenta
        for tool_call in tool_calls:
            
            # Busca a função do tool_map (dicionário) pelo nome da ferramenta
            tool_func = self.tool_map.get(tool_call["name"])
            if tool_func:
                try:
                    # Caso achar a ferramenta, chama a função passando os parâmetros (args) necessários
                    tool_response = tool_func.invoke(tool_call["args"])
                except Exception as e:
                    tool_response = {"error": str(e)}

                tool_content = str(tool_response)

                # Se for a ferramenta de RAG, extrai o contexto e as fontes do JSON de retorno
                if tool_call["name"] == "search_documents_tool":
                    try:
                        parsed = json.loads(tool_content)
                        sources.extend(parsed.get("sources", []))
                        tool_content = parsed.get("context", tool_content)
                    except (json.JSONDecodeError, AttributeError):
                        pass

                # Adiciona o resultado da ferramenta como um ToolMessage para o modelo usar como contexto para responder a pergunta
                messages.append(ToolMessage(
                    content=tool_content,
                    tool_call_id=tool_call["id"]))
                
                # Mensagem de resultado da ferramenta
                new_messages.append(ConversationHistory(
                    role=MessageType.TOOL,
                    content=tool_content,
                    tool_call_id=tool_call["id"]))
    
    def _execute_llm_with_tools(
        self,
        messages: List[BaseMessage],
        new_messages: List[ConversationHistory],
        sources: List[dict],
    ):
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
        
        self._process_tool_calls(response.tool_calls, new_messages, sources, messages)
        
        return None, messages
    
    def _execute_streaming(self, messages: List[BaseMessage], new_messages: List[ConversationHistory]):
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

    def get_response_stream(
        self, user_query: str, chat_history: List[BaseMessage]
    ) -> Tuple[Generator, List[ConversationHistory], List[dict]]:
        """
        Retorna uma tupla (generator de chunks, new_messages, lista de fontes do RAG).
        """
        # A edição de new_messages e sources ocorre com referência de memória
        new_messages: List[ConversationHistory] = []
        sources: List[dict] = []
        messages = self._build_messages(user_query, chat_history)

        response, messages = self._execute_llm_with_tools(messages, new_messages, sources)
        
        if response:
            def generator():
                for char in response.content:
                    yield char
                                
            new_messages.append(ConversationHistory(
                role=MessageType.ASSISTANT,
                content=response.content))
            
            return generator(), new_messages, sources
        
        # Caso precise chamar uma ferramenta, gera a resposta final com o contexto atualizado
        return self._execute_streaming(messages, new_messages), new_messages, sources