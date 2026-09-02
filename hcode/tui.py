from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.screen import ModalScreen
from textual.widgets import Static


class RuntimePhase(str, Enum):
    READY = "READY"
    WORKING = "WORKING"
    ERROR = "ERROR"


class ActivityPhase(str, Enum):
    WORKING = "working"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


@dataclass(frozen=True)
class RuntimeSnapshot:
    permission: str = "DEFAULT"
    phase: RuntimePhase = RuntimePhase.READY
    context_percent: int | None = None
    teammates: int = 0
    mcp_state: str = ""
    elapsed: float = 0.0


def render_brand() -> Text:
    return Text("HCODE", style="bold red")


def render_status(snapshot: RuntimeSnapshot, *, compact: bool) -> Text:
    text = Text()
    text.append(
        snapshot.permission,
        style="bold red" if snapshot.permission == "BYPASS" else "bold",
    )
    text.append(
        f"   {snapshot.phase.value}",
        style={
            RuntimePhase.READY: "green",
            RuntimePhase.WORKING: "yellow",
            RuntimePhase.ERROR: "bold red",
        }[snapshot.phase],
    )
    if snapshot.phase is RuntimePhase.WORKING:
        text.append(f" · {snapshot.elapsed:.1f}s")
    if not compact:
        context = "--" if snapshot.context_percent is None else f"{snapshot.context_percent}%"
        text.append(f"   context {context}", style="#a0a0a0")
        if snapshot.teammates:
            suffix = "s" if snapshot.teammates != 1 else ""
            text.append(f"   {snapshot.teammates} teammate{suffix}")
        if snapshot.mcp_state:
            text.append(f"   MCP {snapshot.mcp_state}", style="yellow")
    if snapshot.phase is RuntimePhase.WORKING:
        working_hint = (
            "   Esc cancel"
            if compact
            else "   Esc cancel · Enter interrupts & sends"
        )
        text.append(working_hint, style="dim")
    elif not compact:
        text.append(
            "   Enter send · Shift+Enter newline · F1 help",
            style="dim",
        )
    return text


class WorkspaceHeader(Horizontal):
    """Compact workspace identity with independently styled header regions."""

    def __init__(self, workspace: str = "", model: str = "", **kwargs: Any) -> None:
        kwargs.setdefault("id", "workspace-header")
        super().__init__(**kwargs)
        self._workspace = workspace
        self._model = model
        self._compact_layout = False

    @property
    def compact_layout(self) -> bool:
        return self._compact_layout

    def compose(self) -> ComposeResult:
        yield Static(render_brand(), id="hcode-logo")
        yield Static(self._workspace, id="workspace-name")
        yield Static(self._model, id="header-model")

    def on_mount(self) -> None:
        self._rerender()

    def set_context(self, workspace: str, model: str) -> None:
        self._workspace = workspace
        self._model = model
        self._rerender()

    def set_compact(self, compact: bool) -> None:
        self._compact_layout = compact
        self._rerender()

    def _rerender(self) -> None:
        try:
            self.query_one("#workspace-name", Static).update(self._workspace)
            self.query_one("#header-model", Static).update(self._model)
            self.query_one("#workspace-name", Static).display = not self._compact_layout
            self.query_one("#header-model", Static).display = not self._compact_layout
        except Exception:
            # Before mounting, compose() reads the stored presentation state.
            pass
        self.refresh()


class RuntimeStatusBar(Static):
    """One-line runtime summary controlled exclusively through a snapshot."""

    def __init__(self, **kwargs: Any) -> None:
        kwargs.setdefault("id", "runtime-status")
        self._snapshot = RuntimeSnapshot()
        self._compact_layout = False
        super().__init__("", **kwargs)

    @property
    def compact_layout(self) -> bool:
        return self._compact_layout

    def set_snapshot(self, snapshot: RuntimeSnapshot) -> None:
        self._snapshot = snapshot
        self.refresh()

    def set_compact(self, compact: bool) -> None:
        self._compact_layout = compact
        self.refresh()

    def render(self) -> Text:
        return render_status(self._snapshot, compact=self._compact_layout)


class ActivityIndicator(Static):
    """A deterministic activity line with a working and three terminal states."""

    def __init__(self, **kwargs: Any) -> None:
        classes = str(kwargs.pop("classes", "")).strip()
        kwargs["classes"] = " ".join(filter(None, (classes, "activity-indicator")))
        super().__init__("", **kwargs)
        self._phase: ActivityPhase | None = None
        self._elapsed = 0.0

    def start(self) -> None:
        self._phase = ActivityPhase.WORKING
        self._elapsed = 0.0
        self.refresh()

    def set_elapsed(self, seconds: float) -> None:
        if self._phase is ActivityPhase.WORKING:
            self._elapsed = seconds
            self.refresh()

    def finish(self, phase: ActivityPhase, seconds: float) -> None:
        if phase is ActivityPhase.WORKING:
            raise ValueError("finish() requires a terminal activity phase")
        self._phase = phase
        self._elapsed = seconds
        self.refresh()

    def render(self) -> Text:
        if self._phase is ActivityPhase.WORKING:
            return Text(f"○ Working · {self._elapsed:.1f}s")
        terminal = {
            ActivityPhase.COMPLETED: f"✓ Completed in {self._elapsed:.1f}s",
            ActivityPhase.CANCELLED: f"! Cancelled after {self._elapsed:.1f}s",
            ActivityPhase.FAILED: f"✕ Failed after {self._elapsed:.1f}s",
        }
        return Text(terminal.get(self._phase, ""))


class ShortcutHelp(ModalScreen[None]):
    """Contextual keyboard reference that can be dismissed without side effects."""

    BINDINGS = [
        Binding("f1", "close_help", "Close", priority=True),
        Binding("escape", "close_help", "Close", priority=True),
        Binding("enter", "close_help", "Close", priority=True),
    ]

    def compose(self) -> ComposeResult:
        yield Static(
            "[bold]Keyboard shortcuts[/bold]\n\n"
            "[bold]Composing[/bold]\n"
            "  Enter              Send\n"
            "  Shift+Enter / Ctrl+J  New line\n"
            "  Tab                Complete command or file\n"
            "  Up / Down          History or completion selection\n\n"
            "[bold]Running[/bold]\n"
            "  Esc                Cancel current work\n"
            "  Enter              Interrupt, then send the new message\n\n"
            "[bold]Tools[/bold]\n"
            "  Ctrl+O             Toggle tool details\n\n"
            "[bold]Application[/bold]\n"
            "  Shift+Tab          Cycle permission mode\n"
            "  Ctrl+C             Cancel or quit\n"
            "  F1 / Esc / Enter   Close this help",
            id="shortcut-panel",
        )

    def action_close_help(self) -> None:
        self.dismiss(None)
