from enum import Enum
from pydantic import BaseModel
from llama_index.core.llms import MessageRole


class PlanType(str, Enum):
    FREE = "free"
    PRO = "pro"


class ChatHistoryItem(BaseModel):
    role: MessageRole
    content: str
