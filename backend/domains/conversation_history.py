from sqlalchemy import UUID, Column, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from domains.enums.message_type import MessageType
from data.database import Base
from .abstractions.domain_base import DomainBase

class ConversationHistory(DomainBase, Base):
    __tablename__ = 'conversation_histories'
    
    content = Column(String, nullable=False) # Armazena o conteúdo da mensagem, seja do usuário, assistente ou resposta da ferramenta
    role = Column(Enum(MessageType), nullable=False)
    
    tool_calls = Column(JSONB, nullable=True) # Armazena as chamadas de ferramentas
    tool_call_id = Column(String, nullable=True) # Quando a mensagem for do tipo TOOL, armazena o ID da chamada da ferramenta correspondente e salva a resposta em content
    
    conversation_id = Column(UUID(as_uuid=True), ForeignKey('conversations.id'), nullable=False)
    conversation = relationship("Conversation", back_populates="conversation_histories")

    def __init__(self, role: MessageType, content: str = "", tool_calls: list = None, tool_call_id: str = None):
        self.role = role
        self.content = content
        self.tool_calls = tool_calls
        self.tool_call_id = tool_call_id