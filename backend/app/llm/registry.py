from app.config import settings
from app.llm.base import LLMProvider


class LLMRegistry:
    _providers: dict[str, LLMProvider] = {}
    _default: str | None = None

    @classmethod
    def initialize(cls):
        if settings.OPENAI_API_KEY:
            from app.llm.providers.openai import OpenAIProvider

            cls.register("openai", OpenAIProvider(api_key=settings.OPENAI_API_KEY))

        if settings.ANTHROPIC_API_KEY:
            from app.llm.providers.anthropic import AnthropicProvider

            cls.register("anthropic", AnthropicProvider(api_key=settings.ANTHROPIC_API_KEY))

        if settings.GOOGLE_API_KEY:
            from app.llm.providers.gemini import GeminiProvider

            cls.register("gemini", GeminiProvider(api_key=settings.GOOGLE_API_KEY))

        if settings.DEFAULT_LLM_PROVIDER in cls._providers:
            cls._default = settings.DEFAULT_LLM_PROVIDER
        elif cls._providers:
            cls._default = next(iter(cls._providers))

    @classmethod
    def register(cls, name: str, provider: LLMProvider):
        cls._providers[name] = provider

    @classmethod
    def get(cls, name: str | None = None) -> LLMProvider:
        key = name or cls._default
        if not key or key not in cls._providers:
            available = list(cls._providers.keys())
            raise RuntimeError(
                f"LLM provider '{key}' not available. Available: {available}"
            )
        return cls._providers[key]

    @classmethod
    def available(cls) -> list[str]:
        return list(cls._providers.keys())

    @classmethod
    def set_default(cls, name: str):
        if name not in cls._providers:
            raise ValueError(f"Provider '{name}' not registered")
        cls._default = name
