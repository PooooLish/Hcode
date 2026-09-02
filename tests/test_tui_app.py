from __future__ import annotations

from collections.abc import AsyncIterator
import asyncio
from types import SimpleNamespace

import pytest
from textual.containers import VerticalScroll
from textual.widgets import Static

from hcode.agent import ErrorEvent, LoopComplete
from hcode.app import ChatInput, HcodeApp
from hcode.client import LLMError
from hcode.commands.completion import CompletionPopup
from hcode.config import ProviderConfig
from hcode.permissions import PermissionMode
from hcode.tui import (
    ActivityIndicator,
    RuntimePhase,
    RuntimeSnapshot,
    RuntimeStatusBar,
    ShortcutHelp,
    WorkspaceHeader,
    render_status,
)


def _provider() -> ProviderConfig:
    return ProviderConfig(
        name="test",
        protocol="openai-compat",
        base_url="https://example.invalid",
        model="test-model",
        api_key="test-only-key",
    )


def _ui_agent(run) -> SimpleNamespace:
    return SimpleNamespace(
        permission_mode=PermissionMode.DEFAULT,
        context_window=0,
        work_dir=".",
        plan_mode=False,
        run=run,
    )


@pytest.mark.asyncio
async def test_shell_uses_compact_header_and_runtime_status(monkeypatch) -> None:
    monkeypatch.setattr(HcodeApp, "_select_provider", lambda self, provider: None)
    app = HcodeApp([_provider()])
    async with app.run_test(size=(120, 36)):
        header = app.query_one("#workspace-header", WorkspaceHeader)
        status = app.query_one("#runtime-status", RuntimeStatusBar)
        assert header.compact_layout is False
        assert status.compact_layout is False
        assert header.content_region.height >= 1
        assert status.content_region.height >= 1
        assert len(app.query("#title-bar")) == 0
        assert len(app.query("#mode-label")) == 0
        assert len(app.query("#model-label")) == 0


@pytest.mark.asyncio
async def test_80_column_layout_keeps_critical_status(monkeypatch) -> None:
    monkeypatch.setattr(HcodeApp, "_select_provider", lambda self, provider: None)
    app = HcodeApp([_provider()])
    async with app.run_test(size=(80, 24)):
        header = app.query_one(WorkspaceHeader)
        status = app.query_one(RuntimeStatusBar)
        assert header.compact_layout is True
        assert status.compact_layout is True
        assert header.content_region.height >= 1
        assert status.content_region.height >= 1
        assert header.query_one("#hcode-logo", Static).render().plain == "HCODE"
        assert "DEFAULT" in status.render().plain
        assert "READY" in status.render().plain


@pytest.mark.asyncio
async def test_resize_preserves_draft_completion_and_chat_end(monkeypatch) -> None:
    monkeypatch.setattr(HcodeApp, "_select_provider", lambda self, provider: None)
    app = HcodeApp([_provider()])
    async with app.run_test(size=(120, 36)) as pilot:
        chat_input = app.query_one(ChatInput)
        popup = app.query_one(CompletionPopup)
        chat = app.query_one("#chat-area", VerticalScroll)
        header = app.query_one(WorkspaceHeader)
        status = app.query_one(RuntimeStatusBar)

        chat_input.insert("保留这份 draft @src /help")
        await pilot.pause()
        popup.show_pairs(
            [
                ("/help  Show help", "/help"),
                ("/status  Show status", "/status"),
            ]
        )
        popup.move_down()
        for index in range(60):
            await chat.mount(Static(f"conversation row {index}"))
        await pilot.pause()
        chat.scroll_end(animate=False)
        await pilot.pause()

        assert chat.scroll_y > 0
        assert chat.scroll_y == chat.max_scroll_y
        assert popup.get_selected() == "/status"
        assert header.compact_layout is False
        assert status.compact_layout is False

        await pilot.resize_terminal(80, 24)
        await pilot.pause()

        assert chat_input.text == "保留这份 draft @src /help"
        assert popup.get_selected() == "/status"
        assert chat.scroll_y == chat.max_scroll_y
        assert header.compact_layout is True
        assert status.compact_layout is True

        await pilot.resize_terminal(120, 36)
        await pilot.pause()

        assert chat_input.text == "保留这份 draft @src /help"
        assert popup.get_selected() == "/status"
        assert chat.scroll_y == chat.max_scroll_y
        assert header.compact_layout is False
        assert status.compact_layout is False


