"""SEO generation, portability and publication regression checks."""
from pathlib import Path
import tempfile
import unittest

from scripts.site_metadata import Metadata, generate, site_origin, verify_metadata


class SiteMetadataTests(unittest.TestCase):
    def fixture(self, root):
        (root / "assets").mkdir()
        (root / "assets/logo.png").write_bytes(b"image")
        (root / "articles").mkdir()
        home = ('<html><head><title>Example · Home</title>'
                '<meta name="description" content="A &amp; B">'
                '<link rel="canonical" href="https://portable.example/">'
                '<meta property="og:image" content="./assets/logo.png">'
                '<meta property="og:image:alt" content="Example"></head></html>')
        (root / "index.html").write_text(home, encoding="utf-8")
        (root / "articles/example.html").write_text(
            home.replace("Example · Home", "Article &amp; author"), encoding="utf-8")

    def test_generated_pages_share_identity_and_keep_their_own_routes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture(root)
            generate(root)
            verify_metadata(root)
            article = Metadata((root / "articles/example.html").read_text(encoding="utf-8"))
            self.assertEqual(article.canonicals, ["https://portable.example/articles/example.html"])
            self.assertEqual(article.meta["og:type"], "article")
            self.assertEqual(article.meta["og:title"], "Article & author")
            self.assertEqual(article.meta["twitter:image"], "https://portable.example/assets/logo.png")
            before = (root / "index.html").read_bytes()
            generate(root)
            self.assertEqual((root / "index.html").read_bytes(), before)

    def test_publication_rejects_drift_and_missing_resources(self):
        for target, replacement in (
            ("articles/example.html", '<html><head><title>Broken</title></head></html>'),
            ("sitemap.xml", '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"/>'),
            ("robots.txt", "User-agent: *\nDisallow: /"),
            ("assets/logo.png", None),
        ):
            with self.subTest(target=target), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                self.fixture(root)
                generate(root)
                if replacement is None:
                    (root / target).unlink()
                else:
                    (root / target).write_text(replacement, encoding="utf-8")
                with self.assertRaises(ValueError):
                    verify_metadata(root)

    def test_homepage_origin_rejects_query_fragment_and_insecure_urls(self):
        for url in ("http://example.org/", "https://example.org/path/", "https://example.org/?q=1", "https://example.org/#main"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                site_origin(f'<link rel="canonical" href="{url}">')
