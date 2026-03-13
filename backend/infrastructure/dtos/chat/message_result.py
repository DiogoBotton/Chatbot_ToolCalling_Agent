from typing import Any, Dict, List

from infrastructure.dtos.base import BaseResult


class MessageResult(BaseResult):
    response: str
    sources: List[Dict[str, Any]] = []