from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.inspection import inspect as sa_inspect


def _to_dict(obj: Any) -> Any:
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, dict):
        return obj
    try:
        mapper = sa_inspect(type(obj))
        return {c.key: getattr(obj, c.key) for c in mapper.column_attrs}
    except Exception:
        return obj


@dataclass
class WSEvent:
    type: str
    data: dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {"type": self.type, "data": self.data, "timestamp": self.timestamp}


def agent_status_event(status: str, current_task: str | None = None) -> WSEvent:
    return WSEvent(type="agent:status", data={"status": status, "currentTask": current_task})


def agent_message_event(message: Any) -> WSEvent:
    return WSEvent(type="agent:message", data={"message": _to_dict(message)})


def trade_executed_event(trade: Any) -> WSEvent:
    return WSEvent(type="trade:executed", data={"trade": _to_dict(trade)})


def trade_held_event(trade: Any, approval: Any) -> WSEvent:
    return WSEvent(type="trade:held", data={"trade": _to_dict(trade), "approval": _to_dict(approval)})


def trade_denied_event(trade: Any, reason: str) -> WSEvent:
    return WSEvent(type="trade:denied", data={"trade": _to_dict(trade), "reason": reason})


def portfolio_update_event(portfolio: Any) -> WSEvent:
    return WSEvent(type="portfolio:update", data={"portfolio": _to_dict(portfolio)})


def news_item_event(item: Any) -> WSEvent:
    return WSEvent(type="news:item", data={"item": _to_dict(item)})


def policy_updated_event(policy: Any) -> WSEvent:
    return WSEvent(type="policy:updated", data={"policy": _to_dict(policy)})


def strategy_updated_event(strategy: Any) -> WSEvent:
    return WSEvent(type="strategy:updated", data={"strategy": _to_dict(strategy)})


def agent_activity_event(phase: str, message: str, detail: dict[str, Any] | None = None) -> WSEvent:
    return WSEvent(
        type="agent:activity",
        data={"phase": phase, "message": message, **(detail or {})},
    )
