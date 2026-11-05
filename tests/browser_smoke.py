"""Exercise the complete UEM artifact, including its Pages project subpath."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from threading import Thread
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PREFIX = "/UEM-Feiyue.github.io"


class Handler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        if path.startswith(PREFIX + "/"):
            path = path[len(PREFIX):]
        return super().translate_path(path)

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
            for width in (320, 390, 900, 901, 1440):
                for theme in ("light", "dark"):
                    context = browser.new_context(viewport={"width": width, "height": 900}, reduced_motion="reduce")
                    context.add_init_script(f"localStorage.setItem('uem-theme', '{theme}')")
                    page = context.new_page()
                    errors = []
                    page.on("pageerror", lambda error: errors.append(str(error)))
                    page.goto(base + PREFIX + "/", wait_until="networkidle")
                    assert page.locator("h1:visible").count() == 1
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
                    assert background["contentBackground"] != "rgba(0, 0, 0, 0)"
                    # Logo on the current homepage must scroll even when the URL
                    # remains unchanged. The previous same-URL guard swallowed it.
                    brand = ".mobile-brand" if width <= 900 else ".sidebar .brand"
                    assert page.locator(brand).is_visible()
                    assert page.locator(brand + " img").evaluate(
                        "el => getComputedStyle(el).maskImage.includes('radial-gradient')"
                    )
                    page.evaluate("window.scrollTo({top:document.documentElement.scrollHeight,behavior:'instant'})")
                    page.wait_for_function("scrollY > 100")
                    page.locator(brand).click()
                    page.wait_for_function("scrollY <= 2")
                    assert page.url.rstrip("/").endswith(PREFIX)
                    assert page.locator("#category-nav [data-category]").count() == 5
                    assert page.locator(".site-footer").count() == 1
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
                        assert page.locator("#sidebar").evaluate("el => getComputedStyle(el).position === 'fixed'")
                        assert page.locator("#sidebar").evaluate("el => el.getBoundingClientRect().top >= document.querySelector('.topbar').getBoundingClientRect().bottom")
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
                    page.keyboard.press("Escape")
                    assert not page.locator("#year-options").evaluate("el => el.matches(':popover-open')")
                    page.locator("#year-trigger").click()
                    page.locator("#year-options [data-value='all']").click()
                    assert page.locator("#year-filter").input_value() == "all"
                    page.locator("#search").fill("no-matching-story-987654321")
                    page.wait_for_function("document.querySelector('#search-status').textContent.includes('没有找到匹配内容')")
                    assert page.locator(".empty-state").is_visible()
                    page.locator("#search").fill(articles[0]["author"])
                    page.wait_for_function("document.querySelector('#search-status').textContent.includes('全文搜索结果')")
                    assert page.locator(".article-item:visible").count() > 0
                    page.locator(".article-item:visible h3 a").first.click()
                    page.wait_for_selector(".article-body")
                    assert page.locator(".demo-badge").is_visible() == articles[0]["demo"]
                    assert page.locator(".article-toc").count() <= 1
                    if page.locator(".article-toc").count():
                        assert page.locator(".article-toc").evaluate("el => el.tagName") == "DETAILS"
                        page.locator(".article-toc summary").click()
                        assert page.locator(".article-toc").get_attribute("open") is not None
                        assert page.locator(".article-toc a").first.is_visible()

                    assert page.locator("#category-nav [aria-current='page']").count() == 1
                    assert page.locator(".site-footer").count() == 1
                    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 2")
                    page.go_back(wait_until="networkidle")
                    assert page.locator("#search").is_visible()
                    assert page.locator("#search").input_value() == articles[0]["author"]
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
                        assert page.locator("#search").is_visible()
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
                    page.locator("#destination").fill("Example institution")
                    assert page.locator("#year").evaluate("el => el.getBoundingClientRect().width < 120")
                    assert "hello@example.com" in page.locator("#contact").get_attribute("placeholder")
                    assert page.locator("#body").evaluate("el => el.getBoundingClientRect().height >= 240")
                    page.locator("#body").fill(("## 复盘\\n\\n" + "过程很重要，经验可以复用。\\n") * 25)
                    assert page.locator("#body").evaluate("el => el.scrollHeight <= el.clientHeight + 3")
                    page.locator("#body").fill("")
                    page.locator(".demo-actions button").filter(has_text="载入示例").click()
                    page.wait_for_function("document.querySelector('#body').value.startsWith('## ')")
                    assert page.locator(".markdown-help").get_attribute("open") is not None
                    assert page.locator(".markdown-preview").is_hidden()
                    assert page.locator("#body").is_visible()
                    assert "Markdown" in page.locator(".markdown-help").inner_text()
                    assert "## 小标题" in page.locator(".markdown-help").inner_text()
                    page.locator("#body").fill("")
                    page.locator("#body").fill("## Heading\n\n**Test body**\n\n<script>window.__unsafe = true</script>")
                    page.locator("#contact").fill("do-not-save@example.invalid")
                    page.locator("#preview-button").click()
                    assert page.locator("#preview").is_visible()
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
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(base + "/?view=all", wait_until="networkidle")
            page.evaluate("window.__sameDocument = true")
            page.locator('#category-nav [data-category="career"]').click()
            page.wait_for_function("location.search === '?category=career' && !document.querySelector('#archive-section').hidden")
            assert page.evaluate("window.__sameDocument")
            page.locator('#search').fill('no-matching-story-987654321')
            page.locator('#category-nav [data-category="all"]').click()
            page.wait_for_function("location.search === '?view=all' && document.querySelector('#search').value === ''")
            page.go_back()
            assert page.locator('#search').input_value() == 'no-matching-story-987654321'
            assert page.locator('#empty-state').is_visible()
            page.go_forward()
            assert page.locator('#search').input_value() == ''
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
            page.locator("#search").fill("推荐信")
            page.wait_for_function("document.querySelector('#search-status').textContent.includes('全文搜索结果')")
            assert page.locator(".article-item:visible").count() == 1
            assert "陈同学" in page.locator(".article-item:visible").inner_text()
            assert "推荐信" in page.locator(".article-item:visible .article-excerpt").inner_text()
            page.locator("#year-trigger").click()
            page.locator("#year-options [data-value='2026']").click()
            assert page.locator(".article-item:visible").count() == 1
            page.locator("#search").fill("")
            assert page.locator(".article-item:visible").count() == len(articles)
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
            page.locator("#destination").fill("某公司")
            page.locator("#body").fill("## 完整经历\\n\\n测试内容")
            page.wait_for_function("!document.querySelector('#submit-button').disabled", timeout=10000)
            page.locator("#submit-button").click()
            page.get_by_text("查看投稿记录").wait_for()
            assert page.locator("#submission-status").get_attribute("data-state") == "success"
            assert page.locator("#submit-button").inner_text() == "投稿分享"
            assert len(submissions) == 1
            assert submissions[0]["category"] == "career"
            assert submissions[0]["turnstileToken"] == "test-token"
            assert page.locator("#author").input_value() == ""
            context.close()
            browser.close()
    finally:
        server.shutdown()
        worker.join()
        server.server_close()


if __name__ == "__main__":
    main()
