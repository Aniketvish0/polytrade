from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import get_db
from app.db.models.user import User
from app.dependencies import get_current_user
from app.schemas.chat import ChatMessage, ChatResponse

router = APIRouter()


@router.post("/message", response_model=ChatResponse)
async def send_message(
    body: ChatMessage,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.nlp.parser import CommandParser

    parser = CommandParser(db=db, user=user)
    result = await parser.process(body.content)
    return ChatResponse(type=result["type"], content=result["content"], message_type=result.get("message_type", "text"))
