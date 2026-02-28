from enum import Enum

class MessageType(Enum):
    ASSISTANT = "assistant"
    USER = "user"
    TOOL = "tool"
    SYSTEM = "system"