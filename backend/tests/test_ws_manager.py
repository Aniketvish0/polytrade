"""Tests for app.ws.manager — ConnectionManager."""

from unittest.mock import AsyncMock, MagicMock

from app.ws.events import WSEvent
from app.ws.manager import ConnectionManager


def _make_ws(*, fail_send: bool = False) -> AsyncMock:
    """Create a mock WebSocket. If *fail_send* is True, ``send_text`` raises."""
    ws = AsyncMock()
    ws.accept = AsyncMock()
    if fail_send:
        ws.send_text = AsyncMock(side_effect=RuntimeError("connection closed"))
    else:
        ws.send_text = AsyncMock()
    return ws


def _make_event() -> WSEvent:
    return WSEvent(type="test:ping", data={"ok": True})


# ---------------------------------------------------------------------------
# connect
# ---------------------------------------------------------------------------

async def test_connect_adds_websocket():
    mgr = ConnectionManager()
    ws = _make_ws()
    await mgr.connect(ws, "user-1")

    ws.accept.assert_awaited_once()
    assert "user-1" in mgr._connections
    assert ws in mgr._connections["user-1"]


async def test_connect_multiple_sockets_same_user():
    mgr = ConnectionManager()
    ws1 = _make_ws()
    ws2 = _make_ws()
    await mgr.connect(ws1, "user-1")
    await mgr.connect(ws2, "user-1")

    assert len(mgr._connections["user-1"]) == 2


async def test_connect_different_users():
    mgr = ConnectionManager()
    ws1 = _make_ws()
    ws2 = _make_ws()
    await mgr.connect(ws1, "user-1")
    await mgr.connect(ws2, "user-2")

    assert "user-1" in mgr._connections
    assert "user-2" in mgr._connections


# ---------------------------------------------------------------------------
# disconnect
# ---------------------------------------------------------------------------

async def test_disconnect_removes_websocket():
    mgr = ConnectionManager()
    ws = _make_ws()
    await mgr.connect(ws, "user-1")

    mgr.disconnect(ws, "user-1")
    assert "user-1" not in mgr._connections


async def test_disconnect_keeps_other_sockets():
    mgr = ConnectionManager()
    ws1 = _make_ws()
    ws2 = _make_ws()
    await mgr.connect(ws1, "user-1")
    await mgr.connect(ws2, "user-1")

    mgr.disconnect(ws1, "user-1")
    assert mgr._connections["user-1"] == [ws2]


async def test_disconnect_unknown_user_no_crash():
    mgr = ConnectionManager()
    ws = _make_ws()
    # Should not raise
    mgr.disconnect(ws, "nonexistent-user")


async def test_disconnect_unknown_ws_no_crash():
    mgr = ConnectionManager()
    ws1 = _make_ws()
    ws2 = _make_ws()
    await mgr.connect(ws1, "user-1")

    # ws2 was never connected — should not raise
    mgr.disconnect(ws2, "user-1")
    assert mgr._connections["user-1"] == [ws1]


# ---------------------------------------------------------------------------
# send_to_user
# ---------------------------------------------------------------------------

async def test_send_to_user_sends_to_connected():
    mgr = ConnectionManager()
    ws = _make_ws()
    await mgr.connect(ws, "user-1")

    ev = _make_event()
    await mgr.send_to_user("user-1", ev)

    ws.send_text.assert_awaited_once()
    sent = ws.send_text.call_args[0][0]
    assert '"test:ping"' in sent


async def test_send_to_user_ignores_unknown():
    mgr = ConnectionManager()
    ev = _make_event()
    # Should not raise when user has no connections
    await mgr.send_to_user("ghost-user", ev)


async def test_send_to_user_removes_dead_connections():
    mgr = ConnectionManager()
    good_ws = _make_ws()
    dead_ws = _make_ws(fail_send=True)

    await mgr.connect(good_ws, "user-1")
    await mgr.connect(dead_ws, "user-1")

    ev = _make_event()
    await mgr.send_to_user("user-1", ev)

    # The dead connection should have been pruned
    assert dead_ws not in mgr._connections.get("user-1", [])
    assert good_ws in mgr._connections["user-1"]


async def test_send_to_user_all_dead_cleans_up():
    mgr = ConnectionManager()
    dead_ws = _make_ws(fail_send=True)
    await mgr.connect(dead_ws, "user-1")

    ev = _make_event()
    await mgr.send_to_user("user-1", ev)

    # user-1 entry should be fully removed
    assert "user-1" not in mgr._connections


# ---------------------------------------------------------------------------
# broadcast
# ---------------------------------------------------------------------------

async def test_broadcast_sends_to_all_users():
    mgr = ConnectionManager()
    ws1 = _make_ws()
    ws2 = _make_ws()
    await mgr.connect(ws1, "user-1")
    await mgr.connect(ws2, "user-2")

    ev = _make_event()
    await mgr.broadcast(ev)

    ws1.send_text.assert_awaited_once()
    ws2.send_text.assert_awaited_once()


async def test_broadcast_removes_dead_connections():
    mgr = ConnectionManager()
    good_ws = _make_ws()
    dead_ws = _make_ws(fail_send=True)
    await mgr.connect(good_ws, "user-1")
    await mgr.connect(dead_ws, "user-2")

    ev = _make_event()
    await mgr.broadcast(ev)

    good_ws.send_text.assert_awaited_once()
    assert "user-2" not in mgr._connections


async def test_broadcast_no_connections():
    mgr = ConnectionManager()
    ev = _make_event()
    # Should not raise
    await mgr.broadcast(ev)
