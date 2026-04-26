from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from config import REQUEST_TIMEOUT, USER_AGENT


class FetchError(Exception):
    pass


def _make_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    return session


def _parse_srcset(srcset: str) -> str | None:
    candidates = []
    for part in srcset.split(","):
        part = part.strip()
        tokens = part.split()
        if tokens:
            candidates.append(tokens[0])
    return candidates[-1] if candidates else None


def extract_image_urls(page_url: str) -> tuple[list[str], set[str]]:
    session = _make_session()
    try:
        resp = session.get(
            page_url,
            timeout=REQUEST_TIMEOUT,
            headers={"Referer": page_url},
        )
        resp.raise_for_status()
    except requests.exceptions.MissingSchema:
        raise FetchError(f"Invalid URL: {page_url}")
    except requests.exceptions.ConnectionError:
        raise FetchError(f"Could not connect to {page_url}. Check the URL.")
    except requests.exceptions.Timeout:
        raise FetchError("Request timed out. The site may be too slow.")
    except requests.exceptions.TooManyRedirects:
        raise FetchError("Too many redirects. Possible redirect loop.")
    except requests.exceptions.HTTPError as e:
        raise FetchError(f"HTTP {e.response.status_code}: {e.response.reason}")
    except requests.exceptions.SSLError:
        raise FetchError("SSL certificate error. The site's certificate may be invalid.")
    except Exception as e:
        raise FetchError(f"Could not fetch page: {e}")

    soup = BeautifulSoup(resp.text, "lxml")

    favicon_urls: set[str] = set()
    favicon_rels = {"icon", "shortcut icon", "apple-touch-icon", "apple-touch-icon-precomposed", "mask-icon"}
    for link in soup.find_all("link", rel=True):
        rel_values = {r.lower() for r in link.get("rel", [])}
        if rel_values & favicon_rels:
            href = link.get("href", "").strip()
            if href:
                favicon_urls.add(urljoin(page_url, href))

    candidate_urls: list[str] = []
    seen: set[str] = set()

    def add(url: str) -> None:
        if not url or url.startswith("data:"):
            return
        abs_url = urljoin(page_url, url)
        parsed = urlparse(abs_url)
        if parsed.scheme not in ("http", "https"):
            return
        if abs_url not in seen:
            seen.add(abs_url)
            candidate_urls.append(abs_url)

    # <img> tags — multiple attributes for lazy loading
    for img in soup.find_all("img"):
        for attr in ("src", "data-src", "data-lazy", "data-original", "data-image", "data-lazy-src"):
            val = img.get(attr, "").strip()
            if val:
                add(val)
                break
        srcset = img.get("srcset", "").strip()
        if srcset:
            url = _parse_srcset(srcset)
            if url:
                add(url)

    # <picture><source> tags
    for source in soup.find_all("source"):
        srcset = source.get("srcset", "").strip()
        if srcset:
            url = _parse_srcset(srcset)
            if url:
                add(url)

    # OGP image
    og_image = soup.find("meta", property="og:image")
    if og_image:
        add(og_image.get("content", "").strip())

    # <link rel="image_src">
    for link in soup.find_all("link", rel=re.compile(r"image_src", re.I)):
        add(link.get("href", "").strip())

    return candidate_urls, favicon_urls