@pytest.mark.asyncio
async def test_f1_help_preserves_input(monkeypatch) -> None:
    monkeypatch.setattr(HcodeApp, "_select_provider", lambda self, provider: None)
    app = HcodeApp([_provider()])
    async with app.run_test(size=(120, 36)) as pilot:
        chat_input = app.query_one(ChatInput)
        chat_input.insert("draft")
        await pilot.press("f1")
        assert isinstance(app.screen, ShortcutHelp)
        await pilot.press("escape")
        assert app.query_one(ChatInput).text == "draft"


@pytest.mark.asyncio
async def test_chat_input_has_operational_defaults_and_six_line_limit(monkeypatch) -> None:
    monkeypatch.setattr(HcodeApp, "_select_provider", lambda self, provider: None)
    app = HcodeApp([_provider()])
    async with app.run_test(size=(120, 36)) as pilot:
        widget = app.query_one(ChatInput)
        assert "@" in str(widget.placeholder)
        assert "/" in str(widget.placeholder)
        assert widget.compact is True
        assert widget.styles.max_height.value == 6
        widget.focus()
        await pilot.pause()
        assert widget.has_focus
        assert widget.styles.border_top[0] == "tall"


@pytest.mark.asyncio
async def test_completion_popup_fills_input_width_and_marks_selection(monkeypatch) -> None:
    monkeypatch.setattr(HcodeApp, "_select_provider", lambda self, provider: None)
    app = HcodeApp([_provider()])
    async with app.run_test(size=(120, 36)) as pilot:
        popup = app.query_one(CompletionPopup)
        popup.show_pairs([("/help  Show help", "/help")])
        await pilot.pause()
        assert popup.styles.width is not None
        assert popup.styles.width.value == 100
        selected_style = str(popup.render().spans[0].style)
        assert "reverse" in selected_style
        assert "#875fff" in selected_style


@pytest.mark.parametrize(
    ("snapshot", "compact", "expected"),
    [
        (
            RuntimeSnapshot(),
            False,
            "DEFAULT   READY   context --   Enter send · Shift+Enter newline · F1 help",
        ),
        (
            RuntimeSnapshot(phase=RuntimePhase.WORKING, elapsed=1.2),
            False,
            "DEFAULT   WORKING · 1.2s   context --   Esc cancel · Enter interrupts & sends",
        ),
        (
            RuntimeSnapshot(),
            True,
            "DEFAULT   READY",
        ),
        (
            RuntimeSnapshot(phase=RuntimePhase.WORKING, elapsed=1.2),
            True,
            "DEFAULT   WORKING · 1.2s   Esc cancel",
        ),
    ],
)
def test_runtime_hints_follow_phase_and_layout(
    snapshot: RuntimeSnapshot, compact: bool, expected: str
) -> None:
    assert render_status(snapshot, compact=compact).plain == expected


@pytest.mark.asyncio
async def test_activity_finishes_once_inside_current_ai_row(monkeypatch) -> None:
    clock = [100.0]
    run_started = asyncio.Event()
    finish_run = asyncio.Event()

    async def run(_conversation) -> AsyncIterator[LoopComplete]:
        run_started.set()
        await finish_run.wait()
        yield LoopComplete(total_turns=1)

    monkeypatch.setattr(HcodeApp, "_select_provider", lambda self, provider: None)
    monkeypatch.setattr(HcodeApp, "_start_spinner", lambda self: None)
    monkeypatch.setattr("hcode.app._time.monotonic", lambda: clock[0])
    app = HcodeApp([_provider()])
    async with app.run_test(size=(120, 36)):
        app.agent = _ui_agent(run)
        task = asyncio.create_task(app._send_message("hello"))
        await run_started.wait()
        clock[0] = 102.5
        app._tick_spinner()
        try:
            activity = next(iter(app.query(ActivityIndicator)), None)
            assert activity is not None
            assert activity.parent.has_class("ai-row")
            assert activity.render().plain == "○ Working · 2.5s"
        finally:
            finish_run.set()
            await task

        activities = list(app.query(ActivityIndicator))
        assert len(activities) == 1
        assert activities[0].render().plain == "✓ Completed in 2.5s"
        assert app._runtime_error is False
        assert "READY" in app.query_one(RuntimeStatusBar).render().plain


