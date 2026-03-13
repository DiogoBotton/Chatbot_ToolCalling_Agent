from datetime import datetime
from uuid import UUID

from infrastructure.dtos.base import BaseResult


class DocumentResult(BaseResult):
    id: UUID
    name: str
    file_type: str
    created_at: datetime
