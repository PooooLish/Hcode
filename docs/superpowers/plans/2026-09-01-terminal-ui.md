# Hcode Professional Compact Terminal UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace Hcode's sparse terminal shell with a professional compact UI that exposes runtime state, improves input and tool feedback, and remains usable at 80 columns without changing core Agent behavior.

**Architecture:** Keep `HcodeApp` as the Agent-event composition root and move presentation-only state into a focused `hcode/tui.py` module. `HcodeApp` translates existing events into header, status, activity, and help component updates; no component may call a provider, execute a tool, decide permission, or mutate conversation state.

**Tech Stack:** Python 3.11.16, Textual 8.2.5, Rich, pytest, pytest-asyncio, existing TCSS theme.

**Spec:** `docs/superpowers/specs/2026-09-01-terminal-ui-design.md`

## Global Constraints

- Preserve Provider, Agent, tool, permission, conversation, session, remote, and streaming protocols.
- Do not add or upgrade dependencies; use the installed Textual 8.2.5 API.
- The persistent header is one row with a bold red `HCODE` wordmark.
- Optimize for 100–140 columns and preserve all critical actions and state at 80 columns.
- Never hide input, errors, permission mode, or runtime phase in compact mode.
- Keep Enter, Shift+Enter, Ctrl+J, Tab, Up/Down, Escape, Shift+Tab, Ctrl+O, and Ctrl+C behavior compatible.
- F1 opens shortcut help and must not destroy typed input.
- Use Chinese and English realistic content in width tests.
- Do not send a provider request during UI verification.
- Store generated SVG review artifacts under `outputs/tui-review/`.
- This project has no independent Git repository. Do not initialize Git or commit unless the user separately approves it; use diff-review checkpoints instead of the commit steps normally required by the planning workflow.

## File Map

- Create `hcode/tui.py`: UI-only enums, snapshots, render helpers, header, status, activity, and shortcut-help components.
- Create `tests/test_tui_components.py`: deterministic component rendering, state, keyboard, and responsive tests.
- Create `tests/test_tui_app.py`: HcodeApp shell wiring and state-transition tests using Textual `run_test()`.
- Create `scripts/capture_tui_review.py`: no-network SVG capture for wide/narrow and idle/working/error states.
- Modify `hcode/app.py`: compose and update the new components, simplify activity rendering, and preserve existing event flow.
- Modify `hcode/styles.tcss`: compact theme roles, layout, focus, overlays, and compact-width classes.
- Modify `hcode/commands/completion.py`: stable completion focus styling and maximum-height behavior only.
- Modify `tests/test_tool_call_block.py`: deterministic tool state vocabulary while retaining expansion behavior.
- Modify `docs/open-source-assessment.md`: record current UI reference research and the conceptual-reference reuse boundary.
- Modify `README.md`: document the visible shell and shortcut summary.
- Modify `project.md`: record status, decisions, progress, next action, blockers, and verification evidence.

---

### Task 1: UI Intake, Open-source Assessment, and Baseline

**Files:**
- Modify: `docs/open-source-assessment.md`
- Modify: `project.md`
- Read: `hcode/app.py`
- Read: `hcode/styles.tcss`
- Read: `hcode/commands/completion.py`
- Read: `tests/test_tool_call_block.py`

**Interfaces:**
- Consumes: approved design at `docs/superpowers/specs/2026-09-01-terminal-ui-design.md`.
- Produces: documented `reference` decision, a fresh regression baseline, and a handoff-safe active task state.

- [ ] **Step 1: Replace the rename-only open-source assessment with a scoped multi-change assessment**

Keep the historical rename conclusion in its own subsection, then add this exact comparison:

