# Chatbot_ToolCalling_Agent

TODOs:

- ~~Ainda não está ignorando .env locais mesmo com .dockerignore.~~
- Melhorar processo de criação das tools e chamamentos de banco de dados.
- Criar histórico de mensagens no banco de dados e passar como session_id/conversation_id para manter o contexto da conversa, ao invés de sempre o front precisar enviar o histórico.
- Retornar a resposta do chatbot em streaming para o front.
- Criar compatibilidade para rodar as LLMs localmente com Ollama.
- Estudar possibilidade do prompt do sistema estar em um arquivo separado e ser carregado na inicialização do chatbot (um markdown .md, por exemplo).
- Criar um README mais detalhado explicando o projeto, como rodar, etc.

- Ajustar erros nas migrations
- Ajustar frontend (talvez verificar possibilidade de já deixar como streaming)

#### Vídeo de apoio:

[Como Implementar Tool/Function Calling com LangChain (Atualizado 2025)](https://www.youtube.com/watch?v=6E-0aLxMRl4)
