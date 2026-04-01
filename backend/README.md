## Backend

#### Criar migrations com alembic

```bash
    alembic revision --autogenerate -m "Mensagem da migration"
```

#### Aplicar migrations

```bash
    alembic upgrade head
```

### Documentação do LangChain sobre ChatOpenAI

Muito útil, tem exemplos de como adquirir uso de tokens, até mesmo de exemplos de como enviar imagens para a LLM analisar.

[LangChain Reference](https://reference.langchain.com/python/langchain-openai/chat_models/base/ChatOpenAI)