from fastapi import APIRouter, Depends, HTTPException, Request

from app.db.models.user import User
from app.dependencies import get_current_user
from app.schemas.agent import AgentStatusResponse

router = APIRouter()


@router.get("/status", response_model=AgentStatusResponse)
async def get_agent_status(
    request: Request, user: User = Depends(get_current_user)
):
    user_key = str(user.id)
    agent_loop = request.app.state.agent_loops.get(user_key)
    if not agent_loop:
        return AgentStatusResponse(status="offline")
    return AgentStatusResponse(
        status=agent_loop.state_manager.state.value,
        current_task=agent_loop.current_task,
    )


@router.post("/start", response_model=AgentStatusResponse)
async def start_agent(request: Request, user: User = Depends(get_current_user)):
    user_key = str(user.id)
    if user_key in request.app.state.agent_loops:
        existing = request.app.state.agent_loops[user_key]
        if not existing.state_manager.is_stopped():
            raise HTTPException(status_code=400, detail="Agent already running")

    from app.agent.loop import AgentLoop
    from app.db.engine import async_session
    from app.ws.manager import ws_manager

    loop = AgentLoop(
        user_id=user.id,
        user_email=user.email,
        db_session_factory=async_session,
        ws_manager=ws_manager,
    )
    request.app.state.agent_loops[user_key] = loop
    await loop.start()
    return AgentStatusResponse(status="scanning")


@router.post("/pause", response_model=AgentStatusResponse)
async def pause_agent(request: Request, user: User = Depends(get_current_user)):
    user_key = str(user.id)
    agent_loop = request.app.state.agent_loops.get(user_key)
    if not agent_loop:
        raise HTTPException(status_code=400, detail="Agent not running")
    agent_loop.pause()
    return AgentStatusResponse(status="paused")


@router.post("/resume", response_model=AgentStatusResponse)
async def resume_agent(request: Request, user: User = Depends(get_current_user)):
    user_key = str(user.id)
    agent_loop = request.app.state.agent_loops.get(user_key)
    if not agent_loop:
        raise HTTPException(status_code=400, detail="Agent not running")
    agent_loop.resume()
    return AgentStatusResponse(status="scanning")
