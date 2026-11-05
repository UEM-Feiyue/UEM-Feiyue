"""Build invariants for structured submissions and safe Markdown output."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

spec = importlib.util.spec_from_file_location("uem_build", ROOT / "scripts" / "build.py")
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)


class SubmissionBuildTests(unittest.TestCase):
    def test_unified_theme_background_and_footer(self):
        stylesheet = (ROOT / "assets/css/site.css").read_text(encoding="utf-8")
        homepage = (ROOT / "index.html").read_text(encoding="utf-8")
        submission = (ROOT / "submit.html").read_text(encoding="utf-8")
        self.assertIn('url("../images/anguo-garden.jpg")', stylesheet)
        self.assertIn(".campus-banner{", stylesheet)
        self.assertIn("background-size:cover", stylesheet)
        self.assertIn("height:clamp(270px,30vw,440px)", stylesheet)
        self.assertIn("height:clamp(220px,60vw,320px)", stylesheet)
        self.assertIn("@view-transition{navigation:auto}", stylesheet)
        self.assertIn("body{background:var(--bg)}", stylesheet)
        self.assertNotIn("background-attachment:fixed", stylesheet)
        self.assertNotIn(".page::before{", stylesheet)
        self.assertIn('rel="preload" as="image"', homepage)
        self.assertIn('class="campus-banner"', homepage)
        self.assertIn('class="campus-banner"', submission)
        self.assertIn('class="campus-banner"', build.render({"category": "career", "author": "同学", "year": "2026", "destination": "企业"}, "## 正文", "articles/test.html"))
        self.assertIn("background:var(--footer-surface)", stylesheet)
        for page in (homepage, submission):
            self.assertIn('data-site-footer', page)
            self.assertIn('assets/js/theme-init.js', page)
        self.assertNotIn("hero-visual", homepage)
        self.assertNotIn("hero-corner", homepage)
        self.assertIn('theme-init.js', build.render({"category": "career", "author": "同学", "year": "2026", "destination": "企业"}, "## 正文", "articles/test.html"))

    def test_pagefind_indexing_and_sidebar_chrome(self):
        homepage = (ROOT / "index.html").read_text(encoding="utf-8")
        submission = (ROOT / "submit.html").read_text(encoding="utf-8")
        renderer = (ROOT / "scripts/site_build.py").read_text(encoding="utf-8")
        article = build.render({"category": "career", "author": "同学", "year": "2026", "destination": "企业"}, "## 搜索正文", "articles/sample.html")
        for html_source in (homepage, submission):
            self.assertIn("<body data-pagefind-ignore>", html_source)
            self.assertEqual(html_source.count('id="theme-toggle"'), 1)
            self.assertNotIn('id="theme-toggle-mobile"', html_source)
        self.assertIn('data-pagefind-body', article)
        self.assertNotIn('data-pagefind-ignore', article)
        self.assertIn('"pagefind"', renderer)
        self.assertNotIn('data-search=', homepage)
        self.assertIn('id="search-status"', homepage)

    def test_year_menu_and_editor_contract(self):
        homepage = (ROOT / "index.html").read_text(encoding="utf-8")
        submission = (ROOT / "submit.html").read_text(encoding="utf-8")
        source = (ROOT / "assets/js/submit.js").read_text(encoding="utf-8")
        site = (ROOT / "assets/js/site.js").read_text(encoding="utf-8")
        css = (ROOT / "assets/css/site.css").read_text(encoding="utf-8")
        schema = json.loads((ROOT / "data/schema.json").read_text(encoding="utf-8"))
        self.assertIn('id="year-options" class="year-options" popover', homepage)
        self.assertIn("yearMenu.showPopover()", site)
        self.assertIn("yearMenu.hidePopover()", site)
        self.assertIn("field-sizing:content", css)
        self.assertNotIn("textarea-grip", css + source)
        self.assertIn("markdown-help-content", source)
        self.assertIn("guide.open = true", source)
        self.assertIn("control.hidden = showing", source)
        self.assertIn("textarea", source)
        self.assertIn('id="preview-text"', submission)
        fields = {entry["name"]: entry for entry in schema["fields"]}
        self.assertIn("hello@example.com", fields["contact"]["placeholder"])
        self.assertEqual(fields["year"]["pattern"], "[0-9]{4}")

    def test_shared_theme_toc_and_form_layout(self):
        stylesheet = (ROOT / "assets/css/site.css").read_text(encoding="utf-8")
        homepage = (ROOT / "index.html").read_text(encoding="utf-8")
        submission = (ROOT / "submit.html").read_text(encoding="utf-8")
        js = (ROOT / "assets/js/site.js").read_text(encoding="utf-8")
        for document in (homepage, submission):
            self.assertIn('data-mode="system"', document)
            for mode in ("system", "light", "dark"):
                self.assertIn('data-theme-icon="' + mode + '"', document)
        self.assertIn("prefers-color-scheme:dark", stylesheet)
        self.assertIn("['system', 'light', 'dark']", js)
        self.assertIn('class="year-select"', homepage)
        self.assertIn('appearance:none', stylesheet)
        self.assertIn('.article-toc summary{', stylesheet)
        self.assertIn(".form-wrap{max-width:820px;padding:0;", stylesheet)
        article = build.render({"category": "career", "author": "同学", "year": "2026", "destination": "企业"},
                               "## 第一章\n\n正文\n\n## 第二章\n\n正文", "articles/test.html")
        self.assertIn('<details class="article-toc">', article)
        self.assertIn('<summary>本页目录</summary>', article)

    def test_published_article_brand_assets(self):
        meta = {"category": "career", "author": "同学", "year": "2026", "destination": "企业"}
        page = build.render(meta, "## 正文", "articles/example.html")
        self.assertIn('../assets/icons/favicon.svg', page)
        self.assertIn('../assets/images/favicon-横版.png', page)

    def test_no_redundant_title_field(self):
        schema = json.loads((ROOT / "data/schema.json").read_text(encoding="utf-8"))
        names = {field["name"] for field in schema["fields"]}
        self.assertNotIn("title", names)
        self.assertTrue({"author", "year", "destination", "program", "body"} <= names)

    def test_title_auto_generated(self):
        meta = {"author": "张同学", "destination": "香港中文大学", "program": "MSc@CS"}
        self.assertEqual(build.display_title(meta), "张同学 — 香港中文大学 · MSc@CS")
        meta.pop("program")
        self.assertEqual(build.display_title(meta), "张同学 — 香港中文大学")

    def test_render_heading_table_and_sanitize(self):
        meta = {"category": "overseas", "author": "张同学", "year": "2026", "destination": "香港中文大学"}
        body = "# 一级标题\\n\\n| 项目 | 说明 |\\n| --- | --- |\\n| A | B |\\n\\n~~删除文字~~\\n\\n- [x] 已完成\\n\\n<script>alert(1)</script>".replace("\\n", "\n")
        page = build.render(meta, body, "articles/sample.html")
        self.assertIn("<h1", page)
        self.assertIn("<table>", page)
        self.assertIn("<del>", page)
        self.assertIn('type="checkbox"', page)
        self.assertNotIn("<script>alert(1)</script>", page)

    def test_schema_required_fields_and_limits_are_enforced_before_publication(self):
        meta = {"category": "career", "author": "Test author", "year": "2026", "destination": "Example"}
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "test.md"
            for field in build.SCHEMA["fields"]:
                if field.get("required"):
                    values = dict(meta)
                    body = "Article body"
                    if field["name"] == "body":
                        body = ""
                    else:
                        values.pop(field["name"], None)
                    source.write_text("---\n" + build.yaml.safe_dump(values) + "---\n" + body, encoding="utf-8")
                    with self.subTest(field=field["name"]), self.assertRaises(ValueError):
                        build.parse(source)
                if field.get("maxLength"):
                    excessive = "x" * (field["maxLength"] + 1)
                    values = dict(meta)
                    body = "Body"
                    if field["name"] == "body":
                        body = excessive
                    else:
                        values[field["name"]] = excessive
                    source.write_text("---\n" + build.yaml.safe_dump(values) + "---\n" + body, encoding="utf-8")
                    with self.subTest(limit=field["name"]), self.assertRaises(ValueError):
                        build.parse(source)

    def test_schema_category_and_year_patterns_reject_invalid_content(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "test.md"
            for category, year in (("unknown", "2026"), ("career", "abcd"), ("career", True)):
                values = {"category": category, "year": year, "author": "Test", "destination": "Example"}
                source.write_text("---\n" + build.yaml.safe_dump(values) + "---\nBody", encoding="utf-8")
                with self.subTest(category=category, year=year), self.assertRaises(ValueError):
                    build.parse(source)

    def test_editorial_demo_inventory(self):
        samples = sorted((ROOT / "content/demo").glob("*.md"))
        if not samples:
            return  # Removing the demo directory later must stay supported.
        self.assertEqual(len(samples), 4)
        categories = []
        for path in samples:
            meta, body = build.parse(path)
            self.assertIs(meta.get("demo"), True)
            self.assertNotIn("演示声明", body)
            self.assertGreater(len(body), 600)
            categories.append(meta["category"])
            rendered = build.render(meta, body, "articles/" + path.stem + ".html")
            self.assertEqual(rendered.count('<span class="demo-badge">演示</span>'), 1)
        self.assertEqual(set(categories), set(build.CATEGORIES))

    def test_preview_reuses_article_styles(self):
        source = (ROOT / "assets/css/site.css").read_text(encoding="utf-8")
        form = (ROOT / "submit.html").read_text(encoding="utf-8")
        self.assertIn('id="preview-text" class="article-page"', form)
        self.assertNotIn(".preview .article-body{font-size", source)
        self.assertNotIn(".preview h3{", source)

    def test_demo_is_not_represented_as_real_story(self):
        sample = (ROOT / "data/demo-submission.md").read_text(encoding="utf-8")
        self.assertIn("不是真实投稿", sample)


if __name__ == "__main__":
    unittest.main()
