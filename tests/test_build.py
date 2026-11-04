"""Build invariants for structured submissions and safe Markdown output."""
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("uem_build", ROOT / "scripts" / "build.py")
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)


class SubmissionBuildTests(unittest.TestCase):
    def test_shared_background_and_simple_homepage(self):
        stylesheet = (ROOT / "assets/css/site.css").read_text(encoding="utf-8")
        homepage = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('url("../images/anguo-garden.jpg")', stylesheet)
        self.assertIn("--photo-tint", stylesheet)
        self.assertIn("--reading-line", stylesheet)
        self.assertNotIn("--reading-bg", stylesheet)
        self.assertNotIn("hero-visual", homepage)
        self.assertNotIn("hero-paths", homepage)
        self.assertIn('data-site-footer', homepage)
        self.assertIn('data-site-footer', (ROOT / 'submit.html').read_text(encoding='utf-8'))
        self.assertIn('class="site-footer"', homepage)
        self.assertNotIn('class="hero-corner"', homepage)
        self.assertIn('background:transparent;min-height', stylesheet)

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

    def test_demo_is_not_represented_as_real_story(self):
        sample = (ROOT / "data/demo-submission.md").read_text(encoding="utf-8")
        self.assertIn("不是真实投稿", sample)


if __name__ == "__main__":
    unittest.main()
