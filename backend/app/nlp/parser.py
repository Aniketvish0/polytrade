import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User

logger = logging.getLogger(__name__)


class CommandParser:
    def __init__(self, db: AsyncSession, user: User):
        self.db = db
        self.user = user

    async def process(self, text: str, conversation_history: list[dict] | None = None) -> dict:
        text = text.strip()
        if not text:
            return {"type": "info", "content": "Empty message.", "message_type": "text"}

        from app.nlp.conversation import ConversationEngine
        engine = ConversationEngine(db=self.db, user=self.user)
        return await engine.respond(text, conversation_history=conversation_history)
