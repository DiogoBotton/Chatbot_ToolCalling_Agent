from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from features.chat import chat_controller
from features.conversation import conversation_controller
from features.document import document_controller
from dotenv import load_dotenv
import os
load_dotenv()

os.environ['OPENAI_API_KEY'] = os.getenv("OPENAI_API_KEY")

app = FastAPI(
    title="Chatbot Tool CallingAPI",
    docs_url="/docs",  # URL para disponibilização do Swagger UI
)

# Libera o CORS da API para requisições via http
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']
)

app.include_router(chat_controller.router)
app.include_router(conversation_controller.router)
app.include_router(document_controller.router)