from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from data.database import Base
from .abstractions.domain_base import DomainBase


class Document(DomainBase, Base):
    __tablename__ = 'documents'

    name = Column(String, nullable=False)
    file_type = Column(String, nullable=False)  # pdf, txt, md

    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")

    def __init__(self, name: str, file_type: str):
        self.name = name
        self.file_type = file_type