```markdown
## Professional compact terminal UI assessment (2026-09-01)

| Source | Version/date checked | License | Useful reference | Reuse boundary |
| --- | --- | --- | --- | --- |
| OpenAI Codex CLI | repository main, checked 2026-09-01 | Apache-2.0 | compact terminal-first coding flow and explicit operational state | concepts only; no code/assets copied |
| Google Gemini CLI | repository/docs main, checked 2026-09-01 | Apache-2.0 | configurable loading phrases, status visibility, accessibility, themes, and alternate-buffer behavior | concepts only; no code/assets copied |
| Textual | installed 8.2.5 plus current official docs | MIT | `App.run_test`, `Pilot`, screen-size testing, reactive components, TCSS, and SVG export | use already-installed public APIs only |

Primary sources:

- https://github.com/openai/codex
- https://github.com/google-gemini/gemini-cli
- https://github.com/google-gemini/gemini-cli/blob/main/docs/reference/configuration.md
- https://textual.textualize.io/guide/testing/
- https://textual.textualize.io/guide/styles/
- https://textual.textualize.io/guide/reactivity/
- https://github.com/Textualize/textual

Decision: `reference`. Hcode keeps its current Python/Textual architecture and
implements the approved design locally. No repository is cloned, no external
source or asset is copied, no package is installed, and no dependency or
license obligation changes.
```

- [ ] **Step 2: Run the fresh pre-change baseline**

Run from `projects/hcode`:

```powershell
$temp = Join-Path ([IO.Path]::GetTempPath()) ('hcode-tui-baseline-' + [guid]::NewGuid().ToString('N'))
python -B -m pytest -q --basetemp $temp
```

Expected: exit 0 with 689 passed and 3 existing skips. If the count differs,
record the actual result and stop to diagnose before changing UI code.

- [ ] **Step 3: Record the active UI task in `project.md`**

Add a decision linking the approved spec and plan. Set the next action to Task
2, state that no provider request is required, and record the exact baseline
command/result. Do not remove historical rename or StreamEnd evidence.

- [ ] **Step 4: Review the documentation-only checkpoint**

Run:

```powershell
rg -n "Professional compact terminal UI|Decision: `reference`|terminal-ui-design|terminal-ui.md" docs/open-source-assessment.md project.md
```

Expected: the assessment, design link, plan link, and project-state entries are
present; no source file has changed in this task.

---

### Task 2: Presentation State and Reusable TUI Components

**Files:**
- Create: `hcode/tui.py`
- Create: `tests/test_tui_components.py`
- Modify: `hcode/styles.tcss`

**Interfaces:**
- Consumes: `PermissionMode` values only as normalized display strings supplied by the app.
- Produces: `RuntimePhase`, `ActivityPhase`, `RuntimeSnapshot`, `WorkspaceHeader.set_context()`, `WorkspaceHeader.set_compact()`, `RuntimeStatusBar.set_snapshot()`, `ActivityIndicator.start()`, `ActivityIndicator.set_elapsed()`, `ActivityIndicator.finish()`, and `ShortcutHelp`.

- [ ] **Step 1: Write failing pure-render and component-state tests**

Create `tests/test_tui_components.py` with these initial cases:

```python
from __future__ import annotations

import pytest
from rich.text import Text
from textual.app import App, ComposeResult

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


def test_unknown_context_is_explicit() -> None:
    snapshot = RuntimeSnapshot(permission="DEFAULT", phase=RuntimePhase.READY)
    assert "context --" in render_status(snapshot, compact=False).plain


def test_activity_uses_deterministic_terminal_states() -> None:
    activity = ActivityIndicator()
    activity.start()
    activity.set_elapsed(2.4)
    assert "Working · 2.4s" in activity.render().plain
    activity.finish(ActivityPhase.COMPLETED, 2.4)
    assert activity.render().plain == "✓ Completed in 2.4s"
```

- [ ] **Step 2: Run the new tests and verify RED**

Run:

```powershell
python -B -m pytest -q tests/test_tui_components.py
```

Expected: collection failure because `hcode.tui` does not exist.

- [ ] **Step 3: Implement the presentation types and deterministic render helpers**

Create `hcode/tui.py` with these public types and signatures:

```python
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.containers import Horizontal
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
    text = Text(snapshot.permission, style="bold red" if snapshot.permission == "BYPASS" else "bold")
    text.append(f"   {snapshot.phase.value}", style={
        RuntimePhase.READY: "green",
        RuntimePhase.WORKING: "yellow",
        RuntimePhase.ERROR: "bold red",
    }[snapshot.phase])
    if snapshot.phase is RuntimePhase.WORKING:
        text.append(f" · {snapshot.elapsed:.1f}s")
    if not compact:
        context = "--" if snapshot.context_percent is None else f"{snapshot.context_percent}%"
        text.append(f"   context {context}", style="dim")
        if snapshot.teammates:
            text.append(f"   {snapshot.teammates} teammate" + ("s" if snapshot.teammates != 1 else ""))
        if snapshot.mcp_state:
            text.append(f"   MCP {snapshot.mcp_state}", style="yellow")
        text.append("   F1 help", style="dim")
    return text
```

