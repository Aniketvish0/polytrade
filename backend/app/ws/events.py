from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class WSEvent:
    type: str
    data: dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {"type": self.type, "data": self.data, "timestamp": self.timestamp}


def agent_status_event(status: str, current_task: str | None = None) -> WSEvent:
    return WSEvent(type="agent:status", data={"status": status, "currentTask": current_task})


def agent_message_event(message: dict) -> WSEvent:
    return WSEvent(type="agent:message", data={"message": message})


def trade_executed_event(trade: dict) -> WSEvent:
    return WSEvent(type="trade:executed", data={"trade": trade})


def trade_held_event(trade: dict, approval: dict) -> WSEvent:
    return WSEvent(type="trade:held", data={"trade": trade, "approval": approval})


def trade_denied_event(trade: dict, reason: str) -> WSEvent:
    return WSEvent(type="trade:denied", data={"trade": trade, "reason": reason})


def portfolio_update_event(portfolio: dict) -> WSEvent:
    return WSEvent(type="portfolio:update", data={"portfolio": portfolio})


def news_item_event(item: dict) -> WSEvent:
    return WSEvent(type="news:item", data={"item": item})


def policy_updated_event(policy: dict) -> WSEvent:
    return WSEvent(type="policy:updated", data={"policy": policy})


def strategy_updated_event(strategy: dict) -> WSEvent:
    return WSEvent(type="strategy:updated", data={"strategy": strategy})
