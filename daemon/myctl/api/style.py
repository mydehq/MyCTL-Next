from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import re


ANSI_RESET = "\x1b[0m"
ANSI_BOLD = "\x1b[1m"
ANSI_16 = {
    "red": "\x1b[31m",
    "green": "\x1b[32m",
    "yellow": "\x1b[33m",
    "blue": "\x1b[34m",
    "cyan": "\x1b[36m",
    "gray": "\x1b[90m",
}
ANSI_256 = {
    "red": "\x1b[38;5;1m",
    "green": "\x1b[38;5;2m",
    "yellow": "\x1b[38;5;3m",
    "blue": "\x1b[38;5;4m",
    "cyan": "\x1b[38;5;6m",
    "gray": "\x1b[38;5;244m",
}
ANSI_TRUECOLOR = {
    "red": "\x1b[38;2;220;38;38m",
    "green": "\x1b[38;2;34;197;94m",
    "yellow": "\x1b[38;2;234;179;8m",
    "blue": "\x1b[38;2;59;130;246m",
    "cyan": "\x1b[38;2;34;211;238m",
    "gray": "\x1b[38;2;148;163;184m",
}
ANSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")


def _get_terminal_value(
    terminal: object | None, key: str, default: object = None
) -> object:
    if terminal is None:
        return default
    if isinstance(terminal, Mapping):
        return terminal.get(key, default)
    return getattr(terminal, key, default)


@dataclass(slots=True)
class StyleHelper:
    terminal: object | None = None
    color_depth: str = "auto"

    def _depth(self) -> str:
        if self.color_depth != "auto":
            return self.color_depth
        if not bool(_get_terminal_value(self.terminal, "is_tty", False)):
            return "none"
        if _get_terminal_value(self.terminal, "no_color", False):
            return "none"
        depth = str(_get_terminal_value(self.terminal, "color_depth", "16") or "16")
        if depth not in {"none", "16", "256", "truecolor"}:
            return "16"
        return depth

    def _wrap(self, text: str, color: str | None = None, bold: bool = False) -> str:
        if self._depth() == "none":
            return text
        prefix = ""
        if bold:
            prefix += ANSI_BOLD
        depth = self._depth()
        if color:
            if depth == "truecolor":
                prefix += ANSI_TRUECOLOR[color]
            elif depth == "256":
                prefix += ANSI_256[color]
            else:
                prefix += ANSI_16[color]
        return f"{prefix}{text}{ANSI_RESET}"

    def bold(self, text: str) -> str:
        return self._wrap(text, bold=True)

    def success(self, text: str) -> str:
        return self._wrap(text, color="green")

    def warning(self, text: str) -> str:
        return self._wrap(text, color="yellow")

    def error(self, text: str) -> str:
        return self._wrap(text, color="red")

    def info(self, text: str) -> str:
        return self._wrap(text, color="blue")

    def strip_ansi(self, text: str) -> str:
        return ANSI_RE.sub("", text)

    def table(
        self,
        rows: Sequence[Sequence[object]],
        headers: Sequence[object] | None = None,
    ) -> str:
        normalized_rows: list[list[str]] = [[str(cell) for cell in row] for row in rows]
        normalized_headers: list[str] | None = (
            [str(cell) for cell in headers] if headers else None
        )
        all_rows: list[list[str]] = list(normalized_rows)
        if normalized_headers:
            all_rows = [normalized_headers] + all_rows
        if not all_rows:
            return ""
        column_count = max(len(row) for row in all_rows)
        widths = [0] * column_count
        for row in all_rows:
            for index in range(column_count):
                cell = row[index] if index < len(row) else ""
                widths[index] = max(widths[index], len(self.strip_ansi(cell)))

        def format_row(row: Sequence[str]) -> str:
            cells = []
            for index in range(column_count):
                cell = row[index] if index < len(row) else ""
                padding = widths[index] - len(self.strip_ansi(cell))
                cells.append(f" {cell}{' ' * padding} ")
            return "|" + "|".join(cells) + "|"

        lines: list[str] = []
        if normalized_headers:
            lines.append(format_row(normalized_headers))
            lines.append("|" + "|".join("-" * (width + 2) for width in widths) + "|")
            for row in normalized_rows:
                lines.append(format_row(row))
        else:
            for row in normalized_rows:
                lines.append(format_row(row))
        return "\n".join(lines)


def make_style(
    terminal: object | None = None, color_depth: str = "auto"
) -> StyleHelper:
    return StyleHelper(terminal=terminal, color_depth=color_depth)
