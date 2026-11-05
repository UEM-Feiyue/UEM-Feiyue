#!/usr/bin/env python3
"""Generate static article pages and a search index from Markdown content."""
import html
import json
import re
from pathlib import Path
from urllib.parse import quote

import bleach
import markdown
from markdown.extensions.toc import slugify_unicode
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
    body = match.group(2).strip()
    if meta.get("category") not in CATEGORIES:
        raise ValueError(f"{path}: unknown category {meta.get('category')}")
    values = dict(meta, body=body)
    for field in SCHEMA["fields"]:
        name = field["name"]
        value = values.get(name, "")
        if not isinstance(value, (str, int)) or isinstance(value, bool):
            raise ValueError(f"{path}: invalid {name}")
        value = str(value).strip()
        if field.get("required") and not value:
            raise ValueError(f"{path}: missing {name}")
        if field.get("maxLength") and len(value) > field["maxLength"]:
            raise ValueError(f"{path}: {name} exceeds maximum length")
        if value and field.get("pattern") and not re.fullmatch(field["pattern"], value):
            raise ValueError(f"{path}: invalid {name}")
    meta["year"] = str(meta["year"]).strip()
    if path.stem == "README":
        raise ValueError("README cannot be an article")
    return meta, body


def display_title(meta):
    """One title convention shared by archive cards and article pages."""
    parts = [str(meta["author"]).strip(), str(meta.get("destination") or "").strip()]
    title = " — ".join(part for part in parts if part)
    program = str(meta.get("program") or "").strip()
    return title + (" · " + program if program else "")


def shared_chrome(source, page, prefix="./", category=None):
    """Reuse the homepage's navigation/header/footer without a separate UI framework."""
    home = (ROOT / "index.html").read_text(encoding="utf-8")
    sidebar = re.search(r'<aside class="sidebar".*?</aside>', home, re.S)[0]
    links = [f'<a href="{prefix}" data-view="home"' + (' aria-current="page"' if page == "index" else '') + '>首页</a>',
             f'<a href="{prefix}?view=all" data-category="all">全部经历</a>']
    for item in SCHEMA["categories"]:
        selected = ' aria-current="page"' if category == item["id"] else ''
        links.append(f'<a href="{prefix}?category={quote(item["id"])}" data-category="{html.escape(item["id"], quote=True)}" data-category-label="{html.escape(item["label"], quote=True)}" data-category-description="{html.escape(item["description"], quote=True)}"{selected}>{html.escape(item["label"])}</a>')
    links.append(f'<a href="{prefix}submit.html" class="nav-contribute"' + (' aria-current="page"' if page == "submit" else '') + '>投稿分享 <span class="link-arrow" aria-hidden="true"></span></a>')
    sidebar = re.sub(r'(<nav class="nav"[^>]*>).*?(</nav>)', lambda m: m[1] + ''.join(links) + m[2], sidebar, flags=re.S)
    header = re.search(r'<header class="topbar">.*?</header>', home, re.S)[0]
    footer = re.search(r'<footer class="site-footer".*?</footer>', home, re.S)[0]
    footer_links = f'<a href="{prefix}?view=all">全部经历</a>' + ''.join(
        f'<a href="{prefix}?category={quote(item["id"])}">{html.escape(item["label"])}</a>' for item in SCHEMA["categories"])
    footer_links += f'<a href="{prefix}submit.html">投稿分享</a>'
    footer = re.sub(r'(<nav class="footer-links"[^>]*>).*?(</nav>)', lambda m: m[1] + footer_links + m[2], footer, flags=re.S)
    for pattern, fragment in ((r'<aside class="sidebar".*?</aside>', sidebar),
                              (r'<header class="topbar">.*?</header>', header),
                              (r'<footer class="site-footer".*?</footer>', footer)):
        source = re.sub(pattern, lambda _: fragment, source, count=1, flags=re.S)
    source = re.sub(r'((?:src|href)=")(?:(?:\./)?assets/)', lambda m: m[1] + prefix + 'assets/', source)
    if prefix != "./":
        source = source.replace('href="./"', f'href="{prefix}"')
    if page != "index":
        source = source.replace('class="page is-home"', 'class="page"')
        source = re.sub(r'<link rel="preload" as="image"[^>]*>', '', source)
    return source


