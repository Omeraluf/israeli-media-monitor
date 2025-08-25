# analysis/text_norm.py
import re
import unicodedata

# Regexes
SPACE_RE = re.compile(r"\s+")
NUM_RE   = re.compile(r"\d+([.,]\d+)*")            # numbers like 123, 12.5, 12,345
PUNCT_RE = re.compile(r"[^\w\u0590-\u05FF\s]")     # drop everything except letters, digits, Hebrew, underscore, space
NIQQUD_RE = re.compile(r"[\u0591-\u05C7]")         # Hebrew diacritics range

def strip_niqqud(s: str) -> str:
    return NIQQUD_RE.sub("", s)

def norm_min(s: str) -> str:
    """
    Aggressive normalization for clustering:
    - NFC normalize diacritics
    - Lowercase
    - Remove Hebrew niqqud
    - Replace numbers with <NUM>
    - Drop all punctuation
    - Collapse whitespace
    """
    if not s:
        return ""
    s = unicodedata.normalize("NFC", s)
    s = s.lower()

    # Replace numbers
    s = NUM_RE.sub(" <NUM> ", s)

    # Strip diacritics
    s = strip_niqqud(s)

    # Remove punctuation (keep only letters, digits, spaces)
    s = PUNCT_RE.sub(" ", s)

    # Collapse multiple spaces
    s = SPACE_RE.sub(" ", s).strip()
    return s
