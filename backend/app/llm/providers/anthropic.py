import uuid

from anthropic import AsyncAnthropic

from app.llm.base import LLMMessage, LLMResponse, ToolCallRequest, ToolDefinition


class AnthropicProvider:
    provider_name = "anthropic"

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model

    def _convert_tools(self, tools: list[ToolDefinition]) -> list[dict]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "input_schema": t.parameters,
            }
            for t in tools
        ]

    def _convert_messages(self, messages: list[LLMMessage]) -> list[dict]:
        result = []
        for msg in messages:
            if msg.role == "tool_result":
                result.append(
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": msg.tool_call_id,
                                "content": msg.content,
                            }
                        ],
                    }
                )
            else:
                result.append({"role": msg.role, "content": msg.content})
        return result

    async def complete(
        self,
        messages: list[LLMMessage],
        tools: list[ToolDefinition] | None = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
        system_prompt: str | None = None,
    ) -> LLMResponse:
        kwargs = {
            "model": self.model,
            "messages": self._convert_messages(messages),
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if system_prompt:
            kwargs["system"] = system_prompt
        if tools:
            kwargs["tools"] = self._convert_tools(tools)

        response = await self.client.messages.create(**kwargs)

        content = None
        tool_calls = []
        for block in response.content:
            if block.type == "text":
                content = block.text
            elif block.type == "tool_use":
                tool_calls.append(
                    ToolCallRequest(id=block.id, name=block.name, arguments=block.input)
                )

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            raw_response=response,
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
            model=self.model,
            finish_reason=response.stop_reason or "stop",
        )

    async def complete_text(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> str:
        messages = [LLMMessage(role="user", content=prompt)]
        response = await self.complete(messages, temperature=temperature, max_tokens=max_tokens, system_prompt=system_prompt)
        return response.content or ""
