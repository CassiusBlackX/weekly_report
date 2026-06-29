"""Server-side HTML sanitisation for rich-text report content.

Defends against stored XSS. The allowed set matches what the TipTap
editor on the frontend can produce (formatting, lists, links, images).
Image src is restricted to our own upload path; any other image is dropped.
"""
import re

import bleach

from .config import settings

_ALLOWED_TAGS = [
    "p", "br", "strong", "em", "u", "s", "code", "pre", "blockquote",
    "h1", "h2", "h3", "h4", "ul", "ol", "li", "a", "img", "hr",
]

_ALLOWED_ATTRS = {
    "a": ["href", "title", "target", "rel"],
    "img": ["src", "alt", "title", "width", "height"],
}

_ALLOWED_PROTOCOLS = ["http", "https", "mailto"]

_IMG_TAG = re.compile(r"<img\b[^>]*>", re.IGNORECASE)
_IMG_SRC = re.compile(r'src="([^"]*)"', re.IGNORECASE)


def _drop_foreign_images(html: str) -> str:
    """Remove <img> tags whose src is not one of our own uploads."""
    upload_prefix = f"{settings.base_path}/api/uploads/"

    def repl(match: re.Match) -> str:
        tag = match.group(0)
        src = _IMG_SRC.search(tag)
        if src and src.group(1).startswith(upload_prefix):
            return tag
        return ""

    return _IMG_TAG.sub(repl, html)


def sanitize_html(html: str) -> str:
    cleaned = bleach.clean(
        html or "",
        tags=_ALLOWED_TAGS,
        attributes=_ALLOWED_ATTRS,
        protocols=_ALLOWED_PROTOCOLS,
        strip=True,
    )
    return _drop_foreign_images(cleaned)
