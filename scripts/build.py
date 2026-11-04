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
SCHEMA = json.loads((ROOT / "data" / "schema.json").read_text(encoding="utf-8"))
CATEGORIES = {item["id"]: item["label"] for item in SCHEMA["categories"]}
YEAR_SUFFIX = next(field.get("suffix", "") for field in SCHEMA["fields"] if field["name"] == "year")


def display_year(value):
    value = str(value).strip()
    return value + (" " + YEAR_SUFFIX if re.fullmatch(r"[0-9]{4}", value) else "")
ALLOWED_TAGS = set(bleach.sanitizer.ALLOWED_TAGS) | {"p", "h1", "h2", "h3", "h4", "del", "input", "pre", "code", "blockquote", "hr", "br", "img", "table", "thead", "tbody", "tr", "th", "td"}
ALLOWED_ATTRS = {"a": ["href", "title"], "img": ["src", "alt", "title"], "th": ["align"], "td": ["align"], "h1": ["id"], "h2": ["id"], "h3": ["id"], "input": ["type", "checked", "disabled"]}


def parse(path):
    source = path.read_text(encoding="utf-8")
    match = re.match(r"\A---\s*\n(.*?)\n---\s*\n(.*)\Z", source, re.S)
    if not match:
        raise ValueError(f"{path}: missing YAML frontmatter")
    meta = yaml.safe_load(match.group(1))
    if not isinstance(meta, dict):
        raise ValueError(f"{path}: invalid metadata")
    for key in ("category", "author", "year"):
        if not isinstance(meta.get(key), (str, int)) or not str(meta[key]).strip():
            raise ValueError(f"{path}: missing {key}")
    if not re.fullmatch(r"[0-9]{4}", str(meta["year"]).strip()):
        raise ValueError(f"{path}: year must be a four-digit graduation year")
    meta["year"] = str(meta["year"]).strip()
    if meta["category"] not in CATEGORIES:
        raise ValueError(f"{path}: unknown category {meta['category']}")
    body = match.group(2).strip()
    if not body:
        raise ValueError(f"{path}: empty article")
    if path.stem == "README":
        raise ValueError("README cannot be an article")
    return meta, body


def display_title(meta):
    """One title convention shared by archive cards and article pages."""
    parts = [str(meta["author"]).strip(), str(meta.get("destination") or "").strip()]
    title = " — ".join(part for part in parts if part)
    program = str(meta.get("program") or "").strip()
    return title + (" · " + program if program else "")


def render(meta, body, url):
    # Escape inline HTML before Markdown conversion; sanitize generated HTML too.
    rendered = markdown.markdown(html.escape(body), extensions=["extra", "toc", "sane_lists", "pymdownx.tilde", "pymdownx.tasklist"])
    clean = bleach.clean(rendered, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, protocols=["http", "https", "mailto"], strip=True)
    title = html.escape(display_title(meta))
    byline = " · ".join(html.escape(display_year(meta[k]) if k == "year" else str(meta[k])) for k in ("author", "year", "major") if meta.get(k))
    headings = re.findall(r'<h([23]) id="([^"]+)">(.+?)</h[23]>', clean)
    toc = '<nav class="article-toc" aria-label="文章目录"><strong>本页目录</strong><ul>' + ''.join(f'<li class="toc-depth-{level}"><a href="#{html.escape(anchor, quote=True)}">{text}</a></li>' for level, anchor, text in headings) + '</ul></nav>' if len(headings) >= 2 else ''
    demo = '<span class="demo-badge">演示内容 · 非真实投稿</span>' if meta.get('demo') is True else ''
    contact = f'<aside class="article-contact"><strong>联系作者</strong><p>{html.escape(str(meta["contact"]))}</p></aside>' if meta.get("contact") else ""
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="{html.escape(str(meta.get('excerpt') or display_title(meta)), quote=True)}"><title>{title} · UEM Feiyue</title><link rel="icon" href="../assets/icons/favicon.svg" type="image/svg+xml"><script src="../assets/js/theme-init.js"></script><link rel="preload" as="image" href="../assets/images/anguo-garden.jpg"><link rel="stylesheet" href="../assets/css/site.css?v=20261104f"><script defer src="../assets/js/site.js?v=20261104f"></script></head>
<body><a class="skip-link" href="#main">跳转到正文</a><div class="shell">
<aside class="sidebar" id="sidebar" aria-label="侧边导航"><a class="brand" href="../"><img class="brand-logo" src="../assets/images/favicon-横版.png" alt="UEM Feiyue · 应急管理大学飞跃手册" width="1226" height="285"></a><nav class="nav" id="category-nav" aria-label="主导航"><a href="../" data-view="home">首页</a><a href="../?view=all" data-category="all">全部经历</a><a href="../submit.html" class="nav-contribute">投稿分享 <span class="link-arrow" aria-hidden="true"></span></a></nav><div class="sidebar-bottom"><button class="sidebar-theme" id="theme-toggle-mobile" type="button" aria-label="切换明暗主题">◐ <span>切换明暗主题</span></button></div></aside>
<div class="page"><header class="topbar"><button class="icon-button menu-button" id="menu-toggle" type="button" aria-label="打开导航" aria-controls="sidebar" aria-expanded="false">☰</button><a class="mobile-brand" href="../"><img class="mobile-brand-logo" src="../assets/images/favicon-横版.png" alt="UEM Feiyue · 应急管理大学飞跃手册" width="1226" height="285"></a><div class="top-actions"><button class="icon-button" id="theme-toggle" type="button" aria-label="切换明暗主题">◐</button></div></header>
<main id="main" class="content"><article class="article-page"><a class="article-back" href="../?category={quote(str(meta['category']))}"><span class="link-arrow link-arrow-left" aria-hidden="true"></span> 返回{html.escape(CATEGORIES[meta['category']])}</a><h1>{title}</h1>{demo}<p class="article-byline">{byline}</p>{toc}<div class="article-body">{clean}</div>{contact}</article></main><footer class="site-footer" data-site-footer aria-label="网站页脚"><div class="footer-inner"><p>UEM Feiyue · 由同学共同维护</p></div></footer></div></div></body></html>"""


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
            "demo": meta.get("demo") is True,
            "title": display_title(meta),
            "category": meta["category"],
            "author": str(meta["author"]),
            "year": str(meta["year"]),
            "major": str(meta.get("major", "")),
            "program": str(meta.get("program", "")),
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
