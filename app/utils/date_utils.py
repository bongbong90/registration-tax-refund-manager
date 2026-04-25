from __future__ import annotations

import re
from datetime import date

KOREAN_DATE_PATTERN = re.compile(r"(\d{4})\s*년\s*(\d{1,2})\s*월\s*(\d{1,2})\s*일")


def parse_korean_date(raw: str) -> str | None:
    if not raw:
        return None

    matched = KOREAN_DATE_PATTERN.search(str(raw))
    if not matched:
        return None

    year, month, day = (int(matched.group(1)), int(matched.group(2)), int(matched.group(3)))
    try:
        parsed = date(year, month, day)
    except ValueError:
        return None
    return parsed.isoformat()

