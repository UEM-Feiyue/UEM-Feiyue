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
        self.assertIn("--photo-overlay", stylesheet)
        self.assertIn("@view-transition{navigation:auto}", stylesheet)
        self.assertIn('rel="preload" as="image"', homepage)
        self.assertNotIn(".page.is-home{background-image:", stylesheet)
        self.assertIn("body{", stylesheet)
        self.assertIn("background:var(--footer-surface)", stylesheet)
        for page in (homepage, submission):
            self.assertIn('data-site-footer', page)
            self.assertIn('assets/js/theme-init.js', page)
        self.assertNotIn("hero-visual", homepage)
        self.assertNotIn("hero-corner", homepage)
        self.assertIn('theme-init.js', build.render({"category": "career", "author": "同学", "year": "2026", "destination": "企业"}, "## 正文", "articles/test.html"))

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

    def test_demo_is_not_represented_as_real_story(self):
        sample = (ROOT / "data/demo-submission.md").read_text(encoding="utf-8")
        self.assertIn("不是真实投稿", sample)


if __name__ == "__main__":
    unittest.main()
