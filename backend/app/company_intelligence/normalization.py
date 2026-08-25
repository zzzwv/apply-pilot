import re
import unicodedata


def normalize_company_name(value: str) -> str:
    """Return a stable lookup value without attempting entity disambiguation."""
    normalized = unicodedata.normalize("NFKC", value)
    return re.sub(r"\s+", " ", normalized).strip().casefold()
