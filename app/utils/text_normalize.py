import re


def normalize_company_name(name: str) -> str:
    """
    "주식회사 케이뱅크" / "(주)케이뱅크" / "㈜케이뱅크" / "케이뱅크 주식회사"
    → 모두 "케이뱅크"로 정규화
    """
    if not name:
        return ""

    # 한자/특수기호 회사 표기 제거
    patterns = [
        r"주식회사",
        r"\(주\)",
        r"㈜",
        r"\(유\)",
        r"유한회사",
        r"\(합\)",
        r"합자회사",
    ]

    result = name
    for pattern in patterns:
        result = re.sub(pattern, "", result)

    # 모든 공백 제거
    result = re.sub(r"\s+", "", result)

    return result.strip()
