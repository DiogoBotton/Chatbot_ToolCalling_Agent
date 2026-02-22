from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from data.database import Base
from .abstractions.domain_base import DomainBase

class User(DomainBase, Base):
    __tablename__ = 'users'

    email = Column(String, nullable=False)
    
    processes = relationship("Process", back_populates="user")

    def __init__(self, email: str):
        self.email = email