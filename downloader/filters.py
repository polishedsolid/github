from __future__ import annotations

import io
import re
from xml.etree import ElementTree as ET

from PIL import Image, UnidentifiedImageError

from config import BANNER_ASPECT_RATIO, BANNER_MAX_HEIGHT, BANNER_MIN_WIDTH, MIN_HEIGHT, MIN_WIDTH

FAVICON_URL_PATTERNS = [
    re.compile(r"favicon\.ico$", re.I),
    re.compile(r"favicon[-_]?\d*\.(png|ico|svg|gif)$", re.I),
    re.compile(r"apple[-_]touch[-_]icon", re.I),
    re.compile(r"/icons?/.*\.(png|ico|svg)$", re.I),
    re.compile(r"site[-_]logo\.(png|ico)$", re.I),
]


def is_favicon_by_url(url: str) -> bool:
    from urllib.parse import urlparse
    path = urlparse(url).path
    return any(p.search(path) for p in FAVICON_URL_PATTERNS)


def is_favicon_by_link_rel(url: str, favicon_urls: set[str]) -> bool:
    return url in favicon_urls


def _get_svg_dimensions(data: bytes) -> tuple[int, int] | None:
    try:
        root = ET.fromstring(data.decode("utf-8", errors="replace"))
        tag = root.tag
        if "}" in tag:
            tag = tag.split("}")[1]
        if tag.lower() != "svg":
            return None
        w = root.get("width", "").replace("px", "").strip()
        h = root.get("height", "").replace("px", "").strip()
        try:
            return int(float(w)), int(float(h))
        except (ValueError, TypeError):
            pass
        vb = root.get("viewBox", "").strip()
        parts = vb.split()
        if len(parts) == 4:
            return int(float(parts[2])), int(float(parts[3]))
    except Exception:
        pass
    return None


def check_dimensions(image_bytes: bytes) -> tuple[bool, str]:
    """Return (passes, reason). passes=True means include the image."""
    # Try Pillow first
    try:
        img = Image.open(io.BytesIO(image_bytes))
        width, height = img.size
    except UnidentifiedImageError:
        # May be SVG
        dims = _get_svg_dimensions(image_bytes)
        if dims is None:
            # Unknown format — include it rather than discard
            return True, "unknown_format_included"
        width, height = dims
    except Exception:
        return False, "unreadable"

    if width < MIN_WIDTH or height < MIN_HEIGHT:
        return False, f"too_small ({width}x{height})"

    if height == 0:
        return False, "zero_height"

    aspect = width / height
    if aspect > BANNER_ASPECT_RATIO:
        return False, f"banner_aspect ({aspect:.1f}:1)"

    if width >= BANNER_MIN_WIDTH and height <= BANNER_MAX_HEIGHT:
        return False, f"banner_dims ({width}x{height})"

    return True, "ok"
