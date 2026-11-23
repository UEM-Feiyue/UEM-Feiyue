"""Homepage-owned identity and metadata for the complete static artifact."""
import html
from html.parser import HTMLParser
import re
from urllib.parse import urljoin, urlsplit
from xml.etree import ElementTree as ET


class Metadata(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.meta = {}
        self.canonicals = []
        self.title = ""
        self.in_title = False
        self.feed(source)

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if tag == "title":
            self.in_title = True
        if tag == "meta":
            key = attrs.get("name", attrs.get("property"))
            if key in self.meta:
                raise ValueError(f"Duplicate metadata: {key}")
            self.meta[key] = attrs.get("content", "")
        if tag == "link" and "canonical" in attrs.get("rel", "").split():
            self.canonicals.append(attrs.get("href", ""))

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title += data


def site_origin(source):
    page = Metadata(source)
    if len(page.canonicals) != 1:
        raise ValueError("Homepage must define exactly one canonical origin")
    url = urlsplit(page.canonicals[0])
    if (url.scheme != "https" or not url.hostname or url.username or url.password
            or url.path != "/" or url.query or url.fragment):
        raise ValueError("Homepage canonical must be an HTTPS origin with a trailing slash")
    return page.canonicals[0].rstrip("/")


def page_url(origin, relative):
    return origin + "/" + ("" if relative == "index.html" else relative)


def social_values(page, identity, url, article):
    image = urljoin(identity.canonicals[0], identity.meta["og:image"])
    return {
        "og:site_name": identity.title.split(" · ")[0],
        "og:title": page.title, "og:description": page.meta["description"],
        "og:url": url, "og:type": "article" if article else "website",
        "og:locale": "zh_CN", "og:image": image,
        "og:image:alt": identity.meta["og:image:alt"],
        "twitter:card": "summary_large_image", "twitter:title": page.title,
        "twitter:description": page.meta["description"],
        "twitter:image": image,
        "twitter:image:alt": identity.meta["og:image:alt"],
    }


def generate(root):
    home = (root / "index.html").read_text(encoding="utf-8")
    origin = site_origin(home)
    identity = Metadata(home)
    urls = []
    for path in sorted(root.rglob("*.html")):
        source = path.read_text(encoding="utf-8")
        page = Metadata(source)
        relative = path.relative_to(root).as_posix()
        url = page_url(origin, relative)
        values = social_values(page, identity, url, relative.startswith("articles/"))
        source = re.sub(r'<link\b[^>]*rel="canonical"[^>]*>\s*|<meta\b[^>]*(?:property|name)="(?:og:|twitter:)[^"]*"[^>]*>\s*', '', source)
        tags = [f'<link rel="canonical" href="{html.escape(url, quote=True)}">']
        for key, value in values.items():
            attr = "name" if key.startswith("twitter:") else "property"
            tags.append(f'<meta {attr}="{key}" content="{html.escape(value, quote=True)}">')
        source = source.replace("</head>", "\n".join(tags) + "\n</head>", 1)
        path.write_text(source, encoding="utf-8")
        urls.append(url)
    sitemap = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    for url in urls:
        ET.SubElement(ET.SubElement(sitemap, "url"), "loc").text = url
    ET.ElementTree(sitemap).write(root / "sitemap.xml", encoding="utf-8", xml_declaration=True)
    (root / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {origin}/sitemap.xml\n", encoding="utf-8")


def verify_metadata(root):
    home = (root / "index.html").read_text(encoding="utf-8")
    origin, identity = site_origin(home), Metadata(home)
    urls = []
    for path in root.rglob("*.html"):
        page = Metadata(path.read_text(encoding="utf-8"))
        relative = path.relative_to(root).as_posix()
        url = page_url(origin, relative)
        if page.canonicals != [url] or not page.title or not page.meta.get("description"):
            raise ValueError(f"{relative}: invalid canonical, title or description")
        for key, expected in social_values(page, identity, url, relative.startswith("articles/")).items():
            if page.meta.get(key) != expected or not expected:
                raise ValueError(f"{relative}: inconsistent {key}")
        if "noindex" in page.meta.get("robots", "").lower():
            raise ValueError(f"{relative}: unexpected noindex")
        urls.append(url)
    image = urlsplit(identity.meta["og:image"])
    if image.scheme != "https" or not image.netloc:
        raise ValueError("Social image must be an absolute HTTPS URL")
    if image.netloc == urlsplit(origin).netloc and not (root / image.path.lstrip("/")).is_file():
        raise ValueError("Missing social image")
    locations = [node.text for node in ET.parse(root / "sitemap.xml").findall(".//{*}loc")]
    if sorted(locations) != sorted(urls):
        raise ValueError("Sitemap does not match published canonical pages")
    if (root / "robots.txt").read_text(encoding="utf-8") != f"User-agent: *\nAllow: /\n\nSitemap: {origin}/sitemap.xml\n":
        raise ValueError("robots.txt does not match canonical origin")
