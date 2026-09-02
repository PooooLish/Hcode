# Hcode Professional Compact Terminal UI Design

Date: 2026-09-01
Status: Approved on 2026-09-01

## Objective

Improve Hcode's daily terminal experience without changing the Agent,
provider, tool, permission, conversation, or session protocols. The interface
should feel like a professional coding tool: compact, calm, easy to scan, and
explicit about current state and available actions.

The primary layout target is a 100–140 column Windows Terminal. An 80-column
terminal remains fully usable by hiding low-priority metadata and shortening
hints; input, errors, permission mode, and runtime state must never be hidden.

## Scope

- Replace the permanent three-line banner with a compact workspace header.
- Improve visual hierarchy for user, assistant, tool, system, and error output.
- Make idle, working, completed, cancelled, and failed states explicit.
- Improve the input prompt, contextual hints, completion popups, and shortcut
  discoverability.
- Add a compact runtime status bar and an in-app shortcut reference.
- Add responsive behavior for wide and narrow terminal sizes.
- Add focused Textual component and interaction tests plus visual SVG checks.

## Non-goals

- No changes to model requests, streaming protocols, Agent control flow, tool
  execution, permission decisions, session persistence, or remote mode.
- No dashboard, sidebar, tabs, task-management surface, or multi-pane layout.
- No new third-party dependency.
- No paid provider request is needed for verification.
- No broad refactor of `hcode/app.py` beyond extracting the UI components
  required by this design.

## Visual Direction

Hcode uses a professional, compact, operational visual language. It avoids
card-heavy layouts, decorative borders, gradients, and persistent character
art. Whitespace, indentation, weight, and a small semantic palette establish
hierarchy.

The only strong brand element is a bold red `HCODE` wordmark in the top-left.
Red is otherwise reserved for errors and dangerous permission states, so the
wordmark is spatially isolated in the header and never used as a status icon.
The workspace name is muted beside it, and the active model is right-aligned.

Example at normal width:

```text
 HCODE  hcode                                  deepseek-v4-pro
────────────────────────────────────────────────────────────
 conversation and tool activity
 ...
────────────────────────────────────────────────────────────
 ❯ 输入消息，@ 引用文件，/ 执行命令
 DEFAULT   READY   context 12%                  F1 help
```

At narrow width, workspace, model, teammate count, and help text are hidden in
that order. The red `HCODE` wordmark, permission mode, runtime phase, input,
and errors remain visible.

## Layout

### Workspace header

The header is one row plus a subtle bottom rule. It contains:

- left: bold red `HCODE` wordmark;
- next: muted basename of the current workspace when space permits;
- right: muted active model when space permits.

The existing three-line cat banner is removed from the persistent layout. The
provider-selection screen reuses the same header.

### Conversation area

The conversation remains a single vertically scrolling reading flow. It does
not use bubbles or boxed cards.

- User messages start with a bold `❯` accent marker.
- Assistant messages start with a `●` accent marker.
- System notices are muted, concise, and prefixed with a textual state where
  useful.
- Errors use both an `ERROR` label/icon and an error color; color is never the
  sole signal.
- Consecutive low-value read/search tool calls may continue to collapse into a
  group summary.

### Input and runtime status

The input area is docked at the bottom and grows from one to six lines. Its
idle placeholder is:

```text
输入消息，@ 引用文件，/ 执行命令
```

The hint row changes with state. Idle hints expose Enter to send,
Shift+Enter to insert a newline, and F1 for help. While working, the status
shows elapsed time and `Esc cancel`, and explicitly states that Enter
interrupts the current response before sending the new message. Existing
submission behavior is preserved.

The runtime status row displays, in priority order:

1. permission mode (`DEFAULT`, `ACCEPT EDITS`, `PLAN`, or `BYPASS`);
2. runtime phase (`READY`, `WORKING`, or `ERROR`);
3. context usage when it can be computed accurately, otherwise `context --`;
4. active teammate count when nonzero;
5. MCP connecting or degraded state when relevant;
6. `F1 help` when space permits.

Dangerous modes such as `BYPASS` use warning text and color continuously.

## Message and Activity States

Thinking and activity are rendered inside the active assistant response rather
than as an unrelated widget at the bottom of the chat. The live activity line
uses one of these explicit states:

- `○ Working · 2.4s`
- `○ Running ReadFile…`
- `✓ Completed in 2.4s`
- `! Cancelled after 2.4s`
- `✕ Failed after 2.4s`

The playful random thinking verbs are removed from the primary state display
because they reduce predictability and scanability. A single activity line is
updated in place and becomes a compact completion line at the end.

Tool calls use the same state vocabulary:

