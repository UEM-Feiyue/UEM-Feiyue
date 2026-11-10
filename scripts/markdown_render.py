"""Canonical static-article Markdown policy.

Preview and publication support the same authored Markdown subset and share
.article-body CSS. The browser renders with Marked; this module renders the
static counterpart with Python-Markdown, using the same pre-escape policy.
All user-supplied HTML stays inert.
"""
import re

import bleach
import markdown
from markdown.extensions.toc import slugify_unicode

ALLOWED_TAGS = set(bleach.sanitizer.ALLOWED_TAGS) | {
    "p", "h1", "h2", "h3", "h4", "del", "input", "pre", "code",
    "blockquote", "hr", "br", "img", "table", "thead", "tbody",
    "tr", "th", "td",
}
ALLOWED_ATTRS = {
    "a": ["href", "title"], "img": ["src", "alt", "title"],
    "th": ["align"], "td": ["align"],
    "h1": ["id"], "h2": ["id"], "h3": ["id"],
    "input": ["type", "checked", "disabled"],
}
EXTENSIONS = ["extra", "toc", "sane_lists", "pymdownx.tilde", "pymdownx.tasklist"]


def render_markdown(source):
    """Render supported Markdown while preventing author HTML execution.

    Escape '<' rather than HTML-escaping all Markdown input: Markdown's
    structural '>' must survive for blockquotes, and '&' is processed by the
    parser. Bleach enforces the output allowlist, including safe link schemes.
    """
    safe_source = re.sub(r"<(?=[a-z!/])", "&lt;", source, flags=re.I)
    rendered = markdown.markdown(
        safe_source, extensions=EXTENSIONS,
        extension_configs={"toc": {"slugify": slugify_unicode}},
    )
    return bleach.clean(
        rendered, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS,
        protocols=["http", "https", "mailto"], strip=True,
    )