Implement `WorkspaceHeader(Horizontal)` with constructor
`__init__(workspace: str = "", model: str = "", **kwargs)`, a read-only
`compact_layout: bool` property, `set_context(workspace: str, model: str) ->
None`, and `set_compact(compact: bool) -> None`. Its `compose()` yields separate
`#hcode-logo`, `#workspace-name`, and `#header-model` `Static` children so TCSS
can keep the model right-aligned. Compact mode hides only workspace and model.
Implement `RuntimeStatusBar(Static)` with
`set_snapshot(snapshot: RuntimeSnapshot) -> None`, a read-only
`compact_layout: bool` property, and `set_compact(compact: bool) -> None`.
Both components rerender immediately.

Implement `ActivityIndicator(Static)` so `start()` renders `○ Working ·
0.0s`, `set_elapsed(seconds)` updates only while working, and
`finish(phase, seconds)` renders exactly one of:

```python
{
    ActivityPhase.COMPLETED: "✓ Completed in {seconds:.1f}s",
    ActivityPhase.CANCELLED: "! Cancelled after {seconds:.1f}s",
    ActivityPhase.FAILED: "✕ Failed after {seconds:.1f}s",
}
```

Implement `ShortcutHelp(ModalScreen[None])` with priority bindings for F1,
Escape, and Enter, each calling `dismiss(None)`. Its composed `Static` lists
the approved composing, running, tools, and application shortcuts.

- [ ] **Step 4: Add component TCSS roles**

Append selectors for `#workspace-header`, `#runtime-status`,
`.activity-indicator`, `ShortcutHelp`, and `#shortcut-panel`. Use a one-row
header/status, subtle `#303030` rules, visible `$accent` focus, and a centered
shortcut panel no wider than 72 columns. Do not style conversation messages as
cards.

- [ ] **Step 5: Run focused tests and make GREEN**

Run:

```powershell
python -B -m pytest -q tests/test_tui_components.py
```

Expected: all component tests pass.

- [ ] **Step 6: Review the Task 2 boundary**

Confirm `hcode/tui.py` imports no provider, Agent, tool registry, conversation,
session, or permission checker module. Review `hcode/styles.tcss` for duplicate
selectors and run `python -B -m py_compile hcode/tui.py`.

---

### Task 3: App Shell, Runtime Status, and Responsive Wiring

**Files:**
- Modify: `hcode/app.py:1-70, 579-712, 960-1055, 1198-1250, 1725-1760, 1884-1920, 2036-2075`
- Modify: `hcode/styles.tcss`
- Create: `tests/test_tui_app.py`

**Interfaces:**
- Consumes: all Task 2 public types and methods.
- Produces: `HcodeApp._runtime_snapshot() -> RuntimeSnapshot`, `HcodeApp._refresh_runtime_status() -> None`, `HcodeApp._set_compact_layout(width: int) -> None`, and the F1 `show_shortcuts` action.

- [ ] **Step 1: Write failing app-shell tests**

Create `tests/test_tui_app.py`. Use a `ProviderConfig` with protocol
`openai-compat`, `https://example.invalid`, model `test-model`, and a literal
test-only key. Patch `HcodeApp._select_provider` in the test harness so no
runtime services start. Add these assertions:

