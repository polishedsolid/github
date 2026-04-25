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


def build_zip(
    page_url: str,
    on_progress: callable = None,
) -> tuple[io.BytesIO, int]:
    def log(msg: str) -> None:
        if on_progress:
            on_progress(msg)

    log("ページを取得して画像URLを収集中...")
    image_urls, favicon_urls = extract_image_urls(page_url)
    candidates = [
        url for url in image_urls[:MAX_IMAGES]
        if not is_favicon_by_url(url) and not is_favicon_by_link_rel(url, favicon_urls)
    ]
    log(f"候補画像: {len(candidates)} 件（ファビコン除外済み）")

    session = make_session()
    buf = io.BytesIO()
    count = 0
    seen_names: dict[str, int] = {}
    failed_urls: list[str] = []

    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for i, url in enumerate(candidates, 1):
            log(f"  [{i}/{len(candidates)}] ダウンロード中: {url[:80]}")
            image_bytes = fetch_image(session, url, referer=page_url)
            if image_bytes is None:
                log(f"    → 失敗（スクリーンショットで再試行予定）")
                failed_urls.append(url)
                continue

            ok, reason = check_dimensions(image_bytes)
            if not ok:
                log(f"    → 除外: {reason}")
                continue

            filename = _safe_filename(url, seen_names)
            zf.writestr(filename, image_bytes)
            count += 1
            log(f"    → 追加: {filename}")

        if failed_urls:
            log(f"\nPlaywright で {len(failed_urls)} 件をスクリーンショット取得中...")
            screenshots = screenshot_images(page_url, failed_urls)
            for url, png_bytes in screenshots.items():
                ok, reason = check_dimensions(png_bytes)
                if not ok:
                    log(f"    → 除外: {reason}")
                    continue
                path = urlparse(url).path
                base_name = os.path.basename(path) or "image"
                base_name = os.path.splitext(base_name)[0] or "image"
                filename = _safe_filename(base_name + "_screenshot.png", seen_names)
                zf.writestr(filename, png_bytes)
                count += 1
                log(f"    → スクショ追加: {filename}")

    return buf, count
