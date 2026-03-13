from uuid import UUID

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from data.database import get_db
from domains.document import Document
from features.base_handler import BaseHandler
from pydantic import BaseModel


class Command(BaseModel):
    document_id: UUID


class DeleteDocument(BaseHandler[Command, None]):
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    def execute(self, request: Command) -> None:
        document: Document | None = (
            self.db.query(Document)
            .filter(Document.id == request.document_id)
            .first()
        )

        if not document:
            raise HTTPException(status_code=404, detail="Documento não encontrado.")

        # As chunks são deletadas em cascata (cascade="all, delete-orphan" no domain)
        self.db.delete(document)
        self.db.commit()
