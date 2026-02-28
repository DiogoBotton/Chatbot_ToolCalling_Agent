from typing import List

from sqlalchemy import UUID, Column, ForeignKey
from sqlalchemy.orm import Mapped, relationship
from domains.conversation_history import ConversationHistory
from data.database import Base
from .abstractions.domain_base import DomainBase

class Conversation(DomainBase, Base):
    __tablename__ = 'conversations'
    
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True) # Por enquanto, pode ser nulo, mas futuramente pode ser obrigatório quando tiver a funcionalidade de associar conversa a um usuário específico
    user = relationship("User", back_populates="conversations")
    
    conversation_histories: Mapped[List["ConversationHistory"]] = relationship("ConversationHistory", back_populates="conversation")

    def __init__(self, user_id: UUID = None):
        self.user_id = user_id