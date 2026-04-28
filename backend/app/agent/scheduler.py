from datetime import datetime, timezone


class CooldownScheduler:
    def __init__(self, cooldown_minutes: int = 5, max_daily_trades: int = 25):
        self._last_trade: dict[str, datetime] = {}
        self._daily_count: int = 0
        self._daily_reset: datetime = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        self.cooldown_minutes = cooldown_minutes
        self.max_daily_trades = max_daily_trades

    def can_trade(self, market_id: str) -> bool:
        now = datetime.now(timezone.utc)

        if now.date() > self._daily_reset.date():
            self._daily_count = 0
            self._daily_reset = now.replace(hour=0, minute=0, second=0, microsecond=0)

        if self._daily_count >= self.max_daily_trades:
            return False

        last = self._last_trade.get(market_id)
        if last:
            elapsed = (now - last).total_seconds() / 60
            if elapsed < self.cooldown_minutes:
                return False

        return True

    def record_trade(self, market_id: str):
        self._last_trade[market_id] = datetime.now(timezone.utc)
        self._daily_count += 1
