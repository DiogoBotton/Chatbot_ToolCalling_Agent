from sqlalchemy import Column, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

from data.database import Base
from .abstractions.domain_base import DomainBase

EMBEDDING_DIMENSIONS = 1536


class DocumentChunk(DomainBase, Base):
    __tablename__ = 'document_chunks'

    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    page_number = Column(Integer, nullable=True)
    embedding = Column(Vector(EMBEDDING_DIMENSIONS), nullable=True)

    document_id = Column(UUID(as_uuid=True), ForeignKey('documents.id'), nullable=False)
    document = relationship("Document", back_populates="chunks")

    def __init__(self, content: str, chunk_index: int, document_id, page_number: int = None):
        self.content = content
        self.chunk_index = chunk_index
        self.document_id = document_id
        self.page_number = page_number
