import json
import logging

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from jose import JWTError, jwt
from sqlalchemy import select

from app.config import settings
from app.ws.manager import ws_manager

logger = logging.getLogger(__name__)

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
                        await _handle_chat_message(msg, user_id, websocket)

                    elif event_type in ("trade:approve", "trade:reject"):
                        await _handle_trade_action(msg, event_type, user_id)

                except json.JSONDecodeError:
                    pass

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, user_id)


async def _handle_chat_message(msg: dict, user_id: str, websocket: WebSocket):
    from app.db.engine import async_session
    from app.db.models.user import User
    from app.ws.events import agent_message_event, WSEvent

    try:
        async with async_session() as db:
            result = await db.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            if not user:
                return

            history = msg.get("data", {}).get("history", [])
            content = msg.get("data", {}).get("content", "")

            if not user.onboarding_completed:
                from app.nlp.onboarding import OnboardingEngine
                engine = OnboardingEngine(db=db, user=user)
                chat_result = await engine.process_step(content)
            else:
                from app.nlp.parser import CommandParser
                parser = CommandParser(db=db, user=user)
                chat_result = await parser.process(content, conversation_history=history)

            await ws_manager.send_to_user(
                user_id,
                agent_message_event(chat_result),
            )

            action = chat_result.get("action", {})
            if isinstance(action, dict):
                await _execute_action(action, user, db, websocket)

            await db.commit()

    except Exception as e:
        logger.exception("chat:message handler error")
        try:
            await ws_manager.send_to_user(
                user_id,
                WSEvent(type="error", data={"message": f"Failed to process message: {e}"}),
            )
        except Exception:
            pass


async def _execute_action(action: dict, user, db, websocket):
    """Execute actions returned by the conversation/onboarding engine."""
    from app.ws.events import WSEvent

    action_type = action.get("type")
    action_data = action.get("data", {})
    user_id = str(user.id)

    if action_type == "create_strategy":
        from app.db.models.strategy import Strategy
        strategy = Strategy(
            user_id=user.id,
            name=action_data.get("name", "My Strategy"),
            is_active=True,
            rules=action_data.get("rules", {}),
            context=action_data.get("context", ""),
            priority=action_data.get("priority", 0),
        )
        db.add(strategy)
        await db.flush()

    elif action_type == "create_policy":
        from app.db.models.policy import Policy
        from sqlalchemy import update
        await db.execute(
            update(Policy).where(Policy.user_id == user.id).values(is_active=False)
        )
        policy = Policy(
            user_id=user.id,
            name=action_data.get("name", "My Policy"),
            is_active=True,
            global_rules=action_data.get("global_rules", {}),
            category_rules=action_data.get("category_rules", {}),
            confidence_rules=action_data.get("confidence_rules", {}),
            risk_rules=action_data.get("risk_rules", {}),
        )
        db.add(policy)
        await db.flush()

    elif action_type == "start_agent":
        try:
            from app.agent.loop import AgentLoop
            from app.db.engine import async_session
            app = websocket.app
            user_key = user_id
            if user_key not in app.state.agent_loops or app.state.agent_loops[user_key].state_manager.is_stopped():
                loop = AgentLoop(
                    user_id=user.id,
                    user_email=user.email,
                    db_session_factory=async_session,
                    ws_manager=ws_manager,
                )
                app.state.agent_loops[user_key] = loop
                await loop.start()
        except Exception as e:
            logger.warning(f"Failed to start agent: {e}")

    elif action_type == "complete_onboarding":
        from app.db.models.policy import Policy
        from app.db.models.strategy import Strategy
        from sqlalchemy import update

        onboarding_data = action_data

        strat_data = onboarding_data.get("strategy", {})
        strategy = Strategy(
            user_id=user.id,
            name=strat_data.get("name", "My Strategy"),
            is_active=True,
            rules=strat_data.get("rules", {}),
            context=strat_data.get("context", ""),
            priority=0,
        )
        db.add(strategy)

        await db.execute(
            update(Policy).where(Policy.user_id == user.id).values(is_active=False)
        )
        pol_data = onboarding_data.get("policy", {})
        policy = Policy(
            user_id=user.id,
            name=pol_data.get("name", "Default Policy"),
            is_active=True,
            global_rules=pol_data.get("global_rules", {}),
            category_rules=pol_data.get("category_rules", {}),
            confidence_rules=pol_data.get("confidence_rules", {}),
            risk_rules=pol_data.get("risk_rules", {}),
        )
        db.add(policy)

        user.onboarding_completed = True
        user.onboarding_step = 4
        await db.flush()

        await ws_manager.send_to_user(
            user_id,
            WSEvent(type="onboarding:complete", data={"completed": True}),
        )

        try:
            from app.agent.loop import AgentLoop
            from app.db.engine import async_session as _sess
            app = websocket.app
            user_key = user_id
            if user_key not in app.state.agent_loops or app.state.agent_loops[user_key].state_manager.is_stopped():
                loop = AgentLoop(
                    user_id=user.id,
                    user_email=user.email,
                    db_session_factory=_sess,
                    ws_manager=ws_manager,
                )
                app.state.agent_loops[user_key] = loop
                await loop.start()
        except Exception as e:
            logger.warning(f"Failed to auto-start agent after onboarding: {e}")


async def _handle_trade_action(msg: dict, event_type: str, user_id: str):
    import uuid as _uuid
    from datetime import datetime as _dt, timezone as _tz
    from app.db.engine import async_session as _async_session
    from app.db.models.approval import Approval
    from app.ws.events import WSEvent

    try:
        approval_id = msg["data"].get("approval_id")
        if not approval_id:
            return

        async with _async_session() as approval_db:
            result = await approval_db.execute(
                select(Approval).where(
                    Approval.id == _uuid.UUID(approval_id),
                    Approval.user_id == _uuid.UUID(user_id),
                )
            )
            approval = result.scalar_one_or_none()
            if not approval or approval.status != "pending":
                return

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

            await ws_manager.send_to_user(
                user_id,
                WSEvent(
                    type=f"approval:{new_status}",
                    data={"approval_id": approval_id, "status": new_status},
                ),
            )

    except Exception as e:
        logger.exception("trade action handler error")
        try:
            await ws_manager.send_to_user(
                user_id,
                WSEvent(type="error", data={"message": f"Failed to process trade action: {e}"}),
            )
        except Exception:
            pass
