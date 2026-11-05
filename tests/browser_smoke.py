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
                    assert page.locator("#category-nav [data-category]").count() == 5
                    assert page.locator(".site-footer").count() == 1
                    if width <= 900:
                        assert page.locator("#sidebar").evaluate("el => el.inert")
                        page.locator("#menu-toggle").click()
                        assert page.locator("#menu-toggle").get_attribute("aria-expanded") == "true"
                        assert not page.locator("#sidebar").evaluate("el => el.inert")
                        page.keyboard.press("Escape")
                        assert page.locator("#menu-toggle").get_attribute("aria-expanded") == "false"
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
                    page.locator("#search").fill("no-matching-story-987654321")
                    assert page.locator(".empty-state").is_visible()
                    page.locator("#search").fill(articles[0]["author"])
                    assert page.locator(".article-item:visible").count() > 0
                    page.locator(".article-item:visible h3 a").first.click()
                    page.wait_for_selector(".article-body")
                    assert page.locator(".demo-badge").is_visible() == articles[0]["demo"]
                    assert page.locator(".article-toc").count() <= 1
                    assert page.locator("#category-nav [aria-current='page']").count() == 1
                    assert page.locator(".site-footer").count() == 1
                    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 2")
                    page.go_back(wait_until="networkidle")
                    assert page.locator("#search").is_visible()
                    assert page.locator("#search").input_value() == articles[0]["author"]
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
                    page.locator("#body").fill("## Heading\n\n**Test body**\n\n<script>window.__unsafe = true</script>")
                    page.locator("#contact").fill("do-not-save@example.invalid")
                    page.locator("#preview-button").click()
                    assert page.locator("#preview").is_visible()
                    assert page.locator("#preview .article-body strong").inner_text() == "Test body"
                    assert not page.evaluate("Boolean(window.__unsafe)")
                    assert "公开 GitHub Issue" in page.locator(".notice").inner_text()
                    assert page.locator("#submit-button").is_visible()
                    assert page.locator("#submit-button").is_disabled()
                    assert page.locator("#submit-button").inner_text() == "投稿分享"
                    assert "暂未开放" in page.locator("#submission-status").inner_text()
                    page.reload(wait_until="networkidle")
                    page.wait_for_selector("#body")
                    assert page.locator("#author").input_value() == "Browser test"
                    assert page.locator("#contact").input_value() == ""
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