def render(meta, body, url):
    # Escape inline HTML before Markdown conversion; sanitize generated HTML too.
    rendered = markdown.markdown(html.escape(body), extensions=["extra", "toc", "sane_lists", "pymdownx.tilde", "pymdownx.tasklist"], extension_configs={"toc": {"slugify": slugify_unicode}})
    clean = bleach.clean(rendered, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, protocols=["http", "https", "mailto"], strip=True)
    byline = " · ".join(html.escape(display_year(meta[k]) if k == "year" else str(meta[k])) for k in ("author", "year", "major") if meta.get(k))
    headings = re.findall(r'<h([23]) id="([^"]+)">(.+?)</h[23]>', clean)
    toc = '<nav class="article-toc" aria-label="文章目录"><strong>本页目录</strong><ul>' + ''.join(f'<li class="toc-depth-{level}"><a href="#{html.escape(anchor, quote=True)}">{text}</a></li>' for level, anchor, text in headings) + '</ul></nav>' if len(headings) >= 2 else ''
    demo = '<span class="demo-badge">演示</span>' if meta.get('demo') is True else ''
    contact = f'<aside class="article-contact"><strong>联系作者</strong><p>{html.escape(str(meta["contact"]))}</p></aside>' if meta.get("contact") else ""
    source = shared_chrome((ROOT / "index.html").read_text(encoding="utf-8"), "article", "../", meta["category"])
    title = html.escape(display_title(meta))
    source = re.sub(r'<title>.*?</title>', lambda _: f'<title>{title} · UEM Feiyue</title>', source, count=1, flags=re.S)
    description = html.escape(str(meta.get("excerpt") or display_title(meta)), quote=True)
    source = re.sub(r'<meta name="description"[^>]*>', lambda _: f'<meta name="description" content="{description}">', source, count=1)
    content = f'<article class="article-page"><a class="article-back" href="../?category={quote(str(meta["category"]))}"><span class="link-arrow link-arrow-left" aria-hidden="true"></span> 返回{html.escape(CATEGORIES[meta["category"]])}</a><h1>{title}</h1>{demo}<p class="article-byline">{byline}</p>{toc}<div class="article-body">{clean}</div>{contact}</article>'
    return re.sub(r'(<main[^>]*>).*?(</main>)', lambda m: m[1] + content + m[2], source, count=1, flags=re.S)


def render_home(entries):
    source = shared_chrome((ROOT / "index.html").read_text(encoding="utf-8"), "index")
    cards = []
    for entry in entries:
        search = ' '.join([entry["title"], entry["author"], entry["major"], entry["destination"], entry["excerpt"], *entry["tags"]])
        badge = '<span class="demo-badge">演示</span>' if entry["demo"] else ''
        esc = lambda value: html.escape(str(value), quote=True)
        label = ' · '.join(filter(None, (CATEGORIES[entry["category"]], entry["year"] + ' 届', entry["major"])))
        cards.append(f'<article class="article-item" data-category="{esc(entry["category"])}" data-year="{esc(entry["year"])}" data-demo="{str(entry["demo"]).lower()}" data-search="{esc(search)}">{badge}<p class="article-meta">{html.escape(label)}</p><h3><a href="./{esc(entry["url"])}">{html.escape(entry["title"])}</a></h3><p class="article-excerpt">{html.escape(entry["excerpt"])}</p><a class="article-more" href="./{esc(entry["url"])}">阅读全文<span class="link-arrow"></span></a></article>')
    source = re.sub(r'(<div id="articles"[^>]*>).*?(</div>)', lambda m: m[1] + ''.join(cards) + m[2], source, count=1, flags=re.S)
    years = ''.join(f'<option value="{html.escape(year, quote=True)}">{html.escape(year)}</option>' for year in sorted({entry["year"] for entry in entries}, reverse=True))
    source = re.sub(r'(<select id="year-filter">).*?(</select>)', lambda m: m[1] + '<option value="all">全部届次</option>' + years + m[2], source, count=1, flags=re.S)
    count = f'{len(entries)} 篇经历' + (' · 含演示内容' if any(entry["demo"] for entry in entries) else '')
    return re.sub(r'(<p id="results-count"[^>]*>).*?(</p>)', lambda m: m[1] + count + m[2], source, count=1, flags=re.S)



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
    (ROOT / "index.html").write_text(render_home(entries), encoding="utf-8")
    submission = (ROOT / "submit.html").read_text(encoding="utf-8")
    (ROOT / "submit.html").write_text(shared_chrome(submission, "submit"), encoding="utf-8")
    print(f"Generated {len(entries)} articles")


if __name__ == "__main__":
    main()
