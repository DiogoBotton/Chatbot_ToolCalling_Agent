# Chatbot_ToolCalling_Agent

### TODOs

- [x] Ainda não está ignorando .env locais mesmo com .dockerignore.
- [x] Criar histórico de mensagens no banco de dados e passar como session_id/conversation_id para manter o contexto da conversa, ao invés de sempre o front precisar enviar o histórico.
- [ ] Criar alguma função para abstrair a criação de ConversationHistory que está dentro da função get_response (pesquisar alguma forma para não necessitar da função get_response retornar a lista de novas mensagens, ser passada por outro lugar).
- [ ] Criar atributo incremental (que incrementa apenas no banco de dados) para definir ordenação das mensagens, ao invés de utilizar apenas o created_at (pois pode ter valores iguais).
- [ ] Melhorar processo de criação das tools e chamamentos de banco de dados.
- [ ] Retornar a resposta do chatbot em **streaming** para o front.
- [ ] Criar compatibilidade para rodar as LLMs localmente com **Ollama**.
- [ ] Estudar possibilidade do prompt do sistema estar em um arquivo separado e ser carregado na inicialização do chatbot (um markdown .md, por exemplo).
- [ ] Criar um README mais detalhado explicando o projeto, como rodar, etc.

#### Vídeo de apoio:

[Como Implementar Tool/Function Calling com LangChain (Atualizado 2025)](https://www.youtube.com/watch?v=6E-0aLxMRl4)
