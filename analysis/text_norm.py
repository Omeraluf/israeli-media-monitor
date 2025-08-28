# # analysis/text_norm.py
# import re
# import unicodedata

# # Regexes
# SPACE_RE = re.compile(r"\s+")
# NUM_RE   = re.compile(r"\d+([.,]\d+)*")            # numbers like 123, 12.5, 12,345
# PUNCT_RE = re.compile(r"[^\w\u0590-\u05FF\s]")     # drop everything except letters, digits, Hebrew, underscore, space
# NIQQUD_RE = re.compile(r"[\u0591-\u05C7]")         # Hebrew diacritics range

# def strip_niqqud(s: str) -> str:
#     return NIQQUD_RE.sub("", s)

# def norm_min(s: str) -> str:
#     """
#     Aggressive normalization for clustering:
#     - NFC normalize diacritics
#     - Lowercase
#     - Remove Hebrew niqqud
#     - Replace numbers with <NUM>
#     - Drop all punctuation
#     - Collapse whitespace
#     """
#     if not s:
#         return ""
#     s = unicodedata.normalize("NFC", s)
#     s = s.lower()

#     # Replace numbers
#     s = NUM_RE.sub(" <NUM> ", s)

#     # Strip diacritics
#     s = strip_niqqud(s)

#     # Remove punctuation (keep only letters, digits, spaces)
#     s = PUNCT_RE.sub(" ", s)

#     # Collapse multiple spaces
#     s = SPACE_RE.sub(" ", s).strip()
#     return s

################# OLD VER ABOVE #################

import re, unicodedata

# --- helpers/regexes ---
NUM_RE   = re.compile(r"\d+(?:[.,]\d+)?")  # 12, 12.5, 12,500
SPACE_RE = re.compile(r"\s+")
# keep Hebrew (0590–05FF), Latin letters, digits, spaces, and our <TOKENS>
PUNCT_RE = re.compile(r"[^0-9A-Za-z\u0590-\u05FF<> ]+")

# niqqud/ta'amim
NIQQUD_RE = re.compile(r"[\u0591-\u05BD\u05BF\u05C1-\u05C7]")

# site suffix after pipe/dash
SITE_SUFFIX = re.compile(
    r"\s*(?:\||[-–—])\s*(?:N12|חדשות\s?12|mako|כאן\s?11|Kan\s?11|ערוץ\s?14|ynet|גלובס|וואלה|israelhayom)\s*$",
    re.I,
)

# CTA labels at start (optional list—tune as you go)
CTA_PREFIX = re.compile(
    r"^(?:צפו|וידאו|פרשנות|דעה|חשיפה|מיוחד|תיעוד|ראיון|ריאיון|מדריך|הסבר)\s*:?\s+",
    re.I,
)

# bullets/typographic dots
BULLETS_RE = re.compile(r"[•·▪◦●○∙]")

# HH:MM -> protect as <TIME>
TIME_RE = re.compile(r"\b(?:[01]?\d|2[0-3]):[0-5]\d\b")

def strip_niqqud(s: str) -> str:
    return NIQQUD_RE.sub("", s)

def norm_min(s: str) -> str:
    """
    Aggressive normalization for clustering:
    - NFKC normalize
    - Remove CTA prefixes (e.g., 'צפו:')
    - Remove site suffixes (' | N12', ' - mako', etc.)
    - Protect times (HH:MM) -> <TIME>
    - Lowercase
    - Replace numbers -> <NUM>
    - Remove Hebrew niqqud
    - Normalize dashes/quotes/bullets
    - Drop punctuation
    - Collapse whitespace
    """
    if not s:
        return ""
    # Normalize compatibility forms (quotes/dashes/space variants)
    s = unicodedata.normalize("NFKC", s)
    s = s.replace("\u200f", " ").replace("\u200e", " ").replace("\u200d", " ")  # bidi/ZWJ
    s = s.replace("…", "...")                          # unify ellipsis
    s = BULLETS_RE.sub(" ", s)                         # remove bullets

    # Remove leading CTA labels and trailing site suffixes
    s = CTA_PREFIX.sub("", s)
    s = SITE_SUFFIX.sub("", s)

    # Protect HH:MM as a semantic token before nuking punctuation/numbers
    s = TIME_RE.sub(" <TIME> ", s)

    s = s.lower()

    # Replace numbers (after <TIME> protection)
    s = NUM_RE.sub(" <NUM> ", s)

    # Strip niqqud
    s = strip_niqqud(s)

    # Dashes → space so תל-אביב == תל אביב
    s = re.sub(r"[‐-–—−-]", " ", s)

    # Unify quotes → space (not strictly needed since we drop punctuation next)
    s = s.replace("“", " ").replace("”", " ").replace("״", " ").replace("’", " ").replace("׳", " ").replace('"', " ")

    # Drop all remaining punctuation except our tokens
    s = PUNCT_RE.sub(" ", s)

    # Collapse spaces
    s = SPACE_RE.sub(" ", s).strip()
    return s
