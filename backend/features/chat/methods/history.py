from typing import List
from uuid import UUID
from fastapi import Depends
from sqlalchemy.orm import Session
from domains.conversation_history import ConversationHistory
from domains.enums.message_type import MessageType
from infrastructure.dtos.chat.message_history import MessageHistory, MessageHistoryItem
from data.database import get_db
from pydantic import BaseModel
from . import BaseHandler

# Request
class Query(BaseModel):
    conversation_id: UUID

# Handle
class ChatHistory(BaseHandler[Query, MessageHistory]):
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    def execute(self, request: Query):
        history = []
        conversation_history: List[ConversationHistory] = (
                                self.db.query(ConversationHistory)
                                .filter(ConversationHistory.conversation_id == request.conversation_id)
                                .order_by(ConversationHistory.created_at.asc())
                                .all())
        
        for ch in conversation_history:
            if ch.role == MessageType.ASSISTANT and ch.content:
                history.append(MessageHistoryItem(type=MessageType.ASSISTANT, message=ch.content))
            elif ch.role == MessageType.USER:
                history.append(MessageHistoryItem(type=MessageType.USER, message=ch.content))
                
        return MessageHistory(items=history)