from __future__ import annotations

from types import SimpleNamespace

import pytest

from hcode.client import OpenAICompatClient
from hcode.config import ProviderConfig
from hcode.conversation import ConversationManager
from hcode.tools.base import StreamEnd, TextDelta


pytestmark = pytest.mark.asyncio


class _ChunkStream:
    def __init__(self, chunks: list[SimpleNamespace]) -> None:
        self._chunks = iter(chunks)

    def __aiter__(self) -> _ChunkStream:
        return self

    async def __anext__(self) -> SimpleNamespace:
        try:
            return next(self._chunks)
        except StopIteration as exc:
            raise StopAsyncIteration from exc


class _Completions:
    def __init__(self, chunks: list[SimpleNamespace]) -> None:
        self._chunks = chunks

    async def create(self, **_kwargs: object) -> _ChunkStream:
        return _ChunkStream(self._chunks)


def _choice_chunk(
    *,
    content: str | None = None,
    finish_reason: str | None = None,
    usage: SimpleNamespace | None = None,
) -> SimpleNamespace:
    delta = SimpleNamespace(
        content=content,
        reasoning_content=None,
        tool_calls=None,
    )
    choice = SimpleNamespace(delta=delta, finish_reason=finish_reason)
    return SimpleNamespace(choices=[choice], usage=usage)


def _usage_chunk(*, prompt: int, completion: int, cached: int = 0) -> SimpleNamespace:
    usage = SimpleNamespace(
        prompt_tokens=prompt,
        completion_tokens=completion,
        prompt_tokens_details=SimpleNamespace(cached_tokens=cached),
    )
    return SimpleNamespace(choices=[], usage=usage)


def _client(chunks: list[SimpleNamespace]) -> OpenAICompatClient:
    config = ProviderConfig(
        name="test",
        protocol="openai-compat",
        base_url="https://example.invalid",
        model="test-model",
        api_key="test-key",
    )
    client = OpenAICompatClient(config)
    client._client = SimpleNamespace(
        chat=SimpleNamespace(completions=_Completions(chunks))
    )
    return client


async def _events(chunks: list[SimpleNamespace]) -> list[object]:
    conversation = ConversationManager()
    conversation.add_user_message("hello")
    return [event async for event in _client(chunks).stream(conversation)]


async def test_emits_stream_end_when_provider_omits_usage_chunk() -> None:
    events = await _events(
        [
            _choice_chunk(content="done"),
            _choice_chunk(finish_reason="stop"),
        ]
    )

    assert [event.text for event in events if isinstance(event, TextDelta)] == ["done"]
    ends = [event for event in events if isinstance(event, StreamEnd)]
    assert ends == [StreamEnd("end_turn", input_tokens=0, output_tokens=0)]


async def test_uses_usage_attached_to_terminal_choice_chunk() -> None:
    usage = SimpleNamespace(
        prompt_tokens=10,
        completion_tokens=3,
        prompt_tokens_details=SimpleNamespace(cached_tokens=2),
    )

    events = await _events(
        [_choice_chunk(content="done", finish_reason="stop", usage=usage)]
    )

    ends = [event for event in events if isinstance(event, StreamEnd)]
    assert ends == [
        StreamEnd(
            "end_turn",
            input_tokens=8,
            output_tokens=3,
            cache_read=2,
        )
    ]


async def test_usage_only_chunk_emits_exactly_one_stream_end() -> None:
    events = await _events(
        [
            _choice_chunk(content="done", finish_reason="stop"),
            _usage_chunk(prompt=11, completion=4, cached=1),
        ]
    )

    ends = [event for event in events if isinstance(event, StreamEnd)]
    assert ends == [
        StreamEnd(
            "end_turn",
            input_tokens=10,
            output_tokens=4,
            cache_read=1,
        )
    ]


async def test_length_finish_reason_maps_to_max_tokens() -> None:
    events = await _events([_choice_chunk(finish_reason="length")])

    ends = [event for event in events if isinstance(event, StreamEnd)]
    assert ends == [StreamEnd("max_tokens", input_tokens=0, output_tokens=0)]
