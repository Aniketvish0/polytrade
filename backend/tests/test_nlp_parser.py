"""Tests for CommandParser (app/nlp/parser.py).

The parser now delegates ALL input to ConversationEngine — natural language,
slash commands, mixed prompts. These tests verify that delegation happens
correctly from a QA perspective.
"""

from unittest.mock import AsyncMock, patch


# ---------------------------------------------------------------------------
# Natural language → ConversationEngine
# ---------------------------------------------------------------------------


async def test_natural_language_delegates_to_conversation_engine(mock_db, mock_user):
    from app.nlp.parser import CommandParser

    mock_response = {"type": "chat", "content": "Here is your portfolio.", "message_type": "text"}

    with patch("app.nlp.conversation.ConversationEngine") as MockEngine:
        instance = AsyncMock()
        instance.respond = AsyncMock(return_value=mock_response)
        MockEngine.return_value = instance

        parser = CommandParser(db=mock_db, user=mock_user)
        result = await parser.process("How is my portfolio doing?")

    assert result == mock_response
    instance.respond.assert_awaited_once_with("How is my portfolio doing?", conversation_history=None)


# ---------------------------------------------------------------------------
# Slash commands also go through ConversationEngine (LLM is context-aware)
# ---------------------------------------------------------------------------


async def test_slash_start_delegates_to_conversation_engine(mock_db, mock_user):
    from app.nlp.parser import CommandParser

    mock_response = {
        "type": "chat",
        "content": "Starting your agent now.",
        "message_type": "text",
        "action": {"type": "start_agent", "data": {}},
    }

    with patch("app.nlp.conversation.ConversationEngine") as MockEngine:
        instance = AsyncMock()
        instance.respond = AsyncMock(return_value=mock_response)
        MockEngine.return_value = instance

        parser = CommandParser(db=mock_db, user=mock_user)
        result = await parser.process("/start")

    assert result["action"]["type"] == "start_agent"
    instance.respond.assert_awaited_once()


async def test_slash_pause_delegates_to_conversation_engine(mock_db, mock_user):
    from app.nlp.parser import CommandParser

    mock_response = {"type": "chat", "content": "Pausing.", "message_type": "text"}

    with patch("app.nlp.conversation.ConversationEngine") as MockEngine:
        instance = AsyncMock()
        instance.respond = AsyncMock(return_value=mock_response)
        MockEngine.return_value = instance

        parser = CommandParser(db=mock_db, user=mock_user)
        result = await parser.process("/pause")

    instance.respond.assert_awaited_once()


async def test_slash_help_delegates_to_conversation_engine(mock_db, mock_user):
    from app.nlp.parser import CommandParser

    mock_response = {"type": "chat", "content": "Here's what I can do.", "message_type": "text"}

    with patch("app.nlp.conversation.ConversationEngine") as MockEngine:
        instance = AsyncMock()
        instance.respond = AsyncMock(return_value=mock_response)
        MockEngine.return_value = instance

        parser = CommandParser(db=mock_db, user=mock_user)
        result = await parser.process("/help")

    instance.respond.assert_awaited_once()


# ---------------------------------------------------------------------------
# Mixed input (command + natural language) goes to ConversationEngine
# ---------------------------------------------------------------------------


async def test_mixed_input_delegates_to_conversation_engine(mock_db, mock_user):
    from app.nlp.parser import CommandParser

    mock_response = {"type": "chat", "content": "Done.", "message_type": "text"}

    with patch("app.nlp.conversation.ConversationEngine") as MockEngine:
        instance = AsyncMock()
        instance.respond = AsyncMock(return_value=mock_response)
        MockEngine.return_value = instance

        parser = CommandParser(db=mock_db, user=mock_user)
        result = await parser.process("start the agent and focus on politics")

    instance.respond.assert_awaited_once()


# ---------------------------------------------------------------------------
# Conversation history is passed through
# ---------------------------------------------------------------------------


async def test_conversation_history_passed_to_engine(mock_db, mock_user):
    from app.nlp.parser import CommandParser

    history = [{"role": "user", "content": "hello"}, {"role": "agent", "content": "hi"}]
    mock_response = {"type": "chat", "content": "Sure.", "message_type": "text"}

    with patch("app.nlp.conversation.ConversationEngine") as MockEngine:
        instance = AsyncMock()
        instance.respond = AsyncMock(return_value=mock_response)
        MockEngine.return_value = instance

        parser = CommandParser(db=mock_db, user=mock_user)
        await parser.process("what's happening?", conversation_history=history)

    instance.respond.assert_awaited_once_with("what's happening?", conversation_history=history)


# ---------------------------------------------------------------------------
# Empty input returns info message
# ---------------------------------------------------------------------------


async def test_empty_input_returns_info(mock_db, mock_user):
    from app.nlp.parser import CommandParser

    parser = CommandParser(db=mock_db, user=mock_user)
    result = await parser.process("")

    assert result["type"] == "info"
    assert result["message_type"] == "text"


async def test_whitespace_only_returns_info(mock_db, mock_user):
    from app.nlp.parser import CommandParser

    parser = CommandParser(db=mock_db, user=mock_user)
    result = await parser.process("   ")

    assert result["type"] == "info"
