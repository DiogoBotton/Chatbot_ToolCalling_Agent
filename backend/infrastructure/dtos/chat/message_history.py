from typing import List
from infrastructure.dtos.base import BaseResult
from domains.enums.message_type import MessageType
    
class MessageHistoryItem(BaseResult):
    type: MessageType
    message: str
    
class MessageHistory(BaseResult):
    items: List[MessageHistoryItem]