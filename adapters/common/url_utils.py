# adapters/common/url_utils.py (minimal)
from urllib.parse import urlparse, urlsplit, urlunsplit
import hashlib, re
from typing import Optional
import unicodedata

def canonicalize_url(url: str) -> str:
    """Normalize scheme/host; strip query/fragment for known hosts."""
    try:
        u = urlsplit(url)
    except Exception:
        return url
    scheme = "https"
    netloc = u.netloc.lower()
    path = u.path.rstrip("/")
    if "mako.co.il" in netloc or "c14.co.il" in netloc:
        return urlunsplit((scheme, netloc, path, "", ""))  # drop query/fragment
    return urlunsplit((scheme, netloc, path, u.query, u.fragment))

def extract_url_id(url: str, source: Optional[str] = None) -> Optional[str]:
    """Return a stable per-site ID or None; avoid fragile numeric tails for mako."""
    host = ""
    try:
        host = urlparse(url).netloc.lower()
    except Exception:
        pass
    s = (source or "").lower()

    # C14: numeric ID in /article/<digits>
    if "c14.co.il" in host or s == "c14":
        m = re.search(r"/article/(\d+)", url)
        return m.group(1) if m else None

    # mako / N12: take the token right after 'Article-' up to '.htm'
    if "mako.co.il" in host or s in {"n12", "mako"}:
        m = re.search(r"Article-([A-Za-z0-9]+)\.htm", url)
        return m.group(1) if m else None

    return None

def short_hash(text: str, n: int = 10) -> str:
    return hashlib.sha1((text or "").encode("utf-8")).hexdigest()[:n]

def build_record_key(source: str, url: str, url_id: Optional[str]) -> str:
    """Prefer site ID; otherwise use a short hash of the canonical URL."""
    src = (source or "").lower().strip()
    if url_id:
        return f"{src}:{url_id}"
    h = hashlib.sha1(canonicalize_url(url).encode("utf-8")).hexdigest()[:12]
    return f"{src}:{h}"

# analysis/hygiene_utils.py
WS_RE = re.compile(r"\s+")


#@@@@@@@@@ KEEP GOING FROM HERE @@@@@@@@@
def normalize_text(text: str) -> str:
    """
    Normalize whitespace & punctuation in titles/summaries:
    - NFC normalize diacritics
    - Collapse multiple spaces/tabs/newlines
    - Replace "....." with a single ellipsis
    - Trim leading/trailing whitespace
    """
    if not text:
        return ""
    s = unicodedata.normalize("NFC", text)
    s = re.sub(r"\s+", " ", s)              # collapse whitespace
    s = re.sub(r"\.{3,}", "…", s)           # replace 3+ dots with ellipsis
    return s.strip()
