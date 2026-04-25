import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config import MAX_IMAGE_SIZE_BYTES, REQUEST_TIMEOUT, USER_AGENT


def make_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=2,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update({"User-Agent": USER_AGENT})
    return session


def fetch_image(session: requests.Session, url: str, referer: str = "") -> bytes | None:
    headers = {}
    if referer:
        headers["Referer"] = referer
    try:
        resp = session.get(url, timeout=REQUEST_TIMEOUT, stream=True, headers=headers)
        resp.raise_for_status()
        ct = resp.headers.get("Content-Type", "")
        if "image/" not in ct and "octet-stream" not in ct:
            return None
        data = b""
        for chunk in resp.iter_content(chunk_size=65536):
            data += chunk
            if len(data) > MAX_IMAGE_SIZE_BYTES:
                return None
        return data if data else None
    except Exception:
        return None
