"""
사무소 정보 관리 서비스.
config/office_info.json 읽기/쓰기/잠금 토글.
"""
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
OFFICE_INFO_PATH = PROJECT_ROOT / "config" / "office_info.json"
LOCK_FILE_PATH = PROJECT_ROOT / "config" / "office_info.lock"


def load_office_info() -> dict:
    """
    사무소 정보 JSON 로드.
    _comment 키는 제외하고 반환.
    파일 없으면 빈 dict 반환.
    """
    if not OFFICE_INFO_PATH.exists():
        return {}

    with open(OFFICE_INFO_PATH, encoding="utf-8-sig") as f:
        data = json.load(f)

    return {k: v for k, v in data.items() if not k.startswith("_")}


def save_office_info(data: dict) -> None:
    """
    사무소 정보 저장.
    잠금 상태이면 저장 거부.
    기존 _comment 키는 보존.
    """
    if is_locked():
        raise PermissionError("사무소 정보가 잠금 상태입니다. 잠금을 해제 후 수정하세요.")

    existing = {}
    if OFFICE_INFO_PATH.exists():
        with open(OFFICE_INFO_PATH, encoding="utf-8") as f:
            existing = json.load(f)

    comment = existing.get("_comment", "사무소 정보. 실제 값으로 교체 후 사용.")

    output = {"_comment": comment}
    output.update(data)

    OFFICE_INFO_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OFFICE_INFO_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)


def is_locked() -> bool:
    """잠금 상태 여부 반환."""
    return LOCK_FILE_PATH.exists()


def set_lock(locked: bool) -> None:
    """
    잠금 설정/해제.
    locked=True: 잠금 파일 생성
    locked=False: 잠금 파일 삭제
    """
    if locked:
        LOCK_FILE_PATH.touch()
    else:
        if LOCK_FILE_PATH.exists():
            LOCK_FILE_PATH.unlink()


def get_office_value(key: str, default: str = "") -> str:
    """
    특정 키 값만 조회.
    예: get_office_value("사무소_명칭")
    """
    data = load_office_info()
    return data.get(key, default)
