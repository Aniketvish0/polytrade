"""Tests for app.agent.state — AgentStateManager."""

import asyncio

from app.agent.state import AgentState, AgentStateManager


# ---------------------------------------------------------------------------
# Basic state management
# ---------------------------------------------------------------------------

async def test_initial_state_is_idle():
    mgr = AgentStateManager()
    assert mgr.state is AgentState.IDLE


async def test_state_setter():
    mgr = AgentStateManager()
    mgr.state = AgentState.RUNNING
    assert mgr.state is AgentState.RUNNING

    mgr.state = AgentState.SCANNING
    assert mgr.state is AgentState.SCANNING

    mgr.state = AgentState.ERROR
    assert mgr.state is AgentState.ERROR


async def test_state_setter_all_enum_values():
    mgr = AgentStateManager()
    for s in AgentState:
        mgr.state = s
        assert mgr.state is s


# ---------------------------------------------------------------------------
# Pause / resume
# ---------------------------------------------------------------------------

async def test_pause_sets_paused_state():
    mgr = AgentStateManager()
    mgr.pause()
    assert mgr.state is AgentState.PAUSED


async def test_pause_blocks_wait_if_paused():
    mgr = AgentStateManager()
    mgr.pause()

    # wait_if_paused should NOT complete within 50 ms while paused
    with_timeout = asyncio.wait_for(mgr.wait_if_paused(), timeout=0.05)
    timed_out = False
    try:
        await with_timeout
    except asyncio.TimeoutError:
        timed_out = True
    assert timed_out, "wait_if_paused should block when paused"


async def test_resume_unblocks_wait_if_paused():
    mgr = AgentStateManager()
    mgr.pause()

    async def _resume_soon():
        await asyncio.sleep(0.02)
        mgr.resume()

    asyncio.create_task(_resume_soon())
    # Should complete once resume() is called
    await asyncio.wait_for(mgr.wait_if_paused(), timeout=1.0)
    assert mgr.state is AgentState.RUNNING


async def test_resume_sets_running_state():
    mgr = AgentStateManager()
    mgr.pause()
    mgr.resume()
    assert mgr.state is AgentState.RUNNING


async def test_wait_if_paused_returns_immediately_when_not_paused():
    mgr = AgentStateManager()
    # Should return immediately since the event is already set
    await asyncio.wait_for(mgr.wait_if_paused(), timeout=0.05)


# ---------------------------------------------------------------------------
# Stop
# ---------------------------------------------------------------------------

async def test_stop_sets_stop_event():
    mgr = AgentStateManager()
    assert not mgr.is_stopped()
    mgr.stop()
    assert mgr.is_stopped()


async def test_is_stopped_false_initially():
    mgr = AgentStateManager()
    assert mgr.is_stopped() is False


async def test_stop_also_unblocks_paused_waiter():
    """stop() sets the resume event so any blocked wait_if_paused call unblocks."""
    mgr = AgentStateManager()
    mgr.pause()
    mgr.stop()
    # Should not block anymore
    await asyncio.wait_for(mgr.wait_if_paused(), timeout=0.05)
    assert mgr.is_stopped()