- `○ Running` while active;
- `✓ Done` on success;
- `✕ Failed` on failure.

Tool details remain collapsed by default. Successful `EditFile` diffs remain
expanded because they are the highest-value review output. Mouse click and
`Ctrl+O` retain their existing expand/collapse behavior.

## Keyboard and Completion Behavior

Existing bindings remain compatible:

- Enter sends;
- Shift+Enter or Ctrl+J inserts a newline;
- Tab completes commands or inserts a tab where applicable;
- Up/Down navigate completion choices or input history;
- Escape dismisses a popup or cancels active work;
- Shift+Tab cycles permission mode;
- Ctrl+O toggles tool details;
- Ctrl+C retains the current staged cancel/quit behavior.

F1 opens a compact shortcut-help overlay. The overlay lists shortcuts by
context: composing, running, tools, and application. It closes with F1,
Escape, or Enter. Slash-command and `@file` completion popups display stable
selection focus, fit within the available terminal height, and do not obscure
the runtime status row.

## Component Boundaries

`HcodeApp` remains the composition root and Agent event dispatcher. A focused
TUI module will contain reusable presentation components:

- `WorkspaceHeader`: renders the wordmark, workspace, and model and applies
  compact visibility rules;
- `RuntimeStatusBar`: renders permission mode, runtime phase, context usage,
  teammate count, MCP state, and contextual hints;
- `ActivityIndicator`: owns the live-to-terminal activity presentation;
- `ShortcutHelp`: owns the F1 overlay and its keyboard dismissal behavior.

`ChatInput`, `ToolCallBlock`, and the existing stream-rendering branch receive
small local changes to use these components. They do not own Agent state.

The application updates the components through explicit presentation methods
or a small UI-only state value. Agent events remain the source of truth:

```text
Agent event -> HcodeApp event branch -> UI-only state/component update
```

No UI component calls the provider, mutates the conversation, executes a tool,
or decides permission.

Responsive behavior is driven by the Textual screen width. The application
toggles a compact CSS class below the selected breakpoint rather than
duplicating the component tree.

## Styling and Accessibility

`styles.tcss` defines consistent semantic roles for brand, accent, muted text,
success, warning, error, borders, and focus. Purple remains the interaction
accent. Green, amber, and red indicate success, warning, and error/danger, with
icons and text providing redundant meaning.

Every focusable element has a visible focus treatment. Long workspace names,
model names, tool commands, and completion labels truncate without pushing
required controls off-screen. The design is checked with realistic Chinese
and English content because terminal character widths differ.

## Error and Edge-state Behavior

- Provider authentication errors remain visible even before a chat starts.
- Empty model output resolves to a completion state rather than leaving a
  spinner active.
- Cancellation always clears `WORKING` and restores input focus.
- An unavailable context estimate renders `context --`, never a guessed value.
- Resize events must not clear input text, reset completion selection, or move
  conversation position unexpectedly.
- If rich glyphs are unavailable, the textual state labels still communicate
  meaning.

## Verification

Implementation follows test-driven development and uses the already-installed
Textual 8.2.5 test API.

Focused tests cover:

- header content and compact visibility;
- every permission/runtime status combination, including `BYPASS`;
- context available and unavailable states;
- input placeholder, growth limit, and idle/working hints;
- activity transitions through working, completed, cancelled, and failed;
- tool success/failure/collapse behavior;
- F1 help focus and dismissal;
- resize behavior at `80×24` and `120×36`;
- existing keyboard and completion behavior.

Textual `App.run_test()` exercises both terminal sizes. SVG screenshots are
exported for human review of hierarchy, truncation, focus, idle, working,
error, and dangerous-mode states. Verification also includes a no-network TUI
startup smoke test and the complete pytest suite. No model request is sent.

## Acceptance Criteria

- The persistent header occupies one row and visibly contains a bold red
  `HCODE` wordmark.
- Primary chat and input remain usable at 80 columns without horizontal
  overflow or hidden critical state.
- Runtime and dangerous permission states are explicit in both text and color.
- The input area communicates available actions in idle and working states.
- Activity and tool states use consistent, deterministic language.
- F1 provides discoverable shortcut help without disrupting typed input.
- Provider, Agent, tool, permission, conversation, and session behavior is
  unchanged.
- No new dependency is added.
- Focused UI tests and the complete project suite pass.

## Implementation Prerequisites

Before implementation, update `docs/open-source-assessment.md` for this UI
work using read-only research of maintained terminal Agent interfaces and
official Textual documentation. The reuse decision remains conceptual
reference only: do not copy external code or assets. Dependency installation,
Git initialization, commits, and publishing remain outside this task unless
separately approved.
