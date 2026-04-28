from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass
class ToolDefinition:
    name: str
    description: str
    parameters: dict[str, Any]


@dataclass
class ToolCallRequest:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class LLMMessage:
    role: str
    content: str
    tool_calls: list[ToolCallRequest] | None = None
    tool_call_id: str | None = None


@dataclass
class LLMResponse:
    content: str | None
    tool_calls: list[ToolCallRequest]
    raw_response: Any = None
    usage: dict[str, int] = field(default_factory=dict)
    model: str = ""
    finish_reason: str = "stop"


@runtime_checkable
class LLMProvider(Protocol):
    provider_name: str

    async def complete(
        self,
        messages: list[LLMMessage],
        tools: list[ToolDefinition] | None = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
        system_prompt: str | None = None,
    ) -> LLMResponse: ...

    async def complete_text(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> str: ...
