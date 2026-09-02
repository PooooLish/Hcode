from __future__ import annotations

import os
import re
from typing import get_type_hints

import pytest
from rich.color import Color
from rich.console import Console
from rich.text import Text
from textual.app import App, ComposeResult
from textual.widgets import Static

from hcode.tui import (
    ActivityIndicator,
    ActivityPhase,
    RuntimePhase,
    RuntimeSnapshot,
    RuntimeStatusBar,
    ShortcutHelp,
    WorkspaceHeader,
    render_brand,
    render_status,
)
from scripts.capture_tui_review import capture


def _svg_text_fill(svg: str, text_pattern: str) -> str:
    text = re.search(
        rf'<text class="([^"]+)"[^>]*>{text_pattern}</text>',
        svg,
        re.DOTALL,
    )
    assert text is not None
    style = re.search(
        rf"\.{re.escape(text.group(1))} \{{ ([^}}]+) \}}",
        svg,
    )
    assert style is not None
    fill = re.search(r"fill: #(\w{6})", style.group(1))
    assert fill is not None
    return f"#{fill.group(1)}"


def _contrast_ratio(foreground: str, background: str) -> float:
    def luminance(color: str) -> float:
        channels = [int(color[index:index + 2], 16) / 255 for index in (1, 3, 5)]
        linear = [
            channel / 12.92
            if channel <= 0.04045
            else ((channel + 0.055) / 1.055) ** 2.4
            for channel in channels
        ]
        return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]

    lighter, darker = sorted((luminance(foreground), luminance(background)), reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


def test_header_has_isolated_bold_red_hcode_wordmark() -> None:
    content = render_brand()
    assert content.plain == "HCODE"
    assert "bold" in str(content.style)
    assert "red" in str(content.style)


def test_compact_header_keeps_only_logo() -> None:
    header = WorkspaceHeader("很长的工作区名称", "deepseek-v4-pro")
    header.set_compact(True)
    assert header.compact_layout is True


def test_status_never_hides_permission_or_phase() -> None:
    snapshot = RuntimeSnapshot(
        permission="BYPASS",
        phase=RuntimePhase.WORKING,
        context_percent=12,
        teammates=2,
        mcp_state="CONNECTING",
        elapsed=2.4,
    )
    compact = render_status(snapshot, compact=True).plain
    assert "BYPASS" in compact
    assert "WORKING" in compact
    assert "context" not in compact


@pytest.mark.parametrize(
    "permission",
    ["DEFAULT", "ACCEPT EDITS", "PLAN", "BYPASS"],
)
@pytest.mark.parametrize(
    "phase",
    [RuntimePhase.READY, RuntimePhase.WORKING, RuntimePhase.ERROR],
)
def test_status_displays_every_permission_and_phase_combination(
    permission: str, phase: RuntimePhase
) -> None:
    status = render_status(
        RuntimeSnapshot(permission=permission, phase=phase),
        compact=True,
    ).plain

    assert permission in status
    assert phase.value in status


def test_unknown_context_is_explicit() -> None:
    snapshot = RuntimeSnapshot(permission="DEFAULT", phase=RuntimePhase.READY)
    assert "context --" in render_status(snapshot, compact=False).plain


def test_bypass_and_error_colors_do_not_leak_into_context() -> None:
    status = render_status(
        RuntimeSnapshot(
            permission="BYPASS",
            phase=RuntimePhase.ERROR,
            context_percent=12,
        ),
        compact=False,
    )
    console = Console(force_terminal=True, color_system="truecolor")

    bypass = status.get_style_at_offset(console, status.plain.index("BYPASS"))
    error = status.get_style_at_offset(console, status.plain.index("ERROR"))
    context = status.get_style_at_offset(console, status.plain.index("context"))

    assert bypass.color == Color.parse("red")
    assert error.color == Color.parse("red")
    assert context.color != Color.parse("red")
    assert context.bold is not True


def test_activity_uses_deterministic_terminal_states() -> None:
    activity = ActivityIndicator()
    activity.start()
    assert activity.render().plain == "○ Working · 0.0s"
    activity.set_elapsed(2.4)
    assert "Working · 2.4s" in activity.render().plain
    activity.finish(ActivityPhase.COMPLETED, 2.4)
    assert activity.render().plain == "✓ Completed in 2.4s"


def test_presentation_mutators_have_none_return_contracts() -> None:
    mutators = (
        WorkspaceHeader.set_context,
        WorkspaceHeader.set_compact,
        RuntimeStatusBar.set_snapshot,
        RuntimeStatusBar.set_compact,
        ActivityIndicator.start,
        ActivityIndicator.set_elapsed,
        ActivityIndicator.finish,
    )
    for mutator in mutators:
        assert get_type_hints(mutator)["return"] is type(None)


class ComponentApp(App[None]):
    def compose(self) -> ComposeResult:
        yield WorkspaceHeader("workspace", "model")
        yield RuntimeStatusBar()


@pytest.mark.asyncio
async def test_header_rerenders_separate_context_children() -> None:
    app = ComponentApp()
    async with app.run_test():
        header = app.query_one(WorkspaceHeader)
        header.set_context("新的工作区", "new-model")
        assert app.query_one("#workspace-name", Static).render().plain == "新的工作区"
        assert app.query_one("#header-model", Static).render().plain == "new-model"
        header.set_compact(True)
        assert app.query_one("#workspace-name", Static).display is False
        assert app.query_one("#header-model", Static).display is False


@pytest.mark.asyncio
async def test_review_capture_preserves_red_wordmark_with_no_color(
    monkeypatch, tmp_path
) -> None:
    monkeypatch.setenv("NO_COLOR", "1")
    path = tmp_path / "preview.svg"

    await capture(path, size=(80, 24), state="idle")

    assert os.environ["NO_COLOR"] == "1"
    svg = path.read_text(encoding="utf-8")

    wordmark = re.search(r'<text class="([^"]+)"[^>]*>HCODE</text>', svg)
    assert wordmark is not None
    style = re.search(
        rf"\.{re.escape(wordmark.group(1))} \{{ ([^}}]+) \}}",
        svg,
    )
    assert style is not None
    fill = re.search(r"fill: #(\w{6})", style.group(1))
    assert fill is not None
    red, green, blue = bytes.fromhex(fill.group(1))
    assert red >= 128
    assert red > green
    assert red > blue


@pytest.mark.asyncio
async def test_review_capture_shows_input_focus(tmp_path) -> None:
    path = tmp_path / "preview.svg"

    await capture(path, size=(80, 24), state="working")

    svg = path.read_text(encoding="utf-8")
    assert "#875fff" in svg.lower()


@pytest.mark.asyncio
async def test_review_idle_capture_shows_chinese_placeholder(tmp_path) -> None:
    path = tmp_path / "preview.svg"

    await capture(path, size=(120, 36), state="idle")

    svg = path.read_text(encoding="utf-8")
    assert "输入消息，@" in svg
    assert "引用文件，/" in svg
    assert "执行命令" in svg


@pytest.mark.asyncio
async def test_review_idle_placeholder_meets_normal_text_contrast(tmp_path) -> None:
    path = tmp_path / "preview.svg"

    await capture(path, size=(120, 36), state="idle")

    svg = path.read_text(encoding="utf-8")
    foreground = _svg_text_fill(svg, r"输入消息，@.*?执行命令")
    assert _contrast_ratio(foreground, "#1e1e1e") >= 4.5


@pytest.mark.asyncio
async def test_review_error_context_meets_enhanced_contrast(tmp_path) -> None:
    path = tmp_path / "preview.svg"

    await capture(path, size=(120, 36), state="error-bypass")

    svg = path.read_text(encoding="utf-8")
    foreground = _svg_text_fill(svg, r"[^<]*context&#160;12%")
    assert _contrast_ratio(foreground, "#121212") >= 4.5


def test_status_bar_rerenders_when_snapshot_or_layout_changes() -> None:
    status = RuntimeStatusBar()
    snapshot = RuntimeSnapshot(permission="PLAN", phase=RuntimePhase.ERROR, context_percent=99)
    status.set_snapshot(snapshot)
    assert "context 99%" in status.render().plain
    status.set_compact(True)
    assert status.compact_layout is True
    assert "context" not in status.render().plain


@pytest.mark.parametrize(
    ("phase", "expected"),
    [
        (ActivityPhase.CANCELLED, "! Cancelled after 1.0s"),
        (ActivityPhase.FAILED, "✕ Failed after 1.0s"),
    ],
)
def test_activity_terminal_phase_is_stable(phase: ActivityPhase, expected: str) -> None:
    activity = ActivityIndicator()
    activity.start()
    activity.finish(phase, 1.0)
    activity.set_elapsed(3.0)
    assert activity.render().plain == expected


class ShortcutApp(App[None]):
    pass


@pytest.mark.asyncio
@pytest.mark.parametrize("key", ["f1", "escape", "enter"])
async def test_shortcut_help_lists_contextual_shortcuts_and_dismisses(key: str) -> None:
    app = ShortcutApp()
    async with app.run_test() as pilot:
        app.push_screen(ShortcutHelp())
        await pilot.pause()
        panel = app.screen.query_one("#shortcut-panel", Static).render().plain
        for category in ("Composing", "Running", "Tools", "Application"):
            assert category in panel
        await pilot.press(key)
        assert not isinstance(app.screen, ShortcutHelp)
