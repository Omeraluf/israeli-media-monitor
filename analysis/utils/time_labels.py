import re

_CLOCK = re.compile(r"^\s*\d{1,2}[:.]\d{2}\s*$")          # "10:22" or "10.22"
_ONLY_DIGITS_SEPARATORS = re.compile(r"^[\s\d:.\-/]+$")   # very short "21:03", "12/08", etc.

_LOCALE = {
    "he": {
        "yesterday": ["אתמול"],
        "ago_prefix": ["לפני"],  # Hebrew "ago" is a prefix
        "units": {
            "minute": ["דקה", "דקות"],
            "hour": ["שעה", "שעות", "כשעה", "שעתיים"],
            "day": ["יום", "ימים", "יומיים"],
        },
    },
    "en": {
        "yesterday": ["yesterday"],
        "ago_prefix": ["ago"],  # usually suffix in English, we handle both
        "units": {
            "minute": ["minute", "minutes", "min", "mins"],
            "hour": ["hour", "hours", "hr", "hrs"],
            "day": ["day", "days"],
        },
    },
}

def is_time_label(text: str) -> bool:
    """
    True if the string looks like a 'posted time' label rather than a real summary.
    Catches: "10:22", "אתמול 21:00", "לפני 5 שעות", "5 minutes ago", etc.
    """
    if not isinstance(text, str):
        return False
    s = text.strip()
    if not s:
        return False

    if _CLOCK.match(s):
        return True
    if len(s) <= 10 and _ONLY_DIGITS_SEPARATORS.match(s):
        return True

    loc = _guess_locale(s)
    L = _LOCALE.get(loc, _LOCALE["en"])

    # “yesterday” token
    if any(word in s.lower() for word in L["yesterday"]):
        return True

    # number + unit + (ago/לפני)
    has_num = re.search(r"\d+", s) is not None
    unit_words = sum(L["units"].values(), [])
    has_unit = any(uw in s for uw in unit_words)
    ago_hit = any(tok in s for tok in L["ago_prefix"])

    if (ago_hit and (has_num or has_unit)) or (has_num and has_unit):
        return True

    return False

def _guess_locale(s: str) -> str:
    # crude but effective: if any Hebrew char -> Hebrew
    if any("\u0590" <= ch <= "\u05FF" for ch in s):
        return "he"
    return "en"