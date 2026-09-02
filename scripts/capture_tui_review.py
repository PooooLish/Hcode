import asyncio
import os
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
    CSS_PATH = Path(__file__).resolve().parents[1] / "hcode" / "styles.tcss"

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
    no_color = os.environ.pop("NO_COLOR", None)
    try:
        app = PreviewApp([preview_provider()])
    finally:
        if no_color is not None:
            os.environ["NO_COLOR"] = no_color
    async with app.run_test(size=size) as pilot:
        chat = app.query_one("#chat-area", VerticalScroll)
        await chat.mount(
            Static("❯ 请检查当前项目并说明下一步", classes="message user-message")
        )
        await chat.mount(
            Static("● 已完成项目结构检查。", classes="message ai-message")
        )
        await chat.mount(
            Static("✓ Done · Read project.md (0.2s)", classes="tool-block")
        )
        await chat.mount(
            Static("SYSTEM  Review capture uses local test state.", classes="message system-message")
        )
        status = app.query_one(RuntimeStatusBar)
        if state == "working":
            activity = ActivityIndicator(classes="activity-indicator")
            await chat.mount(activity)
            activity.start()
            activity.set_elapsed(2.4)
            status.set_snapshot(
                RuntimeSnapshot(
                    permission="DEFAULT",
                    phase=RuntimePhase.WORKING,
                    elapsed=2.4,
                )
            )
        elif state == "error-bypass":
            await chat.mount(
                Static(
                    "ERROR  Provider request failed",
                    classes="message error-message",
                )
            )
            status.set_snapshot(
                RuntimeSnapshot(
                    permission="BYPASS",
                    phase=RuntimePhase.ERROR,
                    context_percent=12,
                )
            )
        if state != "idle":
            app.query_one("#chat-input").focus()
        await pilot.pause()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(app.export_screenshot(), encoding="utf-8")


async def main() -> None:
    await capture(OUTPUT / "wide-idle.svg", size=(120, 36), state="idle")
    await capture(OUTPUT / "narrow-working.svg", size=(80, 24), state="working")
    await capture(
        OUTPUT / "wide-error-bypass.svg",
        size=(120, 36),
        state="error-bypass",
    )


if __name__ == "__main__":
    asyncio.run(main())
