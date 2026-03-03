from uuid import UUID

from fastapi import Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from data.database import get_db
from domains.conversation import Conversation
from domains.user import User
from infrastructure.dtos.generic.register_result import RegisterResult
from . import BaseHandler

class Command(BaseModel):
    user_id: UUID | None = None

class CreateConversation(BaseHandler[Command, RegisterResult]):
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    def execute(self, request: Command) -> RegisterResult:
        if request.user_id is not None:
            user_exists = (
                self.db.query(User.id)
                .filter(User.id == request.user_id)
                .first()
            )
            if not user_exists:
                raise HTTPException(status_code=404, detail="Usuário não encontrado.")

        conversation = Conversation(user_id=request.user_id)
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)

        return conversation
