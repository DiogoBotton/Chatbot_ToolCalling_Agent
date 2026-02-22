from sqlalchemy import Column, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4
from sqlalchemy.ext.declarative import declared_attr # Transforma uma função em um atributo da classe

class DomainBase:
    @declared_attr
    def id(cls): # cls: classe que herdou a classe pai (DomainBase)
        return Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    @declared_attr
    def created_at(cls):
        return Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    @declared_attr
    def updated_at(cls):
        return Column(DateTime(timezone=True), onupdate=func.now())