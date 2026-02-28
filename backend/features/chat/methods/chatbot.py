from typing import List
from uuid import UUID
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from domains.conversation import Conversation
from domains.conversation_history import ConversationHistory
from domains.enums.message_type import MessageType
from infrastructure.services.chatbot_service import ChatbotService
from infrastructure.dtos.chat.message_history import MessageHistory
from infrastructure.dtos.chat.message_result import MessageResult
from data.database import get_db
from pydantic import BaseModel
from . import BaseHandler

# Request
class Command(BaseModel):
    input: str
    conversation_id: UUID | None = None

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
        
        if request.conversation_id and not conversation:
            raise HTTPException(status_code=404, detail="Conversa não encontrada.")
        
        if not conversation:
            conversation = Conversation()
            self.db.add(conversation)
            self.db.commit()
            self.db.refresh(conversation)
            
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
        
        response, new_messages = self.chatbotService.get_response(request.input, history)
        
        conversation.conversation_histories.append(ConversationHistory(role=MessageType.USER, content=request.input))
        conversation.conversation_histories.extend(new_messages)
        self.db.commit()

        return MessageResult(response=response, conversation_id=conversation.id)