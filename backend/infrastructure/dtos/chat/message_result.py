from infrastructure.dtos.base import BaseResult
from uuid import UUID

class MessageResult(BaseResult):
    response: str
    conversation_id: UUID