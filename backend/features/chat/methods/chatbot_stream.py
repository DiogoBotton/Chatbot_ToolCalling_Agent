from typing import List
from uuid import UUID
from fastapi import Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from domains.conversation import Conversation
from domains.conversation_history import ConversationHistory
from domains.enums.message_type import MessageType
from infrastructure.services.chatbot_service_stream import ChatbotService
from infrastructure.dtos.chat.message_result import MessageResult
from data.database import get_db
from pydantic import BaseModel
from . import BaseHandler

# Request
class Command(BaseModel):
    input: str
    conversation_id: UUID

# Handle
class Chatbot(BaseHandler[Command, MessageResult]):
    def __init__(self, db: Session = Depends(get_db), chatbotService: ChatbotService = Depends()):
        self.db = db
        self.chatbotService = chatbotService

    def execute(self, request: Command):
        conversation = (self.db
                        .query(Conversation)
                        .filter(Conversation.id == request.conversation_id)
                        .first()) if request.conversation_id else None
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversa não encontrada.")
            
        history = []
        conversation_history: List[ConversationHistory] = (
                                    self.db.query(ConversationHistory)
                                    .filter(ConversationHistory.conversation_id == conversation.id)
                                    .order_by(ConversationHistory.created_at.asc())
                                    .all()
                                ) if conversation.id else []
        
        for ch in conversation_history:
            if ch.role == MessageType.ASSISTANT:
                history.append(AIMessage(ch.content, tool_calls=ch.tool_calls or []))
            elif ch.role == MessageType.USER:
                history.append(HumanMessage(ch.content))
            elif ch.role == MessageType.TOOL:
                history.append(ToolMessage(ch.content, tool_call_id=ch.tool_call_id))
        
        generator, new_messages, sources = self.chatbotService.get_response_stream(request.input, history)
        
        def wrapped_generator():
            full_response = ""
            for chunk in generator:
                full_response += chunk
                yield chunk
            
            # Após todo o conteúdo, envia as fontes como marcador final para o frontend
            if sources:
                import json
                yield "\n\n__SOURCES__:" + json.dumps(sources, ensure_ascii=False)
            
            # Salva as novas mensagens no banco
            conversation.conversation_histories.append(ConversationHistory(role=MessageType.USER, content=request.input))
            conversation.conversation_histories.extend(new_messages)
            self.db.commit()

        return StreamingResponse(wrapped_generator(), media_type="text/plain")