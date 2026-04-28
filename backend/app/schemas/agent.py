from pydantic import BaseModel


class AgentStatusResponse(BaseModel):
    status: str
    current_task: str | None = None
    last_scan_at: str | None = None
