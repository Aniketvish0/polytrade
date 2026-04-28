import uuid

import google.generativeai as genai

from app.llm.base import LLMMessage, LLMResponse, ToolCallRequest, ToolDefinition


class GeminiProvider:
    provider_name = "gemini"

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        genai.configure(api_key=api_key)
        self.model_name = model

    def _convert_tools(self, tools: list[ToolDefinition]) -> list:
        declarations = []
        for t in tools:
            params = t.parameters.copy()
            params.pop("additionalProperties", None)
            declarations.append(
                genai.protos.FunctionDeclaration(
                    name=t.name,
                    description=t.description,
                    parameters=params,
                )
            )
        return [genai.protos.Tool(function_declarations=declarations)]

    def _convert_messages(self, messages: list[LLMMessage]) -> list[dict]:
        result = []
        for msg in messages:
            role = "model" if msg.role == "assistant" else "user"
            result.append({"role": role, "parts": [msg.content]})
        return result

    async def complete(
        self,
        messages: list[LLMMessage],
        tools: list[ToolDefinition] | None = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
        system_prompt: str | None = None,
    ) -> LLMResponse:
        model = genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=system_prompt,
            generation_config=genai.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            ),
        )

        kwargs = {}
        if tools:
            kwargs["tools"] = self._convert_tools(tools)

        history = self._convert_messages(messages[:-1]) if len(messages) > 1 else []
        chat = model.start_chat(history=history)

        last_message = messages[-1].content if messages else ""
        response = await chat.send_message_async(last_message, **kwargs)

        content = None
        tool_calls = []
        for part in response.parts:
            if part.text:
                content = part.text
            elif part.function_call:
                tool_calls.append(
                    ToolCallRequest(
                        id=str(uuid.uuid4()),
                        name=part.function_call.name,
                        arguments=dict(part.function_call.args),
                    )
                )

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            raw_response=response,
            usage={},
            model=self.model_name,
            finish_reason="stop",
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
