"""Exercise the complete UEM artifact, including its Pages project subpath."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import sys
from threading import Thread
import time
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PREFIX = "/UEM-Feiyue.github.io"
sys.path.insert(0, str(ROOT))
from preview import PreviewHandler


class Handler(SimpleHTTPRequestHandler):
    script_delay = 0

    def translate_path(self, path):
        if path.startswith(PREFIX + "/"):
            path = path[len(PREFIX):]
        return super().translate_path(path)

    def do_GET(self):
        if self.path.endswith('/assets/js/site.js'):
            time.sleep(self.script_delay)
        super().do_GET()

    def log_request(self, *args):
        pass


def main():
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(Handler, directory=str(ROOT / "_site")))
    worker = Thread(target=server.serve_forever, daemon=True)
    worker.start()
    base = f"http://127.0.0.1:{server.server_port}"
    articles = json.loads((ROOT / "_site/data/articles.json").read_text(encoding="utf-8"))
    output = ROOT / "output/playwright"
    output.mkdir(parents=True, exist_ok=True)
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            for width in (320, 390, 900, 901, 1440, 1600):
                for theme in ("light", "dark"):
                    context = browser.new_context(viewport={"width": width, "height": 900}, reduced_motion="reduce")
                    context.add_init_script(f"localStorage.setItem('uem-theme', '{theme}')")
                    page = context.new_page()
                    errors = []
                    page.on("pageerror", lambda error: errors.append(str(error)))
                    page.goto(base + PREFIX + "/", wait_until="networkidle")
                    assert page.locator("h1:visible").count() == 1
                    assert page.locator(".article-item .article-meta").first.inner_text().endswith("某学院 · 某专业")
                    assert page.locator(".article-item h3").first.inner_text().startswith(articles[0]["author"] + " — ")
                    assert page.locator(".article-item").first.evaluate("el => el.querySelector('h3').compareDocumentPosition(el.querySelector('.article-meta')) & Node.DOCUMENT_POSITION_FOLLOWING")
                    # A bounded image banner retains aspect ratio at desktop/mobile sizes.
                    background = page.evaluate("""() => {
                        const container = document.querySelector('.page');
                        const banner = document.querySelector('.campus-banner');
                        const css = getComputedStyle(banner);
                        const rect = banner.getBoundingClientRect();
                        const contentRect = document.querySelector('main.content').getBoundingClientRect();
                        return {
                            bodyImage: getComputedStyle(document.body).backgroundImage,
                            bannerCount: document.querySelectorAll('.campus-banner').length,
                            bannerImage: css.backgroundImage,
                            bannerSize: css.backgroundSize,
                            bannerHeight: rect.height,
                            bannerWidth: rect.width,
                            containerWidth: container.getBoundingClientRect().width,
                            contentTop: contentRect.top,
                            bannerBottom: rect.bottom,
                            titleTop: document.querySelector('#hero-title').getBoundingClientRect().top,
                            titleBottom: document.querySelector('#hero-title').getBoundingClientRect().bottom,
                            leadTop: document.querySelector('.home-intro .lead').getBoundingClientRect().top,
                            contentBackground: getComputedStyle(document.querySelector('main.content')).backgroundColor
                        };
                    }""")
                    assert background["bodyImage"] == "none"
                    assert background["bannerCount"] == 1
                    # The mobile header is a real, stable row above the banner.
                    if width <= 900:
                        layout = page.evaluate("""() => {
                            const header = document.querySelector('.topbar');
                            const banner = document.querySelector('.campus-banner');
                            const head = header.getBoundingClientRect();
                            const image = banner.getBoundingClientRect();
                            return {height:head.height, top:head.top, bottom:head.bottom,
                                    imageTop:image.top, surface:getComputedStyle(header).backgroundColor};
                        }""")
                        assert layout["height"] == 72
                        assert abs(layout["imageTop"] - layout["bottom"]) <= 1
                        assert layout["surface"] != "rgba(0, 0, 0, 0)"
                        assert background["bannerImage"].count("linear-gradient") == 3
                        assert layout["surface"] in background["bannerImage"]
                    else:
                        assert page.locator(".campus-banner").evaluate("el => Math.abs(el.getBoundingClientRect().top) < 1")
                    assert page.locator("#theme-toggle").count() == 1
                    if width <= 900:
                        assert page.locator(".topbar").is_visible()
                    else:
                        assert page.locator(".topbar").is_hidden()
                        assert page.locator("#theme-toggle").is_visible()
                    assert "anguo-garden.jpg" in background["bannerImage"]
                    assert all(value.strip() == "cover" for value in background["bannerSize"].split(","))
                    assert 220 <= background["bannerHeight"] <= 440
                    assert abs(background["bannerWidth"] - background["containerWidth"]) <= 1
                    assert background["contentTop"] >= background["bannerBottom"] - 1
                    assert background["titleTop"] < background["bannerBottom"]
                    assert background["titleBottom"] > background["bannerBottom"] - background["bannerHeight"]
                    assert background["leadTop"] >= background["bannerBottom"]
                    assert background["contentBackground"] != "rgba(0, 0, 0, 0)"
                    # Logo on the current homepage must scroll even when the URL
                    # remains unchanged. The previous same-URL guard swallowed it.
                    brand = ".mobile-brand" if width <= 900 else ".sidebar .brand"
                    assert page.locator(brand).is_visible()
                    assert page.locator(brand + " img").evaluate(
                        "el => el.naturalWidth === 1226 && el.naturalHeight === 285 && getComputedStyle(el).maskImage === 'none'"
                    )
                    assert page.locator(".footer-logo").evaluate(
                        "el => getComputedStyle(el).backgroundColor === 'rgba(0, 0, 0, 0)' && getComputedStyle(el).paddingTop === '0px'"
                    )
                    if width > 900:
                        # The viewport-fixed desktop navigation stays independent of
                        # document scrolling and must not compress its brand.
                        geometry = lambda: page.locator(brand + " img").evaluate("""el => {
                            const r = el.getBoundingClientRect();
                            return {width:r.width,height:r.height,top:r.top};
                        }""")
                        before_scroll = geometry()
                        assert page.locator("#sidebar").evaluate(
                            "el => getComputedStyle(el).position === 'fixed' && Math.abs(el.getBoundingClientRect().left) < .5"
                        )
                        assert page.locator(".page").evaluate(
                            "el => Math.abs(el.getBoundingClientRect().left - document.querySelector('#sidebar').getBoundingClientRect().right) < .5"
                        )
                        assert page.locator(brand).evaluate(
                            "el => getComputedStyle(el).flexShrink === '0'"
                        )
                        assert abs(before_scroll["width"] / before_scroll["height"] - 1226 / 285) < .015
                    page.evaluate("window.scrollTo({top:document.documentElement.scrollHeight,behavior:'instant'})")
                    if page.evaluate("document.documentElement.scrollHeight - innerHeight > 100"):
                        page.wait_for_function("scrollY > 100")
                    if width > 900:
                        after_scroll = geometry()
                        for dimension in ("width", "height", "top"):
                            assert abs(before_scroll[dimension] - after_scroll[dimension]) <= .5, (
                                width, dimension, before_scroll, after_scroll
                            )
                        divider_positions = page.evaluate("""() => [
                            document.querySelector('.sidebar-bottom').getBoundingClientRect().top,
                            document.querySelector('.footer-bottom').getBoundingClientRect().top
                        ]""")
                        assert abs(divider_positions[0] - divider_positions[1]) <= 2, (width, divider_positions)
                    page.locator(brand).click()
                    page.wait_for_function("scrollY <= 2")
                    assert page.url.rstrip("/").endswith(PREFIX)
                    assert page.locator("#category-nav [data-category]").count() == 5
                    assert page.locator(".site-footer").count() == 1
                    assert page.locator(".site-footer").evaluate(
                        "el => getComputedStyle(el).backgroundImage.includes('linear-gradient')"
                    )
                    # Footer columns align to the outside edges of the content area.
                    footer = page.evaluate("""() => {
                        const inner = document.querySelector('.footer-inner').getBoundingClientRect();
                        const brand = document.querySelector('.footer-grid > div:first-child').getBoundingClientRect();
                        const links = document.querySelector('.footer-grid > div:last-child').getBoundingClientRect();
                        return {left: inner.left, right: inner.right, brand: brand.left,
                                navLeft: links.left, navRight: links.right};
                    }""")
                    assert abs(footer["brand"] - footer["left"]) <= 2
                    if width > 720:
                        assert abs(footer["navRight"] - footer["right"]) <= 2
                    else:
                        assert abs(footer["navLeft"] - footer["left"]) <= 2

                    if width <= 900:
                        assert page.locator("#sidebar").evaluate("el => el.inert")
                        page.locator("#menu-toggle").click()
                        assert page.locator("#menu-toggle").get_attribute("aria-expanded") == "true"
                        assert page.locator(".shell").evaluate("el => el.classList.contains('menu-open')")
                        assert page.locator(".shell").evaluate("el => getComputedStyle(el, '::before').content === 'none'")
                        assert page.locator("#sidebar").evaluate("el => getComputedStyle(el).position === 'fixed'")
                        assert page.locator("#sidebar").evaluate("el => el.getBoundingClientRect().top >= document.querySelector('.topbar').getBoundingClientRect().bottom")
                        assert page.locator("#sidebar").evaluate("el => el.getBoundingClientRect().height < innerHeight * .8")
                        assert page.locator("#menu-toggle").evaluate("el => getComputedStyle(el).position !== 'absolute'")
                        assert not page.locator("#sidebar").evaluate("el => el.inert")
                        assert page.locator("#theme-toggle").is_visible()
                        original_theme = page.evaluate("document.documentElement.dataset.theme")
                        modes = ["system", "light", "dark"]
                        start = modes.index(original_theme or "system")
                        for step in range(1, 4):
                            page.locator("#theme-toggle").click()
                            current = modes[(start + step) % 3]
                            assert page.locator("#theme-toggle").get_attribute("data-mode") == current
                            assert (page.evaluate("document.documentElement.dataset.theme") or "system") == current
                        assert page.evaluate("document.documentElement.dataset.theme") == original_theme
                        page.keyboard.press("Escape")
                        assert page.locator("#menu-toggle").get_attribute("aria-expanded") == "false"
                        assert not page.locator(".shell").evaluate("el => el.classList.contains('menu-open')")
                        assert page.locator("#menu-toggle").evaluate("el => el === document.activeElement")
                        page.keyboard.press("Tab")
                        assert not page.locator("#sidebar").evaluate("el => el.contains(document.activeElement)")
                    else:
                        assert not page.locator("#sidebar").evaluate("el => el.inert")
                    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 2")
                    if width in (390, 1440) and theme == "light":
                        page.screenshot(path=str(output / f"home-{width}.png"), full_page=True)
                    page.evaluate("window.__sameDocument = true")
                    page.locator('#home-intro a').filter(has_text='浏览').first.click()
                    assert page.evaluate("window.__sameDocument")
                    assert "view=all" in page.url
                    assert page.locator(".article-item:visible").count() == len(articles)
                    if width in (390, 1440) and theme == "light":
                        page.evaluate("scrollTo(0, document.body.scrollHeight)")
                        assert page.evaluate("scrollY > 0")
                        if width <= 900:
                            page.locator("#menu-toggle").click()
                        page.locator("#category-nav [data-category='kaoyan']").click()
                        page.wait_for_url("**/?category=kaoyan")
                        page.wait_for_function("scrollY === 0")
                        assert page.locator(".article-item:visible").count() == 1
                        if width <= 900:
                            page.locator("#menu-toggle").click()
                        page.locator("#category-nav [data-category='all']").click()
                        page.wait_for_url("**/?view=all")
                    assert page.locator("#year-filter").evaluate("el => getComputedStyle(el).appearance") == "none"
                    assert page.locator(".year-select svg").is_visible()
                    assert page.locator("#year-trigger").is_visible()
                    assert page.locator("#year-trigger").evaluate("el => el.getBoundingClientRect().width < 160")
                    page.locator("#year-trigger").click()
                    assert page.locator("#year-options").evaluate("el => el.matches(':popover-open')")
                    assert page.locator("#year-options .year-option").count() >= 2
                    page.locator("#year-options [data-value='2026']").click()
                    assert page.locator("#year-filter").input_value() == "2026"
                    assert page.locator("#year-label").inner_text() == "2026"
                    page.locator("#year-trigger").focus()
                    page.keyboard.press("ArrowDown")
                    assert page.locator("#year-options").evaluate("el => el.matches(':popover-open')")
                    assert page.locator("#year-options [data-value='all']").evaluate(
                        "el => el.getBoundingClientRect().height < 50 && el.getBoundingClientRect().right <= innerWidth - 8"
                    )
                    page.keyboard.press("Escape")
                    assert not page.locator("#year-options").evaluate("el => el.matches(':popover-open')")
                    page.locator("#year-trigger").click()
                    page.locator("#year-options [data-value='all']").click()
                    assert page.locator("#year-filter").input_value() == "all"
                    visible_before_search = page.locator(".article-item:visible").count()
                    page.locator(".search-open").click()
                    assert page.locator("#search-dialog").evaluate("el => el.open")
                    assert page.locator("#search").evaluate("el => document.activeElement === el")
                    if width <= 900:
                        assert page.locator('.search-open').evaluate("""el => {
                            const button = el.getBoundingClientRect();
                            const menu = document.querySelector('#menu-toggle').getBoundingClientRect();
                            return getComputedStyle(el.querySelector('.search-label')).display === 'none' &&
                                button.right + 4 <= menu.left;
                        }""")
                    assert page.locator("#search-dialog").evaluate("""el => {
                        const dialog = el.getBoundingClientRect();
                        const button = document.querySelector('.search-open').getBoundingClientRect();
                        const expectedTop = button.bottom + 12;
                        const actualTop = dialog.top;
                        return Math.abs(actualTop - expectedTop) < 3 &&
                            Math.abs((dialog.left + dialog.right) / 2 - innerWidth / 2) < 2 &&
                            (innerWidth > 900 || button.bottom <= document.querySelector('.topbar').getBoundingClientRect().bottom);
                    }""")
                    if width <= 900:
                        assert page.locator('#search-dialog').evaluate("""el => {
                            const viewport = visualViewport;
                            Object.defineProperty(viewport, 'height', {configurable: true, value: 360});
                            viewport.dispatchEvent(new Event('resize'));
                            const available = 360 + viewport.offsetTop - el.getBoundingClientRect().top - 12;
                            const fits = parseFloat(getComputedStyle(el).maxHeight) <= available + 1;
                            delete viewport.height;
                            viewport.dispatchEvent(new Event('resize'));
                            return fits;
                        }""")
                    page.locator("#search").fill("no-matching-story-987654321")
                    assert page.locator(".article-item:visible").count() == visible_before_search
                    page.wait_for_function("document.querySelector('#search-results').textContent.includes('没有找到匹配内容')")
                    page.locator("#search").fill("简历修改")
                    page.locator("#search-results li a").first.wait_for(state="visible")
                    assert page.locator("#search-results .search-summary").inner_text().startswith("找到 ")
                    assert page.locator("#search-results .search-match mark").count() > 0
                    page.locator("#search-results li a").first.click()
                    page.wait_for_selector(".article-body")
                    assert articles[0]["author"] not in page.locator(".article-page > h1").inner_text()
                    if width == 1600:
                        assert page.evaluate("""() => {
                            const main = document.querySelector('main.content');
                            const article = document.querySelector('.article-page');
                            const box = main.getBoundingClientRect();
                            const content = article.getBoundingClientRect();
                            const style = getComputedStyle(main);
                            return Math.abs(content.left - box.left - parseFloat(style.paddingLeft)) < 2 &&
                                Math.abs(content.right - box.right + parseFloat(style.paddingRight)) < 2;
                        }""")
                    assert page.locator(".demo-badge").is_visible() == articles[0]["demo"]
                    assert page.locator(".article-toc").count() <= 1
                    if page.locator(".article-toc").count():
                        assert page.locator(".article-toc").evaluate("el => el.tagName") == "DETAILS"
                        assert page.locator(".article-toc-side").count() == 0
                        page.locator(".article-toc summary").click()
                        assert page.locator(".article-toc").get_attribute("open") is not None
                        assert page.locator(".article-toc a").first.is_visible()

                    assert page.locator("#category-nav [aria-current='page']").count() == 1
                    assert page.locator(".site-footer").count() == 1
                    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 2")
                    page.go_back(wait_until="networkidle")
                    assert page.locator(".search-open").is_visible()
                    assert not page.locator("#search-dialog").evaluate("el => el.open")
                    if width == 390 and theme == "light":
                        # Cross-document navigation should never expose the old page with
                        # a dismissed menu (the old root snapshot flash).
                        page.locator("#menu-toggle").click()
                        assert page.locator("#menu-toggle").get_attribute("aria-expanded") == "true"
                        page.locator("#category-nav a.nav-contribute").click()
                        page.wait_for_url("**/submit.html")
                        assert page.locator(".topbar").is_visible()
                        assert page.locator(".campus-banner").is_visible()
                        assert page.locator("#menu-toggle").get_attribute("aria-expanded") == "false"
                        assert page.locator("#sidebar").evaluate("el => el.inert")
                        page.go_back(wait_until="networkidle")
                        assert page.locator(".search-open").is_visible()
                    # Closed-mode regression without contacting live Turnstile or Worker.
                    page.route("**/assets/js/submission-config.js*", lambda route: route.fulfill(
                        content_type="application/javascript",
                        body="window.UEM_SUBMISSION_CONFIG={enabled:false};"
                    ))
                    page.goto(base + PREFIX + "/submit.html", wait_until="networkidle")
                    page.wait_for_selector("#body")
                    page.locator("#author").fill("Browser test")
                    page.locator("#year").fill("abcd")
                    assert not page.locator("#year").evaluate("el => el.checkValidity()")
                    page.locator("#year").fill("2026")
                    assert page.locator(".education-fields legend").inner_text() == "在校信息"
                    assert not page.locator("#college").evaluate("el => el.checkValidity()")
                    page.locator("#college").fill("某学院")
                    assert not page.locator("#major").evaluate("el => el.checkValidity()")
                    page.locator("#major").fill("某专业")
                    page.locator("#destination").fill("Example institution")
                    assert page.locator("#year").evaluate("el => el.getBoundingClientRect().width < 120")
                    assert "hello@example.com" in page.locator("#contact").get_attribute("placeholder")
                    assert page.locator("#body").evaluate("el => el.getBoundingClientRect().height >= 240")
                    page.locator("#body").fill(("## 复盘\\n\\n" + "过程很重要，经验可以复用。\\n") * 25)
                    assert page.locator("#body").evaluate("el => el.scrollHeight <= el.clientHeight + 3")
                    page.locator("#body").fill("")
                    page.locator(".demo-actions button").filter(has_text="载入示例").click()
                    page.wait_for_function("document.querySelector('#body').value.startsWith('## ')")
                    assert page.locator(".markdown-help").get_attribute("open") is None
                    assert page.locator(".markdown-preview").is_hidden()
                    assert page.locator("#body").is_visible()
                    assert "Markdown" in page.locator(".markdown-help").inner_text()
                    page.locator(".markdown-help summary").click()
                    assert "## 小标题" in page.locator(".markdown-help").inner_text()
                    page.locator("#body").fill("")
                    page.locator("#body").fill("## Heading\n\n**Test body**\n\n<script>window.__unsafe = true</script>")
                    page.locator("#contact").fill("do-not-save@example.invalid")
                    page.locator("#preview-button").click()
                    assert page.locator("#preview").is_visible()
                    assert page.locator("#preview .article-body strong").count() == 1, page.locator("#preview-text").inner_html()
                    assert page.locator("#preview .article-body strong").inner_text() == "Test body"
                    assert not page.evaluate("Boolean(window.__unsafe)")
                    assert "公开 GitHub Issue" in page.locator(".notice").inner_text()
                    assert page.locator(".form-wrap").evaluate("el => getComputedStyle(el).borderTopWidth") == "0px"
                    assert page.locator(".form-wrap").evaluate("el => getComputedStyle(el).boxShadow") == "none"
                    assert page.locator("#submit-button").is_visible()
                    assert page.locator("#submit-button").is_disabled()
                    assert page.locator("#submit-button").inner_text() == "投稿分享"
                    assert "暂未开放" in page.locator("#submission-status").inner_text()
                    page.reload(wait_until="networkidle")
                    page.wait_for_selector("#body")
                    assert page.locator("#author").input_value() == "Browser test"
                    assert page.locator("#contact").input_value() == ""
                    assert page.locator("#body").evaluate("el => el.scrollHeight <= el.clientHeight + 3")
                    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 2")
                    assert errors == [], errors
                    context.close()
                    print(f"UEM browser passed: {width}px, {theme}")
            context = browser.new_context(reduced_motion="no-preference")
            page = context.new_page()
            Handler.script_delay = 2
            try:
                page.goto(base + "/?category=kaoyan", wait_until="commit")
                page.wait_for_selector('#archive-intro')
                assert page.evaluate("""() => ({
                    active: document.querySelector('#category-nav [aria-current="page"]')?.dataset.category,
                    homeHidden: document.querySelector('#home-intro').hidden,
                    archiveHidden: document.querySelector('#archive-intro').hidden,
                    heading: document.querySelector('#stories-heading').textContent
                })""") == {
                    "active": "kaoyan", "homeHidden": True,
                    "archiveHidden": False, "heading": "考研经历"
                }
                page.wait_for_load_state("networkidle")
                Handler.script_delay = 0
                page.goto(base + "/articles/demo-postgraduate.html", wait_until="networkidle")
                Handler.script_delay = 2
                page.locator('.article-back').click(no_wait_after=True)
                page.wait_for_url('**/?category=kaoyan', wait_until='commit')
                page.wait_for_selector('#archive-intro')
                assert page.locator('#category-nav [aria-current="page"]').get_attribute('data-category') == 'kaoyan'
                assert page.locator('#home-intro').is_hidden()
            finally:
                Handler.script_delay = 0
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(base + "/?view=all", wait_until="networkidle")
            page.evaluate("window.__sameDocument = true")
            page.locator('#category-nav [data-category="career"]').click()
            page.wait_for_function("location.search === '?category=career' && !document.querySelector('#archive-section').hidden")
            assert page.evaluate("window.__sameDocument")
            page.keyboard.press("Control+k")
            assert page.locator('#search-dialog').evaluate("el => el.open")
            page.locator('#search').fill('no-matching-story-987654321')
            page.wait_for_function("document.querySelector('#search-results').textContent.includes('没有找到匹配内容')")
            page.keyboard.press("Escape")
            assert not page.locator('#search-dialog').evaluate("el => el.open")
            page.wait_for_function("document.querySelector('#search').value === ''")
            page.locator('#category-nav [data-category="all"]').click()
            page.wait_for_function("location.search === '?view=all'")
            page.go_back()
            assert page.url.endswith('?category=career')
            assert page.locator('.article-item:visible').count() == 1
            page.go_forward()
            assert page.url.endswith('?view=all')
            page.goto(base + '/?category=kaoyan', wait_until='networkidle')
            page.locator('.search-open').click()
            page.locator('#search').fill('周同学')
            page.wait_for_function("document.querySelector('#search-results').textContent.includes('没有找到匹配内容')")
            page.locator('.search-close').click()
            page.locator(".article-item:visible h3 a").first.click()
            page.wait_for_load_state("networkidle")
            page.locator(".article-back").click()
            page.wait_for_load_state("networkidle")
            assert errors == [], errors
            context.close()
            context = browser.new_context(java_script_enabled=False)
            page = context.new_page()
            for route in ("/", "/" + articles[0]["url"]):
                page.goto(base + PREFIX + route)
                assert page.locator(".footer-links a").count() == 6
                assert page.locator("#category-nav [data-category]").count() == 5
                assert page.locator("h1").count() >= 1
                if route == "/":
                    assert page.locator(".article-item:visible").count() == len(articles)
            context.close()
            # A submitted Markdown story should preview as its published counterpart.
            # Inspect real production-rendered HTML, not an imagined CSS fixture.
            demo_source = (ROOT / "content/demo/demo-postgraduate.md").read_text(encoding="utf-8")
            demo_body = demo_source.split('---', 2)[2].strip()
            context = browser.new_context(reduced_motion="reduce")
            page = context.new_page()
            page.goto(base + PREFIX + "/articles/demo-postgraduate.html", wait_until="networkidle")
            def appearance(selector):
                return page.locator(selector).first.evaluate("""el => {
                    const style = getComputedStyle(el);
                    return {
                        fontSize: style.fontSize,
                        lineHeight: style.lineHeight,
                        color: style.color,
                        marginTop: style.marginTop,
                        marginBottom: style.marginBottom
                    };
                }""")
            expected = {
                "title": page.locator(".article-page > h1").inner_text(),
                "byline": page.locator(".article-page > .article-byline").inner_text(),
                "headings": page.locator(".article-body h1, .article-body h2, .article-body h3").all_inner_texts(),
                "toc": page.locator(".article-toc a").all_inner_texts(),
                "toc_urls": page.locator(".article-toc a").evaluate_all("items => items.map(item => item.getAttribute(\'href\'))"),
                "body": appearance(".article-body"),
                "h2": appearance(".article-body h2"),
                "title_style": appearance(".article-page > h1"),
            }
            page.route("**/assets/js/submission-config.js*", lambda route: route.fulfill(
                content_type="application/javascript",
                body="window.UEM_SUBMISSION_CONFIG={enabled:false};"
            ))
            page.goto(base + PREFIX + "/submit.html", wait_until="networkidle")
            page.locator("#category").select_option("kaoyan")
            page.locator("#author").fill("林同学")
            page.locator("#year").fill("2026")
            page.locator("#college").fill("某学院")
            page.locator("#major").fill("某专业")
            page.locator("#destination").fill("某理工类高校")
            page.locator("#program").fill("安全工程相关专业")
            page.locator("#body").fill(demo_body)
            page.locator("#preview-button").click()
            assert page.locator("#preview").is_visible()
            assert page.locator("#preview-text > h1").inner_text() == expected["title"]
            assert page.locator("#preview-text > .article-byline").inner_text() == expected["byline"]
            assert page.locator("#preview-text .article-body h1, #preview-text .article-body h2, #preview-text .article-body h3").all_inner_texts() == expected["headings"]
            assert page.locator("#preview-text .article-toc a").all_inner_texts() == expected["toc"]
            assert page.locator("#preview-text .article-toc a").evaluate_all("items => items.map(item => item.getAttribute(\'href\'))") == expected["toc_urls"]
            assert appearance("#preview-text .article-body") == expected["body"]
            assert appearance("#preview-text .article-body h2") == expected["h2"]
            assert appearance("#preview-text > h1") == expected["title_style"]
            context.close()
            # A phrase found only in the article body must be searchable.
            context = browser.new_context()
            page = context.new_page()
            page.goto(base + "/?view=all", wait_until="networkidle")
            page.locator(".search-open").click()
            page.locator("#search").fill("理工")
            page.wait_for_function("document.querySelectorAll('#search-results li a').length === 2")
            page.locator("#search").fill("林同学")
            page.wait_for_function("document.querySelectorAll('#search-results li a').length === 1")
            assert page.locator("#search-results .search-title mark").count() == 1
            page.locator("#search").fill("2026")
            page.wait_for_function("document.querySelectorAll('#search-results li a').length === 4")
            assert page.locator("#search-results .search-match mark").count() == 4
            assert page.locator("#search-results .search-match").first.inner_text().startswith("2026 届")
            page.locator("#search").fill("某学院")
            page.wait_for_function("document.querySelector('#search-results .search-match mark')?.textContent === '某学院'")
            assert page.locator("#search-results li a").count() == 4
            assert page.locator("#search-results .search-match mark").count() == 4
            page.locator("#search").fill("推荐信")
            page.locator("#search-results li a").first.wait_for(state="visible")
            assert page.locator("#search-results li a").count() == 1
            assert "香港某高校" in page.locator("#search-results li a").inner_text()
            assert "推荐信" in page.locator("#search-results .search-match").inner_text()
            assert page.locator("#search-results .search-match mark").count() == 1
            assert page.locator("#search-results .search-title mark").count() == 0
            page.locator(".search-close").click()
            page.locator("#year-trigger").click()
            page.locator("#year-options [data-value='2026']").click()
            assert page.locator(".article-item:visible").count() > 0
            assert page.locator(".article-item:visible").evaluate_all(
                "items => items.every(item => item.dataset.year === '2026')"
            )
            page.locator(".search-open").click()
            page.locator("#search").fill("推荐信")
            page.locator("#search-results li a").first.wait_for(state="visible")
            assert page.locator("#search-results li a").count() == 1
            page.locator("#search").fill("")
            assert page.locator("#search-results").is_hidden()
            context.close()
            # Mocked public mode: confirm the complete browser payload/feedback
            # without contacting Cloudflare or opening an actual GitHub Issue.
            context = browser.new_context()
            page = context.new_page()
            submissions = []
            page.route("**/assets/js/submission-config.js*", lambda route: route.fulfill(
                content_type="application/javascript",
                body="window.UEM_SUBMISSION_CONFIG={enabled:true,apiEndpoint:'https://uem-feiyue-submissions.futseyi.workers.dev/submit',turnstileSiteKey:'test-site-key'};"
            ))
            page.route("https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit",
                       lambda route: route.fulfill(content_type="application/javascript",
                           body="window.turnstile={render:(_,o)=>{setTimeout(()=>o.callback(),0);return 'test-widget';},getResponse:()=> 'test-token',reset:()=>{}};"))
            def accept_submission(route):
                submissions.append(route.request.post_data_json)
                route.fulfill(status=201, content_type="application/json",
                              headers={"Access-Control-Allow-Origin": base},
                              body=json.dumps({"ok": True, "issueUrl": "https://github.com/UEM-Feiyue/UEM-Feiyue.github.io/issues/57"}))
            page.route("https://uem-feiyue-submissions.futseyi.workers.dev/submit", accept_submission)
            page.goto(base + "/submit.html", wait_until="networkidle")
            page.wait_for_selector("#body")
            page.locator("#category").select_option("career")
            page.locator("#author").fill("测试同学")
            page.locator("#year").fill("2026")
            page.locator("#college").fill("某学院")
            page.locator("#major").fill("某专业")
            page.locator("#destination").fill("某公司")
            page.locator("#body").fill("## 完整经历\\n\\n测试内容")
            page.wait_for_function("!document.querySelector('#submit-button').disabled", timeout=10000)
            page.locator("#submit-button").click()
            page.get_by_text("查看投稿记录").wait_for()
            assert page.locator("#submission-status").get_attribute("data-state") == "success"
            assert page.locator("#submit-button").inner_text() == "投稿分享"
            assert len(submissions) == 1
            assert submissions[0]["category"] == "career"
            assert submissions[0]["college"] == "某学院"
            assert submissions[0]["major"] == "某专业"
            assert submissions[0]["turnstileToken"] == "test-token"
            assert page.locator("#author").input_value() == ""
            context.close()
            # The actual preview server must not load Turnstile on localhost.
            preview_server = ThreadingHTTPServer(("127.0.0.1", 0), partial(PreviewHandler, directory=str(ROOT / "_site")))
            preview_worker = Thread(target=preview_server.serve_forever, daemon=True)
            preview_worker.start()
            try:
                context = browser.new_context()
                page = context.new_page()
                cloudflare_requests = []
                page.on("request", lambda request: cloudflare_requests.append(request.url) if "challenges.cloudflare.com" in request.url else None)
                page.goto(f"http://127.0.0.1:{preview_server.server_port}/submit.html", wait_until="networkidle")
                page.locator("#body").wait_for()
                assert page.locator("#submit-button").is_disabled()
                assert "本地预览" in page.locator("#submission-status").inner_text()
                assert cloudflare_requests == []
                context.close()
            finally:
                preview_server.shutdown()
                preview_worker.join()
                preview_server.server_close()
            context = browser.new_context(viewport={"width": 390, "height": 844})
            page = context.new_page()
            page.goto(base + "/articles/demo-postgraduate.html", wait_until="networkidle")
            toc = page.locator(".article-toc")
            toc.locator("summary").click()
            assert toc.get_attribute("open") is not None
            assert toc.locator("a.is-active").count() == 0
            assert toc.locator(".article-toc-panel").evaluate("el => getComputedStyle(el).transitionDuration") != "0s"
            page.wait_for_timeout(300)
            toc.locator("summary").click()
            page.wait_for_function("!document.querySelector('.article-toc').open")
            toc.locator("summary").click()
            toc.locator("a").last.click()
            page.wait_for_function("[...document.querySelectorAll('.article-toc a')].at(-1)?.classList.contains('is-active')")
            page.wait_for_function("""() => {
                const link = [...document.querySelectorAll('.article-toc a')].at(-1);
                const target = document.getElementById(decodeURIComponent(link.hash.slice(1)));
                const top = Math.min(target.getBoundingClientRect().top + scrollY - 24, document.documentElement.scrollHeight - innerHeight);
                return Math.abs(scrollY - top) < 4;
            }""")
            context.close()
            browser.close()
    finally:
        server.shutdown()
        worker.join()
        server.server_close()


if __name__ == "__main__":
    main()
