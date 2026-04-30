import logging
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

RESEARCH_COOLDOWN_SECONDS = 60
ANALYSIS_COOLDOWN_SECONDS = 300
PRICE_MOVEMENT_THRESHOLD = 0.10
TRADE_COOLDOWN_SECONDS = 600
DENIED_COOLDOWN_SECONDS = 300
MAX_CACHE_AGE_SECONDS = 3600


class ResearchCacheEntry:
    __slots__ = (
        "market_id",
        "last_researched_at",
        "last_analyzed_at",
        "analysis_result",
        "research_result",
        "last_price_at_analysis",
        "last_price_at_research",
        "cooldown_until",
        "scan_count",
        "last_scanned_at",
        "last_traded_at",
    )

    def __init__(self, market_id: str):
        self.market_id = market_id
        self.last_researched_at: datetime | None = None
        self.last_analyzed_at: datetime | None = None
        self.analysis_result: dict | None = None
        self.research_result: dict | None = None
        self.last_price_at_analysis: float | None = None
        self.last_price_at_research: float | None = None
        self.cooldown_until: datetime | None = None
        self.scan_count: int = 0
        self.last_scanned_at: datetime | None = None
        self.last_traded_at: datetime | None = None


def _price_moved(old_price: float | None, new_price: float) -> bool:
    if old_price is None or old_price == 0:
        return True
    return abs(new_price - old_price) / old_price >= PRICE_MOVEMENT_THRESHOLD


class ResearchCache:
    def __init__(self):
        self._entries: dict[str, ResearchCacheEntry] = {}

    def __len__(self):
        return len(self._entries)

    def get(self, market_id: str) -> ResearchCacheEntry | None:
        return self._entries.get(market_id)

    def should_research(self, market_id: str, current_price: float, now: datetime | None = None) -> bool:
        now = now or datetime.now(timezone.utc)
        entry = self._entries.get(market_id)
        if not entry:
            return True
        if entry.cooldown_until and now < entry.cooldown_until:
            return False
        if not entry.last_researched_at:
            return True
        elapsed = (now - entry.last_researched_at).total_seconds()
        if elapsed < RESEARCH_COOLDOWN_SECONDS and not _price_moved(entry.last_price_at_research, current_price):
            return False
        return True

    def should_analyze(self, market_id: str, current_price: float, now: datetime | None = None) -> bool:
        now = now or datetime.now(timezone.utc)
        entry = self._entries.get(market_id)
        if not entry:
            return True
        if not entry.last_analyzed_at:
            return True
        elapsed = (now - entry.last_analyzed_at).total_seconds()
        if elapsed < ANALYSIS_COOLDOWN_SECONDS and not _price_moved(entry.last_price_at_analysis, current_price):
            return False
        return True

    def is_on_trade_cooldown(self, market_id: str, now: datetime | None = None) -> bool:
        now = now or datetime.now(timezone.utc)
        entry = self._entries.get(market_id)
        if not entry or not entry.last_traded_at:
            return False
        return (now - entry.last_traded_at).total_seconds() < TRADE_COOLDOWN_SECONDS

    def record_research(self, market_id: str, research_result: dict, current_price: float):
        entry = self._ensure_entry(market_id)
        entry.last_researched_at = datetime.now(timezone.utc)
        entry.research_result = research_result
        entry.last_price_at_research = current_price

    def record_analysis(self, market_id: str, analysis_result: dict, current_price: float):
        entry = self._ensure_entry(market_id)
        entry.last_analyzed_at = datetime.now(timezone.utc)
        entry.analysis_result = analysis_result
        entry.last_price_at_analysis = current_price

    def record_scan(self, market_id: str):
        entry = self._ensure_entry(market_id)
        entry.scan_count += 1
        entry.last_scanned_at = datetime.now(timezone.utc)

    def record_trade(self, market_id: str):
        now = datetime.now(timezone.utc)
        entry = self._ensure_entry(market_id)
        entry.last_traded_at = now
        entry.cooldown_until = now + timedelta(seconds=TRADE_COOLDOWN_SECONDS)

    def record_denied(self, market_id: str):
        now = datetime.now(timezone.utc)
        entry = self._ensure_entry(market_id)
        entry.last_traded_at = now
        entry.cooldown_until = now + timedelta(seconds=DENIED_COOLDOWN_SECONDS)
        entry.analysis_result = {"action": "pass", "reason": "denied_by_policy"}

    def get_freshness_score(self, market_id: str, now: datetime | None = None) -> float:
        now = now or datetime.now(timezone.utc)
        entry = self._entries.get(market_id)
        if not entry or entry.scan_count == 0:
            return 1.0
        scan_decay = max(0.0, 1.0 - (entry.scan_count / 20))
        if entry.last_scanned_at:
            seconds_since = (now - entry.last_scanned_at).total_seconds()
            recency = min(1.0, seconds_since / 300)
        else:
            recency = 1.0
        return scan_decay * recency

    def cleanup(self, max_age_seconds: int = MAX_CACHE_AGE_SECONDS):
        now = datetime.now(timezone.utc)
        stale = [
            mid for mid, entry in self._entries.items()
            if entry.last_scanned_at and (now - entry.last_scanned_at).total_seconds() > max_age_seconds
        ]
        for mid in stale:
            del self._entries[mid]
        if stale:
            logger.debug(f"Research cache cleanup: evicted {len(stale)} stale entries")

    def _ensure_entry(self, market_id: str) -> ResearchCacheEntry:
        if market_id not in self._entries:
            self._entries[market_id] = ResearchCacheEntry(market_id)
        return self._entries[market_id]


_caches: dict[str, ResearchCache] = {}


def get_cache(user_id: str) -> ResearchCache:
    if user_id not in _caches:
        _caches[user_id] = ResearchCache()
    return _caches[user_id]