```python
from textual.widgets import Static

from hcode.app import ChatInput, HcodeApp
from hcode.config import ProviderConfig
from hcode.tui import RuntimePhase, RuntimeStatusBar, ShortcutHelp, WorkspaceHeader


def _provider() -> ProviderConfig:
    return ProviderConfig(
        name="test",
        protocol="openai-compat",
        base_url="https://example.invalid",
        model="test-model",
        api_key="test-only-key",
    )


@pytest.mark.asyncio
async def test_shell_uses_compact_header_and_runtime_status(monkeypatch) -> None:
    monkeypatch.setattr(HcodeApp, "_select_provider", lambda self, provider: None)
    app = HcodeApp([_provider()])
    async with app.run_test(size=(120, 36)):
        assert app.query_one("#workspace-header", WorkspaceHeader)
        assert app.query_one("#runtime-status", RuntimeStatusBar)
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
        assert header.query_one("#hcode-logo", Static).render().plain == "HCODE"
        assert "DEFAULT" in status.render().plain
        assert "READY" in status.render().plain


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
async def test_error_phase_persists_after_stream_finishes(monkeypatch) -> None:
    monkeypatch.setattr(HcodeApp, "_select_provider", lambda self, provider: None)
    app = HcodeApp([_provider()])
    async with app.run_test(size=(120, 36)):
        app._streaming = False
        app._runtime_error = True
        app._refresh_runtime_status()
        assert "ERROR" in app.query_one(RuntimeStatusBar).render().plain
```

- [ ] **Step 2: Run app-shell tests and verify RED**

Run:

```powershell
python -B -m pytest -q tests/test_tui_app.py
```

Expected: failures because the new shell is not composed or wired.

- [ ] **Step 3: Replace the persistent banner and status labels**

Import the Task 2 types. Replace `compose()` header and old status children
with:

```python
yield WorkspaceHeader(os.path.basename(os.getcwd()), "", id="workspace-header")
if len(self.providers) > 1:
    with Vertical(id="provider-select"):
        yield Static("Select a Provider", id="select-label")
        yield OptionList(
            *[
                Option(f"{provider.name}  [{provider.model}]", id=provider.name)
                for provider in self.providers
            ],
            id="provider-list",
        )
yield VerticalScroll(id="chat-area")
with Vertical(id="input-area"):
    yield ChatInput(id="chat-input")
    yield RuntimeStatusBar(id="runtime-status")
    yield CompletionPopup()
```

Remove `_make_banner`, `#title-bar`, `#status-bar`, `#mode-label`,
`#teammates-label`, and `#model-label` code. In `_select_provider`, call
`WorkspaceHeader.set_context(os.path.basename(work_dir), provider.model)`.

- [ ] **Step 4: Centralize runtime status calculation**

Implement:

```python
def _runtime_snapshot(self) -> RuntimeSnapshot:
    permission = "DEFAULT"
    context_percent: int | None = None
    if self.agent is not None:
        permission = {
            PermissionMode.DEFAULT: "DEFAULT",
            PermissionMode.ACCEPT_EDITS: "ACCEPT EDITS",
            PermissionMode.PLAN: "PLAN",
            PermissionMode.BYPASS: "BYPASS",
        }.get(self.agent.permission_mode, self.agent.permission_mode.value.upper())
        if self.agent.context_window > 0:
            context_percent = min(
                999,
                round(self.conversation.current_tokens() * 100 / self.agent.context_window),
            )
    phase = (
        RuntimePhase.ERROR
        if self._runtime_error
        else RuntimePhase.WORKING
        if self._streaming
        else RuntimePhase.READY
    )
    return RuntimeSnapshot(
        permission=permission,
        phase=phase,
        context_percent=context_percent,
        teammates=self._active_teammates,
        mcp_state="CONNECTING" if self._mcp_connecting else "",
        elapsed=max(0.0, _time.monotonic() - self._thinking_start) if self._streaming else 0.0,
    )

def _refresh_runtime_status(self) -> None:
    self.query_one(RuntimeStatusBar).set_snapshot(self._runtime_snapshot())
```

Initialize `self._runtime_error = False` and `self._active_teammates = 0`.
Replace `_update_teammates_label(count)` with `_set_active_teammates(count)`,
which stores the nonnegative count and calls `_refresh_runtime_status()`.
Replace every `_update_mode_label()` call with `_refresh_runtime_status()`.
Set `_runtime_error = True` in `_show_error()`; clear it at the beginning of a
new send and after a successful `LoopComplete`. Refresh after
provider selection, mode changes, usage events, compact notifications, MCP
state changes, teammate polling, streaming start, and streaming finish.

- [ ] **Step 5: Wire compact layout and shortcut help**

Add `Binding("f1", "show_shortcuts", "Help", priority=True)`. Implement:

