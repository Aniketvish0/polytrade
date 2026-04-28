import json

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from jose import JWTError, jwt

from app.config import settings
from app.ws.manager import ws_manager

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...)):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")
        if not user_id:
            await websocket.close(code=4001)
            return
    except JWTError:
        await websocket.close(code=4001)
        return

    await ws_manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text(json.dumps({"type": "pong", "data": {}}))
            else:
                try:
                    msg = json.loads(data)
                    event_type = msg.get("type")

                    if event_type == "chat:message":
                        from app.db.engine import async_session
                        from app.nlp.parser import CommandParser
                        from app.db.models.user import User
                        from sqlalchemy import select

                        async with async_session() as db:
                            result = await db.execute(
                                select(User).where(User.id == user_id)
                            )
                            user = result.scalar_one_or_none()
                            if user:
                                parser = CommandParser(db=db, user=user)
                                chat_result = await parser.process(msg["data"]["content"])
                                from app.ws.events import agent_message_event
                                await ws_manager.send_to_user(
                                    user_id,
                                    agent_message_event(chat_result),
                                )
                                await db.commit()

                    elif event_type == "trade:approve":
                        pass  # TODO: wire to approval service

                    elif event_type == "trade:reject":
                        pass  # TODO: wire to approval service

                except json.JSONDecodeError:
                    pass

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, user_id)
