"""
HTML rendering for the chat transcript.

Qt's rich-text engine supports only a subset of HTML4/CSS2, so layout is built
from tables (no flexbox, no border-radius). Model output is treated as
untrusted: raw HTML is escaped and only Markdown is rendered.
"""

import html
import re
from dataclasses import dataclass
from typing import Final

import markdown

from styles import Palette


@dataclass(frozen=True)
class ChatMessage:
    """A single transcript entry. `role` is 'user', 'assistant' or 'error'."""

    role: str
    content: str
    meta: str = ""


@dataclass(frozen=True)
class _RoleStyle:
    display_name: str
    avatar_glyph: str
    avatar_color: str


_ROLE_STYLES: Final[dict[str, _RoleStyle]] = {
    "user": _RoleStyle("你", "你", Palette.ACCENT),
    "assistant": _RoleStyle("SmolLM", "S", Palette.ASSISTANT),
    "error": _RoleStyle("系統", "!", Palette.DANGER_STRONG),
}

SUGGESTIONS: Final[list[tuple[str, str]]] = [
    ("解釋概念", "Explain how a transformer language model works, in simple terms."),
    ("撰寫程式", "Write a Python function that checks whether a string is a palindrome, with tests."),
    ("整理重點", "Summarize the main benefits and trade-offs of running LLMs locally."),
    ("發想創意", "Suggest five creative names for a cozy coffee shop and explain each."),
]

STREAMING_CURSOR: Final = "▍"
_CODE_BLOCK_OPEN: Final = re.compile(r"<pre><code[^>]*>")
_TABLE_OPEN: Final = (
    f'<table border="1" cellspacing="0" cellpadding="6" '
    f'style="border-color: {Palette.BORDER}; border-style: solid;">'
)


def _build_markdown() -> markdown.Markdown:
    renderer = markdown.Markdown(extensions=["fenced_code", "tables", "sane_lists", "nl2br"])
    # Disable raw-HTML passthrough so model output cannot inject markup.
    renderer.preprocessors.deregister("html_block")
    renderer.inlinePatterns.deregister("html")
    return renderer


_MARKDOWN: Final = _build_markdown()


def markdown_to_html(text: str) -> str:
    """Render untrusted Markdown into Qt-compatible HTML."""
    _MARKDOWN.reset()
    rendered = _MARKDOWN.convert(text)
    rendered = _CODE_BLOCK_OPEN.sub('<pre><code class="block">', rendered)
    return rendered.replace("<table>", _TABLE_OPEN)


def plain_text_to_html(text: str) -> str:
    """Escape text verbatim, preserving line breaks."""
    return "<p>" + html.escape(text).replace("\n", "<br>") + "</p>"


def _avatar(style: _RoleStyle) -> str:
    return (
        f'<table cellspacing="0" cellpadding="5" width="28" bgcolor="{style.avatar_color}">'
        '<tr><td align="center" style="color: #ffffff; font-size: 12px; font-weight: 600;">'
        f"{html.escape(style.avatar_glyph)}</td></tr></table>"
    )


def render_message(index: int, message: ChatMessage, streaming: bool = False) -> str:
    """Render one transcript row. `index` is used for per-message actions (copy)."""
    style = _ROLE_STYLES.get(message.role, _ROLE_STYLES["assistant"])

    if message.role == "user":
        body = plain_text_to_html(message.content)
    elif message.role == "error":
        body = f'<p class="error">{html.escape(message.content)}</p>'
    elif streaming and not message.content.strip():
        body = '<p class="meta">思考中…</p>'
    else:
        body = markdown_to_html(message.content + (STREAMING_CURSOR if streaming else ""))

    footer = ""
    if message.role == "assistant" and not streaming:
        parts = [html.escape(message.meta)] if message.meta else []
        parts.append(f'<a href="copy:{index}">複製</a>')
        footer = f'<p class="meta">{" &nbsp;·&nbsp; ".join(parts)}</p>'

    return (
        '<table width="100%" cellspacing="0" cellpadding="0" style="margin-top: 20px;">'
        "<tr>"
        f'<td width="44" valign="top">{_avatar(style)}</td>'
        '<td valign="top">'
        f'<p class="role">{html.escape(style.display_name)}</p>'
        f"{body}{footer}"
        "</td></tr></table>"
    )


def render_welcome(model_name: str) -> str:
    """Empty-state screen with clickable prompt suggestions (`prompt:<i>` links)."""
    if model_name:
        subtitle = (
            f"目前模型：<b>{html.escape(model_name)}</b> &nbsp;·&nbsp; "
            "完全在本機執行，資料不會離開你的電腦"
        )
    else:
        subtitle = "請先從左側載入模型。預設模型 SmolLM2 1.7B 只需下載一次，之後即可離線使用。"

    cells = [
        f'<td width="50%" valign="top" bgcolor="{Palette.SURFACE}">'
        f'<a href="prompt:{i}"><b>{html.escape(title)}</b></a><br>'
        f'<span class="meta">{html.escape(prompt)}</span></td>'
        for i, (title, prompt) in enumerate(SUGGESTIONS)
    ]
    rows = "".join(f"<tr>{''.join(cells[i:i + 2])}</tr>" for i in range(0, len(cells), 2))

    return (
        '<table width="100%" cellspacing="0" cellpadding="0" style="margin-top: 72px;">'
        '<tr><td align="center">'
        '<p class="welcome-title">今天想聊些什麼？</p>'
        f'<p class="muted">{subtitle}</p>'
        "</td></tr></table>"
        f'<table width="100%" cellspacing="10" cellpadding="14" style="margin-top: 18px;">{rows}</table>'
    )


def wrap_document(inner_html: str, width_px: int) -> str:
    """Center content in a fixed-width reading column."""
    return (
        "<html><body>"
        f'<table align="center" width="{max(1, int(width_px))}" cellspacing="0" cellpadding="0">'
        f"<tr><td>{inner_html}</td></tr></table>"
        '<p style="margin-bottom: 16px;"></p>'
        "</body></html>"
    )
