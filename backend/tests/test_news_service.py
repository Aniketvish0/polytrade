"""Tests for news caching (app/services/news_service.py)."""

import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import app.services.news_service as news_mod
from app.services.news_service import NewsService, _cache_get, _cache_set


# ---------------------------------------------------------------------------
# Fixture — reset cache between tests
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _reset_cache():
    """Clear the module-level cache before each test."""
    news_mod._NEWS_CACHE.clear()
    yield
    news_mod._NEWS_CACHE.clear()


# ---------------------------------------------------------------------------
# _cache_set stores and _cache_get retrieves
# ---------------------------------------------------------------------------


async def test_cache_set_stores_and_cache_get_retrieves():
    items = [{"source": "Reuters", "title": "Test"}]
    _cache_set("market:politics", items)

    result = _cache_get("market:politics")
    assert result is not None
    assert result == items


# ---------------------------------------------------------------------------
# _cache_get returns None for missing key
# ---------------------------------------------------------------------------


async def test_cache_get_returns_none_for_missing_key():
    result = _cache_get("nonexistent_key")
    assert result is None


# ---------------------------------------------------------------------------
# _cache_get returns None for expired entry
# ---------------------------------------------------------------------------


async def test_cache_get_returns_none_for_expired_entry(monkeypatch):
    items = [{"source": "AP", "title": "Old news"}]
    _cache_set("expired:key", items)

    # Fast-forward time past TTL (300 seconds)
    original_ts = news_mod._NEWS_CACHE["expired:key"][0]
    news_mod._NEWS_CACHE["expired:key"] = (original_ts - 400, items)

    result = _cache_get("expired:key")
    assert result is None

    # The expired entry should have been removed
    assert "expired:key" not in news_mod._NEWS_CACHE


# ---------------------------------------------------------------------------
# _cache_set evicts oldest when > 100 entries
# ---------------------------------------------------------------------------


async def test_cache_set_evicts_oldest_when_over_100():
    # Fill cache with 100 entries
    for i in range(100):
        _cache_set(f"key_{i}", [{"index": i}])

    assert len(news_mod._NEWS_CACHE) == 100
    assert "key_0" in news_mod._NEWS_CACHE

    # Adding one more should evict the oldest
    _cache_set("key_100", [{"index": 100}])

    assert len(news_mod._NEWS_CACHE) == 100
    assert "key_0" not in news_mod._NEWS_CACHE  # oldest evicted
    assert "key_100" in news_mod._NEWS_CACHE


# ---------------------------------------------------------------------------
# search() — returns cached results on cache hit
# ---------------------------------------------------------------------------


async def test_search_returns_cached_results_no_api_calls(mock_db):
    cached_items = [{"source": "Tavily", "title": "Cached article", "url": "http://ex.com"}]
    _cache_set("market123:politics", cached_items)

    service = NewsService(db=mock_db)

    with patch.object(service, "_search_tavily", new_callable=AsyncMock) as mock_tavily, \
         patch.object(service, "_search_newsapi", new_callable=AsyncMock) as mock_newsapi:

        result = await service.search(query="test", category="politics", market_id="market123")

    assert result == cached_items
    mock_tavily.assert_not_awaited()
    mock_newsapi.assert_not_awaited()


# ---------------------------------------------------------------------------
# search() — populates cache on miss
# ---------------------------------------------------------------------------


async def test_search_populates_cache_on_miss(mock_db):
    tavily_items = [{"source": "tavily", "title": "Tavily result", "url": "http://t.com", "summary": "Test"}]
    newsapi_items = [{"source": "newsapi", "title": "NewsAPI result", "url": "http://n.com", "summary": "Test"}]

    service = NewsService(db=mock_db)

    with patch.object(service, "_search_tavily", new_callable=AsyncMock, return_value=tavily_items) as mock_tavily, \
         patch.object(service, "_search_newsapi", new_callable=AsyncMock, return_value=newsapi_items) as mock_newsapi, \
         patch.object(service, "_score_items", new_callable=AsyncMock) as mock_score:

        # _score_items should return the items with scores added
        scored = [
            {**tavily_items[0], "relevance_score": 0.9, "credibility_score": 0.8, "sentiment_score": 0.5},
            {**newsapi_items[0], "relevance_score": 0.7, "credibility_score": 0.6, "sentiment_score": 0.3},
        ]
        mock_score.return_value = scored

        result = await service.search(query="test", category="politics", market_id="miss_market")

    # API clients were called
    mock_tavily.assert_awaited_once()
    mock_newsapi.assert_awaited_once()

    # Cache is now populated
    cached = _cache_get("miss_market:politics")
    assert cached is not None
    assert len(cached) == 2

    # Result matches scored items
    assert result == scored
