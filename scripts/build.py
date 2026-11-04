#!/usr/bin/env python3
"""Generate static article pages and a search index from Markdown content."""
import html
import json
import re
from pathlib import Path
from urllib.parse import quote

import bleach
import markdown
import yaml

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
OUTPUT = ROOT / "articles"
INDEX = ROOT / "data" / "articles.json"
CATEGORIES = {item["id"]: item["label"] for item in json.loads((ROOT / "data" / "schema.json").read_text(encoding="utf-8"))["categories"]}
ALLOWED_TAGS = set(bleach.sanitizer.ALLOWED_TAGS) | {"p", "h2", "h3", "h4", "pre", "code", "blockquote", "hr", "br", "img", "table", "thead", "tbody", "tr", "th", "td"}
ALLOWED_ATTRS = {"a": ["href", "title"], "img": ["src", "alt", "title"], "th": ["align"], "td": ["align"]}


def parse(path):
    source = path.read_text(encoding="utf-8")
    match = re.match(r"\A---\s*\n(.*?)\n---\s*\n(.*)\Z", source, re.S)
    if not match:
        raise ValueError(f"{path}: missing YAML frontmatter")
    meta = yaml.safe_load(match.group(1))
    if not isinstance(meta, dict):
        raise ValueError(f"{path}: invalid metadata")
    for key in ("title", "category", "author", "year"):
        if not isinstance(meta.get(key), (str, int)) or not str(meta[key]).strip():
            raise ValueError(f"{path}: missing {key}")
    if meta["category"] not in CATEGORIES:
        raise ValueError(f"{path}: unknown category {meta['category']}")
    body = match.group(2).strip()
    if not body:
        raise ValueError(f"{path}: empty article")
    if path.stem == "README":
        raise ValueError("README cannot be an article")
    return meta, body


def render(meta, body, url):
    # Escape inline HTML before Markdown conversion; sanitize generated HTML too.
    rendered = markdown.markdown(html.escape(body), extensions=["extra", "toc"])
    clean = bleach.clean(rendered, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, protocols=["http", "https", "mailto"], strip=True)
    title = html.escape(str(meta["title"]))
    byline = " · ".join(html.escape(str(meta[k])) for k in ("author", "year", "major") if meta.get(k))
    contact = f'<aside class="article-contact"><strong>联系作者</strong><p>{html.escape(str(meta["contact"]))}</p></aside>' if meta.get("contact") else ""
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="{html.escape(str(meta.get('excerpt') or meta['title']), quote=True)}"><title>{title} · UEM Feiyue</title><link rel="stylesheet" href="../assets/css/site.css"><script defer src="../assets/js/site.js"></script></head>
<body><a class="skip-link" href="#main">跳转到正文</a><div class="shell">
<aside class="sidebar" id="sidebar" aria-label="主导航"><a class="brand" href="../"><span class="brand-mark" aria-hidden="true">跃</span><span><strong>UEM Feiyue</strong><small>应急管理大学飞跃手册</small></span></a><nav class="nav" id="category-nav"><a href="../">全部经历</a></nav><div class="sidebar-bottom"><p>把走过的路，留给后来的人。</p><a class="nav-submit" href="../submit.html">分享我的经历 ↗</a></div></aside>
<div class="page"><header class="topbar"><button class="icon-button menu-button" id="menu-toggle" type="button" aria-label="打开导航" aria-controls="sidebar" aria-expanded="false">☰</button><a class="mobile-brand" href="../">UEM Feiyue</a><div class="top-actions"><button class="icon-button" id="theme-toggle" type="button" aria-label="切换明暗主题">◐</button><a class="top-submit" href="../submit.html">投稿 ↗</a></div></header>
<main id="main" class="content"><article class="article-page"><a class="article-back" href="../?category={quote(str(meta['category']))}">← {html.escape(CATEGORIES[meta['category']])}</a><p class="eyebrow">UEM FEIYUE · {html.escape(CATEGORIES[meta['category']])}</p><h1>{title}</h1><p class="article-byline">{byline}</p><div class="article-body">{clean}</div>{contact}</article><footer class="footer"><span>UEM Feiyue · 由同学共同维护</span><a href="https://github.com/UEM-Feiyue/UEM-Feiyue.github.io">GitHub ↗</a></footer></main></div></div><button class="scrim" id="scrim" type="button" aria-label="关闭导航" hidden></button></body></html>"""


def main():
    paths = sorted(CONTENT.rglob("*.md"))
    entries = []
    pages = {}
    for path in paths:
        if path.name == "README.md":
            continue
        meta, body = parse(path)
        slug = path.stem
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", slug):
            raise ValueError(f"{path}: filename must be lowercase ascii slug")
        filename = slug + ".html"
        if filename in pages:
            raise ValueError(f"duplicate article slug: {slug}")
        url = "articles/" + filename
        pages[filename] = render(meta, body, url)
        entries.append({
            "title": str(meta["title"]),
            "category": meta["category"],
            "author": str(meta["author"]),
            "year": str(meta["year"]),
            "major": str(meta.get("major", "")),
            "destination": str(meta.get("destination", "")),
            "excerpt": str(meta.get("excerpt") or re.sub(r"\s+", " ", re.sub(r"[#*_`]", "", body))[:150]),
            "tags": meta.get("tags", []),
            "url": url,
        })
    OUTPUT.mkdir(exist_ok=True)
    for old in OUTPUT.glob("*.html"):
        if old.name not in pages:
            old.unlink()
    for name, page in pages.items():
        (OUTPUT / name).write_text(page, encoding="utf-8")
    INDEX.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Generated {len(entries)} articles")


if __name__ == "__main__":
    main()
