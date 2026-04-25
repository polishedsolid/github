from urllib.parse import urlparse


def screenshot_images(page_url: str, failed_urls: list[str]) -> dict[str, bytes]:
    """
    Use Playwright to screenshot image elements for URLs that failed direct download.
    Returns a mapping of {original_url: png_bytes}.
    """
    if not failed_urls:
        return {}

    results: dict[str, bytes] = {}

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return results

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        try:
            page.goto(page_url, wait_until="domcontentloaded", timeout=30_000)
            page.wait_for_load_state("networkidle", timeout=10_000)
        except Exception:
            try:
                page.goto(page_url, wait_until="domcontentloaded", timeout=30_000)
            except Exception:
                browser.close()
                return results

        for url in failed_urls:
            png_bytes = _screenshot_element(page, url)
            if png_bytes:
                results[url] = png_bytes

        browser.close()

    return results


def _screenshot_element(page, url: str) -> bytes | None:
    path = urlparse(url).path
    selectors = [
        f'img[src="{url}"]',
        f'img[data-src="{url}"]',
        f'img[src*="{path}"]',
        f'img[data-src*="{path}"]',
    ]
    for selector in selectors:
        try:
            locator = page.locator(selector).first
            if locator.count() == 0:
                continue
            locator.wait_for(state="visible", timeout=3_000)
            png = locator.screenshot(type="png")
            if png:
                return png
        except Exception:
            continue
    return None
