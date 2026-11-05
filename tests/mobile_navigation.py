"""Mobile WebKit regression for stable UEM headers and navigation."""
from functools import partial
from http.server import ThreadingHTTPServer
from threading import Thread

from playwright.sync_api import sync_playwright

from browser_smoke import Handler, PREFIX, ROOT


def main():
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        partial(Handler, directory=str(ROOT / "_site")),
    )
    Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_port}{PREFIX}"
    try:
        with sync_playwright() as playwright:
            browser = playwright.webkit.launch()
            for width in (320, 390):
                for theme in ("light", "dark"):
                    context = browser.new_context(
                        viewport={"width": width, "height": 780},
                        device_scale_factor=3, is_mobile=True, has_touch=True,
                        reduced_motion="no-preference",
                    )
                    context.add_init_script(
                        f"localStorage.setItem('uem-theme', '{theme}')"
                    )
                    page = context.new_page()
                    # Keep the navigation regression offline: the production Turnstile
                    # widget intentionally refuses cross-origin localhost iframes.
                    page.route("**/assets/js/submission-config.js*", lambda route: route.fulfill(
                        content_type="application/javascript",
                        body="window.UEM_SUBMISSION_CONFIG={enabled:false};",
                    ))
                    errors = []
                    page.on("pageerror", lambda error: errors.append(str(error)))
                    page.goto(base + "/", wait_until="networkidle")
                    assert page.locator(".topbar").is_visible()
                    assert page.locator(".mobile-brand-logo").is_visible()
                    assert page.locator(".menu-button").is_visible()
                    assert page.locator(".topbar").evaluate(
                        "el => getComputedStyle(el).position === 'sticky'"
                    )
                    assert page.locator(".campus-banner").evaluate(
                        "el => Math.abs(el.getBoundingClientRect().top - "
                        "document.querySelector('.topbar').getBoundingClientRect().bottom) <= 1"
                    )
                    page.locator("#menu-toggle").click()
                    assert page.locator(".shell").evaluate(
                        "el => el.classList.contains('menu-open')"
                    )
                    assert page.locator("#sidebar").is_visible()
                    assert page.locator("#menu-toggle").get_attribute(
                        "aria-expanded"
                    ) == "true"
                    # Observe the *outgoing document* after site.js handles the
                    # click. Previous tests only inspected the destination,
                    # missing the visible residual-panel flash before navigation.
                    page.evaluate("""() => {
                        document.addEventListener('click', event => {
                            if (!event.target.closest('#category-nav a.nav-contribute')) return;
                            const menu = document.querySelector('#sidebar');
                            const shell = document.querySelector('.shell');
                            sessionStorage.setItem('outgoing-menu-state', JSON.stringify({
                                reset: shell.classList.contains('nav-reset'),
                                open: shell.classList.contains('menu-open'),
                                panelOpen: menu.classList.contains('open'),
                                inert: menu.inert,
                                expanded: document.querySelector('#menu-toggle').getAttribute('aria-expanded'),
                                transition: getComputedStyle(menu).transitionDuration
                            }));
                        });
                    }""")
                    page.locator("#category-nav a.nav-contribute").click()
                    page.wait_for_url("**/submit.html")
                    outgoing = page.evaluate(
                        "() => JSON.parse(sessionStorage.getItem('outgoing-menu-state'))"
                    )
                    assert outgoing == {
                        "reset": True, "open": False, "panelOpen": False,
                        "inert": True, "expanded": "false", "transition": "0s"
                    }, outgoing
                    assert page.locator(".mobile-brand-logo").is_visible()
                    assert page.locator(".menu-button").is_visible()
                    assert page.locator("#menu-toggle").get_attribute(
                        "aria-expanded"
                    ) == "false"
                    assert page.locator("#sidebar").evaluate("el => el.inert")
                    assert page.locator(".campus-banner").is_visible()
                    page.go_back(wait_until="networkidle")
                    assert page.locator("#menu-toggle").get_attribute(
                        "aria-expanded"
                    ) == "false"
                    assert page.locator(".mobile-brand-logo").is_visible()
                    assert not errors, errors
                    context.close()
                    print(f"UEM WebKit mobile navigation passed: {width}px, {theme}")
            browser.close()
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()
