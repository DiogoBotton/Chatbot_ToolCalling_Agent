from pydantic import BaseModel

from infrastructure.dtos.base import BaseResult


class DocumentUploadResult(BaseResult):
    id: str
    name: str
    file_type: str
    total_chunks: int