```python
def action_show_shortcuts(self) -> None:
    if isinstance(self.screen, ShortcutHelp):
        self.pop_screen()
    else:
        self.push_screen(ShortcutHelp())

def _set_compact_layout(self, width: int) -> None:
    compact = width < 96
    self.query_one(WorkspaceHeader).set_compact(compact)
    self.query_one(RuntimeStatusBar).set_compact(compact)
    self.screen.set_class(compact, "compact")

def on_resize(self, event: events.Resize) -> None:
    self._set_compact_layout(event.size.width)
```

Call `_set_compact_layout(self.size.width)` after mount. Add `.compact` TCSS
rules that reduce horizontal padding and completion width without hiding
critical status.

- [ ] **Step 6: Run app-shell and component tests**

Run:

```powershell
python -B -m pytest -q tests/test_tui_components.py tests/test_tui_app.py
```

Expected: all tests pass at 80×24 and 120×36.

- [ ] **Step 7: Review the Task 3 event boundary**

Inspect the diff and confirm all Agent-event branches remain in their original
order, Provider and Agent construction are unchanged, and only presentation
updates replaced old labels. Run `tests/test_agent.py`, `tests/test_context.py`,
and `tests/test_context_window.py` as a neighboring regression gate.

---

### Task 4: Deterministic Activity, Tool States, Input, and Completion UX

**Files:**
- Modify: `hcode/app.py:140-285, 374-430, 433-484, 1332-1580, 1725-1760, 2036-2045`
- Modify: `hcode/styles.tcss`
- Modify: `hcode/commands/completion.py`
- Modify: `tests/test_tool_call_block.py`
- Modify: `tests/test_tui_app.py`

**Interfaces:**
- Consumes: `ActivityIndicator` and `ActivityPhase` from Task 2; runtime refresh methods from Task 3.
- Produces: deterministic activity lifecycle and tool vocabulary with unchanged submission, cancellation, completion, and expansion semantics.

- [ ] **Step 1: Write failing activity, input, and tool-copy tests**

Append these expectations:

```python
def test_tool_block_uses_explicit_running_success_and_failure_states() -> None:
    block = ToolCallBlock("ReadFile", {"file_path": "foo.py"})
    assert "○ Running" in block.render().plain
    block.set_result("ok", False, 0.2)
    assert "✓ Done" in block.render().plain
    block.set_result("bad", True, 0.3)
    assert "✕ Failed" in block.render().plain


def test_chat_input_has_operational_placeholder_and_six_line_limit() -> None:
    widget = ChatInput()
    assert "@" in widget.placeholder.plain
    assert "/" in widget.placeholder.plain
```

Add an app test that starts the UI-only activity, advances elapsed time,
finishes it, and asserts only one `ActivityIndicator` remains with the completed
copy. Add cancellation and failure cases asserting `Cancelled` and `Failed`.

- [ ] **Step 2: Run focused tests and verify RED**

Run:

```powershell
python -B -m pytest -q tests/test_tool_call_block.py tests/test_tui_app.py
```

Expected: copy, placeholder, and activity lifecycle assertions fail.

- [ ] **Step 3: Replace random thinking copy with an inline activity component**

Remove `random`, `THINKING_VERBS`, and `_to_past_tense`. Keep the existing
timer lifecycle but make `_tick_spinner()` call
`self._activity_indicator.set_elapsed(elapsed)` and refresh runtime status.

At the start of `_send_message`, mount one `ActivityIndicator` inside the
current `ai_row`, call `start()`, and retain it as
`self._activity_indicator`. On `LoopComplete`, call
`finish(ActivityPhase.COMPLETED, total_time)`. On cancellation call
`finish(ActivityPhase.CANCELLED, elapsed)`. On `ErrorEvent` or `LLMError`, call
`finish(ActivityPhase.FAILED, elapsed)`. `_finish_streaming()` stops timers and
clears only the Python reference; it must not remove a terminal activity line.

- [ ] **Step 4: Normalize tool state vocabulary without changing detail behavior**

Use these exact headers in `ToolCallBlock`:

```python
loading = f"  ○ Running · {self._title}"
success = f"  ✓ Done · {self._title} ({self._elapsed:.1f}s)"
failure = f"  ✕ Failed · {self._title} ({self._elapsed:.1f}s)"
```

Keep successful `EditFile` expanded, errors collapsed, other tools collapsed,
click toggling, `Ctrl+O`, Rich escaping, truncation, and diff coloring exactly
as before. Update `ToolGroupSummary` and `SubAgentBlock` to the same
Running/Done/Failed vocabulary without changing their stored data.

