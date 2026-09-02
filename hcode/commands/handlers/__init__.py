
from __future__ import annotations

from hcode.commands.handlers.clear import CLEAR_COMMAND
from hcode.commands.handlers.compact import COMPACT_COMMAND
from hcode.commands.handlers.help import HELP_COMMAND
from hcode.commands.handlers.mcp import MCP_COMMAND
from hcode.commands.handlers.memory import MEMORY_COMMAND
from hcode.commands.handlers.plan import PLAN_COMMAND
from hcode.commands.handlers.sandbox import SANDBOX_COMMAND
from hcode.commands.handlers.session import SESSION_COMMAND
from hcode.commands.handlers.skill import SKILL_COMMAND
from hcode.commands.handlers.rewind import REWIND_COMMAND
from hcode.commands.handlers.status import STATUS_COMMAND
from hcode.commands.registry import CommandRegistry


ALL_COMMANDS = [
    HELP_COMMAND,
    COMPACT_COMMAND,
    CLEAR_COMMAND,
    PLAN_COMMAND,
    SESSION_COMMAND,
    MCP_COMMAND,
    MEMORY_COMMAND,
    SANDBOX_COMMAND,
    REWIND_COMMAND,
    STATUS_COMMAND,
    SKILL_COMMAND,
]


def register_all_commands(registry: CommandRegistry) -> None:
    for cmd in ALL_COMMANDS:
        registry.register_sync(cmd)

