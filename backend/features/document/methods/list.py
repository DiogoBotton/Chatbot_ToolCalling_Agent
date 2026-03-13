from typing import List

from fastapi import Depends
from sqlalchemy.orm import Session

from data.database import get_db
from domains.document import Document
from features.base_handler import BaseHandler
from infrastructure.dtos.document.document_result import DocumentResult
from pydantic import BaseModel


class Query(BaseModel):
    pass


class ListDocuments(BaseHandler[Query, List[DocumentResult]]):
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    def execute(self, request: Query = None) -> List[DocumentResult]:
        documents: List[Document] = (
            self.db.query(Document)
            .order_by(Document.created_at.desc())
            .all()
        )
        return [DocumentResult.model_validate(doc) for doc in documents]
