from sqlalchemy import UUID, Column, ForeignKey, String, Enum
from sqlalchemy.orm import relationship
from domains.enums.process_status import ProcessStatus
from data.database import Base
from .abstractions.domain_base import DomainBase

class Process(DomainBase, Base):
    __tablename__ = 'processes'

    number = Column(String, nullable=False)
    status = Column(Enum(ProcessStatus), nullable=False)
    
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    
    user = relationship("User", back_populates="processes")

    def __init__(self, number: str, user_id: UUID):
        self.number = number
        self.user_id = user_id
        self.status = ProcessStatus.RECEBIDO