- [ ] **Step 5: Improve input and completion presentation**

In `ChatInput.__init__`, set defaults without overriding caller values:

```python
kwargs.setdefault("placeholder", "输入消息，@ 引用文件，/ 执行命令")
kwargs.setdefault("compact", True)
super().__init__(**kwargs)
```

Set TCSS `#chat-input` max-height to 6, keep soft wrapping, and add a visible
focus rule. The status component supplies idle hints and working hints; do not
insert help copy into the editable text.

In `CompletionPopup.DEFAULT_CSS`, retain maximum height 8, add width 100%, and
use stable accent/reverse selection styling. Do not change display/value
pairing, cursor bounds, click selection, or hide behavior.

- [ ] **Step 6: Make runtime hints state-aware**

Extend `render_status` so the noncompact idle suffix is `Enter send ·
Shift+Enter newline · F1 help`, while working it is `Esc cancel · Enter
interrupts & sends`. Compact mode shows only `Esc cancel` while working and no
idle hint. Add exact tests for all three cases.

- [ ] **Step 7: Run focused and neighboring regressions**

Run:

```powershell
python -B -m pytest -q tests/test_tui_components.py tests/test_tui_app.py tests/test_tool_call_block.py tests/test_commands.py tests/test_clear.py
```

Expected: all tests pass, including existing expansion and command behavior.

- [ ] **Step 8: Review the Task 4 behavior boundary**

Compare `_send_message`, `on_chat_input_submitted`, `action_cancel`, and
`action_handle_ctrl_c` before/after. Confirm the same Agent calls, cancellation
points, event branches, and input submission order remain; only mounted widgets
and presentation copy may differ.

---

### Task 5: Visual Capture, Documentation, Full Verification, and Handoff

**Files:**
- Create: `scripts/capture_tui_review.py`
- Create: `outputs/tui-review/wide-idle.svg`
- Create: `outputs/tui-review/narrow-working.svg`
- Create: `outputs/tui-review/wide-error-bypass.svg`
- Modify: `README.md`
- Modify: `project.md`

**Interfaces:**
- Consumes: completed TUI shell and components from Tasks 2–4.
- Produces: repeatable no-network visual evidence, user-facing shortcut documentation, complete regression evidence, and a resumable project state.

- [ ] **Step 1: Create a no-network SVG capture script**

Implement `scripts/capture_tui_review.py` as an async script that subclasses
the real `HcodeApp` and overrides only `_select_provider()` to update the
header without constructing runtime services. It enters `run_test()` at the requested size,
mounts representative user/assistant/tool/system content, sets the desired UI
state, and writes `app.export_screenshot()` to the named output path.

The script must expose:

```python
import asyncio
from pathlib import Path

from textual.containers import VerticalScroll
from textual.widgets import Static

from hcode.app import HcodeApp
from hcode.config import ProviderConfig
from hcode.tui import (
    ActivityIndicator,
    RuntimePhase,
    RuntimeSnapshot,
    RuntimeStatusBar,
    WorkspaceHeader,
)


OUTPUT = Path(__file__).resolve().parents[1] / "outputs" / "tui-review"


class PreviewApp(HcodeApp):
    def _select_provider(self, provider: ProviderConfig) -> None:
        self._selected_provider = provider
        self.query_one(WorkspaceHeader).set_context(Path.cwd().name, provider.model)


def preview_provider() -> ProviderConfig:
    return ProviderConfig(
        name="preview",
        protocol="openai-compat",
        base_url="https://example.invalid",
        model="deepseek-v4-pro",
        api_key="test-only-key",
    )


async def capture(path: Path, *, size: tuple[int, int], state: str) -> None:
    if state not in {"idle", "working", "error-bypass"}:
        raise ValueError(f"unknown preview state: {state}")
    app = PreviewApp([preview_provider()])
    async with app.run_test(size=size) as pilot:
        chat = app.query_one("#chat-area", VerticalScroll)
        await chat.mount(Static("❯ 请检查当前项目并说明下一步", classes="message user-message"))
        await chat.mount(Static("● 已完成项目结构检查。", classes="message ai-message"))
        status = app.query_one(RuntimeStatusBar)
        if state == "working":
            activity = ActivityIndicator(classes="activity-indicator")
            await chat.mount(activity)
            activity.start()
            activity.set_elapsed(2.4)
            status.set_snapshot(RuntimeSnapshot(
                permission="DEFAULT", phase=RuntimePhase.WORKING, elapsed=2.4,
            ))
        elif state == "error-bypass":
            await chat.mount(Static("ERROR  Provider request failed", classes="message error-message"))
            status.set_snapshot(RuntimeSnapshot(
                permission="BYPASS", phase=RuntimePhase.ERROR, context_percent=12,
            ))
        await pilot.pause()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(app.export_screenshot(), encoding="utf-8")

async def main() -> None:
    await capture(OUTPUT / "wide-idle.svg", size=(120, 36), state="idle")
    await capture(OUTPUT / "narrow-working.svg", size=(80, 24), state="working")
    await capture(OUTPUT / "wide-error-bypass.svg", size=(120, 36), state="error-bypass")


if __name__ == "__main__":
    asyncio.run(main())
```

