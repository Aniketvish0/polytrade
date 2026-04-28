import asyncio
from enum import Enum


class AgentState(Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    SCANNING = "scanning"
    RESEARCHING = "researching"
    ANALYZING = "analyzing"
    TRADING = "trading"
    ERROR = "error"


class AgentStateManager:
    def __init__(self):
        self._state: AgentState = AgentState.IDLE
        self._resume_event = asyncio.Event()
        self._resume_event.set()
        self._stop_event = asyncio.Event()

    @property
    def state(self) -> AgentState:
        return self._state

    @state.setter
    def state(self, value: AgentState):
        self._state = value

    def pause(self):
        self._state = AgentState.PAUSED
        self._resume_event.clear()

    def resume(self):
        self._resume_event.set()
        self._state = AgentState.RUNNING

    def stop(self):
        self._stop_event.set()
        self._resume_event.set()

    async def wait_if_paused(self):
        await self._resume_event.wait()

    def is_stopped(self) -> bool:
        return self._stop_event.is_set()
