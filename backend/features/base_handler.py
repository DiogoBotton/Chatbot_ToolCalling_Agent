from fastapi import Depends
from sqlalchemy.orm import Session
from data.database import get_db
from abc import ABC, abstractmethod
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Generic, TypeVar

# Tipos genéricos para Request e Response
TRequest = TypeVar("TRequest", bound=BaseModel)
TResponse = TypeVar("TResponse")

class BaseHandler(ABC, Generic[TRequest, TResponse]):
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    @abstractmethod
    def execute(self, request: TRequest):
        """Método principal que deve ser implementado pelas subclasses"""
        raise NotImplementedError("Handler não implementada.")