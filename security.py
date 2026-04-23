import re
from typing import Any

_EMAIL = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
_PHONE = re.compile(r"(\+?886[-\s]?|0)(\d[\d\s\-]{7,10})")
_TWID  = re.compile(r"\b[A-Z][12]\d{8}\b")


def _scrub(s: str) -> str:
    s = _EMAIL.sub("[EMAIL]", s)
    s = _PHONE.sub("[PHONE]", s)
    s = _TWID.sub("[ID]", s)
    return s


def sanitize(obj: Any) -> Any:
    if isinstance(obj, str):  return _scrub(obj)
    if isinstance(obj, dict): return {k: sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list): return [sanitize(i) for i in obj]
    return obj
