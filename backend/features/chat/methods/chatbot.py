from typing import List
from fastapi import Depends
from sqlalchemy.orm import Session
from langchain_core.messages import HumanMessage, AIMessage
from domains.enums.message_type import MessageType
from services.chatbot_service import ChatbotService
from infrastructure.dtos.chat.message_history import MessageHistory
from infrastructure.dtos.chat.message_result import MessageResult
from data.database import get_db
from pydantic import BaseModel
from . import BaseHandler

# Request
class Command(BaseModel):
    input: str
    chat_history: List[MessageHistory]
    #session_id: UUID | None = None

# Handle
class Chatbot(BaseHandler[Command, MessageResult]):
    def __init__(self, db: Session = Depends(get_db), chatbotService: ChatbotService = Depends()):
        self.db = db
        self.chatbotService = chatbotService

    def execute(self, request: Command):
        # TODO: Refatorar este histórico para ser salvo no banco de dados e não enviado pelo cliente
        history = []
        for h in request.chat_history:
            if h.type == MessageType.AI:
                history.append(AIMessage(h.message))
            else:
                history.append(HumanMessage(h.message))
        
        response = self.chatbotService.get_response(request.input, history)

        return MessageResult(response=response)