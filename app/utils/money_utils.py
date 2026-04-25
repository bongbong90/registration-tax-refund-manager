from __future__ import annotations

import re


def parse_money(raw: str) -> int | None:
    if raw is None:
        return None

    text = str(raw)
    text = text.replace(",", "").replace("원", "")
    text = re.sub(r"\s+", "", text)
    digits = re.findall(r"\d+", text)
    if not digits:
        return None

    number = "".join(digits)
    try:
        return int(number)
    except ValueError:
        return None

