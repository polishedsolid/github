import io
import os
import zipfile
from urllib.parse import urlparse

from config import MAX_IMAGES
from downloader.extractor import FetchError, extract_image_urls
from downloader.fetcher import fetch_image, make_session
from downloader.filters import check_dimensions, is_favicon_by_link_rel, is_favicon_by_url
from downloader.screenshot import screenshot_images


def _safe_filename(url: str, seen: dict[str, int]) -> str:
    path = urlparse(url).path
    name = os.path.basename(path) or "image"
    name = name.split("?")[0]
    if "." not in name:
        name += ".jpg"
    base, ext = os.path.splitext(name)
    key = name.lower()
    if key in seen:
        seen[key] += 1
        name = f"{base}_{seen[key]}{ext}"
    else:
        seen[key] = 0
    return name


def build_zip(page_url: str) -> tuple[io.BytesIO, int]:
    image_urls, favicon_urls = extract_image_urls(page_url)

    session = make_session()
    buf = io.BytesIO()
    count = 0
    seen_names: dict[str, int] = {}
    failed_urls: list[str] = []

    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for url in image_urls[:MAX_IMAGES]:
            if is_favicon_by_url(url):
                continue
            if is_favicon_by_link_rel(url, favicon_urls):
                continue

            image_bytes = fetch_image(session, url, referer=page_url)
            if image_bytes is None:
                failed_urls.append(url)
                continue

            ok, _ = check_dimensions(image_bytes)
            if not ok:
                continue

            filename = _safe_filename(url, seen_names)
            zf.writestr(filename, image_bytes)
            count += 1

        # Playwright fallback for failed downloads
        if failed_urls:
            screenshots = screenshot_images(page_url, failed_urls)
            for url, png_bytes in screenshots.items():
                ok, _ = check_dimensions(png_bytes)
                if not ok:
                    continue
                path = urlparse(url).path
                base_name = os.path.basename(path) or "image"
                base_name = os.path.splitext(base_name)[0] or "image"
                filename = _safe_filename(base_name + "_screenshot.png", seen_names)
                zf.writestr(filename, png_bytes)
                count += 1

    return buf, count
