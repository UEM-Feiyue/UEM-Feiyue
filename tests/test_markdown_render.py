"""Regression contract for authored Markdown in preview and static articles."""
import unittest
from pathlib import Path

from scripts.markdown_render import render_markdown

ROOT = Path(__file__).resolve().parents[1]


class MarkdownPublicationTests(unittest.TestCase):
    def test_blockquote_is_markup_not_a_literal_greater_than(self):
        body = (
            "# 【系统测试】考研经历投稿\n\n"
            "> 本文仅用于投稿系统测试。\n\n"
            "## 一、前期准备\n\n"
            "准备阶段整理目标院校。\n\n"
            "1. 基础阶段\n2. 强化阶段\n3. 冲刺阶段\n\n"
            "**测试标记：UEM-QA-POSTGRAD-001**"
        )
        rendered = render_markdown(body)
        self.assertIn("<blockquote>", rendered)
        self.assertIn("<p>本文仅用于投稿系统测试。</p>", rendered)
        self.assertNotIn("&gt; 本文", rendered)
        self.assertNotIn("> 本文", rendered)
        self.assertIn("<ol>", rendered)
        self.assertIn("<strong>", rendered)

    def test_extended_markdown_works_under_publication_sanitizer(self):
        body = (
            "| 阶段 | 事项 |\n| --- | --- |\n| 开始 | 整理 |\n\n"
            "- [x] 已完成\n\n~~删除线~~\n\n"
            "```python\nprint('hi')\n```"
        )
        output = render_markdown(body)
        for tag in ("<table>", "<del>", "<pre>", "<code>"):
            self.assertIn(tag, output)
        self.assertIn('type="checkbox"', output)

    def test_user_html_does_not_execute_and_link_schemes_are_sanitized(self):
        body = (
            "> **提示** <script>alert(1)</script>\n\n"
            "[危险链接](javascript:alert%281%29)\n\n"
            "<img src=x onerror=alert(1)>\n\n"
            "[正常链接](https://example.com)"
        )
        output = render_markdown(body)
        self.assertIn("<blockquote>", output)
        self.assertNotIn("<script", output)
        self.assertNotIn("<img src=x", output)
        self.assertNotIn('href="javascript:', output)
        self.assertIn('href="https://example.com"', output)

    def test_preview_and_published_article_use_same_typography(self):
        browser = (ROOT / "assets/js/submit.js").read_text(encoding="utf-8")
        css = (ROOT / "assets/css/site.css").read_text(encoding="utf-8")
        self.assertIn("body.className = 'article-body'", browser)
        self.assertIn("bodyPreview.className = 'markdown-preview article-body'", browser)
        self.assertIn("marked.parse(safeSource", browser)
        self.assertIn("source.replace(/<(?=[a-z!/])/gi, '&lt;')", browser)
        self.assertIn(".article-body blockquote {", css)
        self.assertNotIn(".preview .article-body blockquote", css)
        self.assertNotIn(".markdown-preview blockquote", css)


if __name__ == "__main__":
    unittest.main()