@pytest.mark.asyncio
async def test_cancelled_activity_leaves_one_terminal_line(monkeypatch) -> None:
    run_started = asyncio.Event()

    async def run(_conversation) -> AsyncIterator[LoopComplete]:
        run_started.set()
        await asyncio.Event().wait()
        yield LoopComplete(total_turns=1)

    monkeypatch.setattr(HcodeApp, "_select_provider", lambda self, provider: None)
    monkeypatch.setattr(HcodeApp, "_start_spinner", lambda self: None)
    app = HcodeApp([_provider()])
    async with app.run_test(size=(120, 36)):
        app.agent = _ui_agent(run)
        task = asyncio.create_task(app._send_message("hello"))
        await run_started.wait()
        task.cancel()
        await task

        activities = list(app.query(ActivityIndicator))
        assert len(activities) == 1
        assert "Cancelled" in activities[0].render().plain


@pytest.mark.asyncio
async def test_error_event_then_loop_complete_preserves_failed_runtime(monkeypatch) -> None:
    async def run(_conversation) -> AsyncIterator[ErrorEvent | LoopComplete]:
        yield ErrorEvent(message="boom")
        yield LoopComplete(total_turns=1)

    monkeypatch.setattr(HcodeApp, "_select_provider", lambda self, provider: None)
    monkeypatch.setattr(HcodeApp, "_start_spinner", lambda self: None)
    app = HcodeApp([_provider()])
    async with app.run_test(size=(120, 36)):
        app.agent = _ui_agent(run)
        await app._send_message("hello")

        activities = list(app.query(ActivityIndicator))
        assert len(activities) == 1
        assert "Failed" in activities[0].render().plain
        assert app._runtime_error is True
        assert "ERROR" in app.query_one(RuntimeStatusBar).render().plain


@pytest.mark.asyncio
async def test_llm_error_leaves_one_failed_activity_line(monkeypatch) -> None:
    async def run(_conversation) -> AsyncIterator[LoopComplete]:
        if False:
            yield LoopComplete(total_turns=1)
        raise LLMError("boom")

    monkeypatch.setattr(HcodeApp, "_select_provider", lambda self, provider: None)
    monkeypatch.setattr(HcodeApp, "_start_spinner", lambda self: None)
    app = HcodeApp([_provider()])
    async with app.run_test(size=(120, 36)):
        app.agent = _ui_agent(run)
        await app._send_message("hello")

        activities = list(app.query(ActivityIndicator))
        assert len(activities) == 1
        assert "Failed" in activities[0].render().plain


@pytest.mark.asyncio
async def test_error_phase_persists_after_stream_finishes(monkeypatch) -> None:
    monkeypatch.setattr(HcodeApp, "_select_provider", lambda self, provider: None)
    app = HcodeApp([_provider()])
    async with app.run_test(size=(120, 36)):
        app._streaming = False
        app._runtime_error = True
        app._refresh_runtime_status()
        assert "ERROR" in app.query_one(RuntimeStatusBar).render().plain


def test_runtime_snapshot_uses_context_and_cached_teammate_state(monkeypatch) -> None:
    app = HcodeApp([_provider()])
    app.agent = SimpleNamespace(
        permission_mode=PermissionMode.PLAN,
        context_window=400,
    )
    monkeypatch.setattr(app.conversation, "current_tokens", lambda: 100)
    app._active_teammates = 2
    app._mcp_connecting = True
    app._streaming = True
    app._thinking_start = 0.0

    snapshot = app._runtime_snapshot()

    assert snapshot.permission == "PLAN"
    assert snapshot.phase is RuntimePhase.WORKING
    assert snapshot.context_percent == 25
    assert snapshot.teammates == 2
    assert snapshot.mcp_state == "CONNECTING"
    assert snapshot.elapsed > 0.0
