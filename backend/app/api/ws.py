import json

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from jose import JWTError, jwt
from sqlalchemy import select

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

                    elif event_type in ("trade:approve", "trade:reject"):
                        import uuid as _uuid
                        from datetime import datetime as _dt, timezone as _tz
                        from app.db.engine import async_session as _async_session
                        from app.db.models.approval import Approval

                        approval_id = msg["data"].get("approval_id")
                        if approval_id:
                            async with _async_session() as approval_db:
                                result = await approval_db.execute(
                                    select(Approval).where(
                                        Approval.id == _uuid.UUID(approval_id),
                                        Approval.user_id == _uuid.UUID(user_id),
                                    )
                                )
                                approval = result.scalar_one_or_none()
                                if approval and approval.status == "pending":
                                    new_status = "approved" if event_type == "trade:approve" else "rejected"
                                    approval.status = new_status
                                    approval.resolved_by = _uuid.UUID(user_id)
                                    approval.resolved_at = _dt.now(_tz.utc)
                                    approval.resolution_note = msg["data"].get("note")

                                    if new_status == "approved":
                                        from app.db.models.market_cache import MarketCache
                                        from app.trading.engine import SimulatedTradingEngine
                                        from app.ws.events import trade_executed_event, portfolio_update_event

                                        mkt = await approval_db.execute(
                                            select(MarketCache).where(
                                                MarketCache.condition_id == approval.market_id
                                            )
                                        )
                                        market = mkt.scalar_one_or_none()
                                        if market:
                                            engine = SimulatedTradingEngine(approval_db)
                                            trade = await engine.execute_buy(
                                                user_id=_uuid.UUID(user_id),
                                                market=market,
                                                side=approval.side,
                                                shares=approval.shares,
                                                price=approval.price,
                                                decision={
                                                    "confidence": float(approval.confidence_score or 0),
                                                    "reasoning": approval.reasoning,
                                                    "sources_count": len(approval.sources or []),
                                                },
                                                enforcement_result="approved",
                                                policy_id=approval.policy_id,
                                            )
                                            await approval_db.flush()
                                            await ws_manager.send_to_user(user_id, trade_executed_event(trade))
                                            portfolio = await engine._get_portfolio(_uuid.UUID(user_id))
                                            await ws_manager.send_to_user(user_id, portfolio_update_event(portfolio))

                                    await approval_db.commit()

                                    from app.ws.events import WSEvent
                                    await ws_manager.send_to_user(
                                        user_id,
                                        WSEvent(
                                            type=f"approval:{new_status}",
                                            data={"approval_id": approval_id, "status": new_status},
                                        ),
                                    )

                except json.JSONDecodeError:
                    pass

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, user_id)
