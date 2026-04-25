import json
from pathlib import Path

OFFICE_INFO_PATH = Path(__file__).parent.parent.parent / "config" / "office_info.json"


def load_office_info() -> dict:
    """사무소 정보 JSON 로드. 키 앞에 _comment 시작하는 항목은 제외."""
    with open(OFFICE_INFO_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return {k: v for k, v in data.items() if not k.startswith("_")}
