from infrastructure.dtos.base import BaseResult
# from uuid import UUID

class MessageResult(BaseResult):
    response: str
    #session_id: UUID | None = None