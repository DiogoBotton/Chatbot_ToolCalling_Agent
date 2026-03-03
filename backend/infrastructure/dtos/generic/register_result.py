from uuid import UUID

from infrastructure.dtos.base import BaseResult
    
class RegisterResult(BaseResult):
    id: UUID
