import json
import uuid

from openai import AsyncOpenAI

from app.llm.base import LLMMessage, LLMResponse, ToolCallRequest, ToolDefinition


class OpenAIProvider:
    provider_name = "openai"

    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model

    def _convert_tools(self, tools: list[ToolDefinition]) -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                },
            }
            for t in tools
        ]

    def _convert_messages(
        self, messages: list[LLMMessage], system_prompt: str | None
    ) -> list[dict]:
        result = []
        if system_prompt:
            result.append({"role": "system", "content": system_prompt})
        for msg in messages:
            if msg.role == "tool_result":
                result.append(
                    {"role": "tool", "content": msg.content, "tool_call_id": msg.tool_call_id}
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
            "messages": self._convert_messages(messages, system_prompt),
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if tools:
            kwargs["tools"] = self._convert_tools(tools)

        response = await self.client.chat.completions.create(**kwargs)
        choice = response.choices[0]

        tool_calls = []
        if choice.message.tool_calls:
            for tc in choice.message.tool_calls:
                tool_calls.append(
                    ToolCallRequest(
                        id=tc.id,
                        name=tc.function.name,
                        arguments=json.loads(tc.function.arguments),
                    )
                )

        return LLMResponse(
            content=choice.message.content,
            tool_calls=tool_calls,
            raw_response=response,
            usage={
                "input_tokens": response.usage.prompt_tokens if response.usage else 0,
                "output_tokens": response.usage.completion_tokens if response.usage else 0,
            },
            model=self.model,
            finish_reason=choice.finish_reason or "stop",
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
