from infrastructure.dtos.base import BaseResult
from domains.enums.message_type import MessageType

class MessageHistory(BaseResult):
    type: MessageType
    message: str