Reject any state outside `idle`, `working`, and `error-bypass`. Use only
literal fake credentials and `https://example.invalid`; never resolve the real
environment key.

- [ ] **Step 2: Run the capture and inspect all SVGs**

Run:

```powershell
python -B scripts/capture_tui_review.py
```

Inspect all three files. Verify the red bold `HCODE` wordmark, no horizontal
overflow, visible focus, readable Chinese placeholder, deterministic activity,
explicit error/BYPASS labels, and critical 80-column status. If any check
fails, fix the smallest responsible component and rerun its focused test before
recapturing.

- [ ] **Step 3: Update README usage documentation**

Add a `## Terminal UI` section with the 120-column text mockup and these
shortcuts: Enter, Shift+Enter/Ctrl+J, Tab, Up/Down, Escape, Shift+Tab, Ctrl+O,
F1, and Ctrl+C. State that `@` references files and `/` opens commands. Do not
claim a model/provider capability changed.

- [ ] **Step 4: Run syntax, dependency, and focused verification**

Run:

```powershell
python -B -m compileall -q hcode tests scripts/capture_tui_review.py
python -B -m pip check
python -B -m pytest -q tests/test_tui_components.py tests/test_tui_app.py tests/test_tool_call_block.py
```

Expected: all commands exit 0 and `pip check` reports no broken requirements.

- [ ] **Step 5: Run the complete suite after final source changes**

Run:

```powershell
$temp = Join-Path ([IO.Path]::GetTempPath()) ('hcode-tui-final-' + [guid]::NewGuid().ToString('N'))
python -B -m pytest -q --basetemp $temp
```

Expected: exit 0; pass count equals the 689-test baseline plus all new tests,
with the same 3 existing skips. Report the exact count and duration.

- [ ] **Step 6: Run a no-network TUI startup smoke**

Use a child process with a literal test-only provider configuration or the
capture harness. Start the Textual app, wait for mount, assert the header,
input, and runtime status exist, then exit without submitting text. Expected:
exit 0 and zero provider calls.

- [ ] **Step 7: Update `project.md` with final task state**

Record:

- completed design and plan paths;
- source and test files changed;
- focused and complete test results;
- SVG artifact paths and inspected states;
- no dependency changes and no provider request;
- next action as user visual acceptance or separately scoped follow-up;
- blockers and unverified terminal-emulator differences.

Preserve all historical rename, environment, security-analysis, and StreamEnd
evidence.

- [ ] **Step 8: Run workspace handoff health checks**

From the workspace root:

```powershell
python -B capabilities/tools/workspace.py handoff hcode
python -B capabilities/tools/workspace.py doctor hcode
```

Expected: both exit 0; doctor reports `[ok] hcode` and 0 items requiring
review.

- [ ] **Step 9: Perform final diff and secret review**

Review every changed file against the approved spec. Scan only the changed
source, tests, docs, and generated SVG text for credential markers; report
counts, never matched content. Confirm `.hcode/config.yaml`, user environment
variables, and `.local/` were not read or copied by this task.

The completion report must state exact verification commands/results, the
three existing skips, visual states inspected, no paid request, no dependency
change, remaining emulator-specific limitations, and that no Git commit was
created.
