from pydantic import BaseModel


class ChatMessage(BaseModel):
    content: str


class ChatResponse(BaseModel):
    type: str
    content: str | dict
    message_type: str = "text"
