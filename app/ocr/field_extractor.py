"""
키워드/패턴/표셀 매칭 기반 필드 추출기.
PaddleOCR이 추출한 텍스트 라인 리스트에서 필요한 필드만 골라냄.
"""

from __future__ import annotations

import re


def extract_fields(ocr_lines: list[dict]) -> dict:
    """
    OCR 추출 텍스트 라인들에서 필수 10개 필드를 추출한다.

    반환 형식:
    {
        "payer_name": {"value": str, "confidence": float, "needs_review": bool, "errors": list[str]},
        ...
    }
    """
    texts = [line["text"] for line in ocr_lines]
    confs = [line["confidence"] for line in ocr_lines]

    result = {}

    result["payer_name"] = _extract_payer_name(texts, confs)
    result["corp_no_masked"] = _extract_corp_no_masked(texts, confs)
    result["address"] = _extract_address(texts, confs)
    result["tax_item_code"], result["levy_period"], result["tax_no"] = \
        _extract_tax_no_table(ocr_lines)
    result["tax_base"] = _extract_tax_base(texts, confs)
    result["tax_total"] = _extract_tax_total(texts, confs)
    result["paid_date"] = _extract_paid_date(texts, confs)
    result["issue_authority"] = _extract_issue_authority(texts, confs)

    return result


def _make_field(value: str, confidence: float = 0.0, errors: list[str] | None = None) -> dict:
    errors = errors or []
    return {
        "value": value,
        "confidence": confidence,
        "needs_review": (not value) or (confidence < 0.85) or bool(errors),
        "errors": errors,
    }


# ============================================================
# 1. 납세자명 — "성명(법인명)" 라벨 뒤 텍스트
# ============================================================
def _extract_payer_name(texts: list[str], confs: list[float]) -> dict:
    """
    "성명(법인명) : 주식회사 케이뱅크" 형태에서 콜론 뒤 추출.
    동일 줄에 "주민(법인...)" 라벨이 같이 있을 수 있으므로 분리.
    """
    pattern = re.compile(r"성명\s*\(법인명\)\s*[:：]\s*(.+?)(?=\s+주민|\s*$)")
    for idx, text in enumerate(texts):
        m = pattern.search(text)
        if m:
            value = m.group(1).strip()
            return _make_field(value, confs[idx])
    return _make_field("", 0.0, ["납세자명 라벨을 찾지 못함"])


# ============================================================
# 2. 법인번호 마스킹 — \d{6}-\*{7} 패턴
# ============================================================
def _extract_corp_no_masked(texts: list[str], confs: list[float]) -> dict:
    """
    "110111-*******" 형태 검출. 라인 어디든 등장하면 매칭.
    OCR이 *를 ★, x, X 등으로 잘못 읽을 수 있으므로 보정.
    """
    strict = re.compile(r"(\d{6})\s*-\s*(\*{7})")
    loose = re.compile(r"(\d{6})\s*-\s*([\*★xX]{5,8})")

    for idx, text in enumerate(texts):
        m = strict.search(text)
        if m:
            return _make_field(f"{m.group(1)}-*******", confs[idx])
        m = loose.search(text)
        if m:
            return _make_field(f"{m.group(1)}-*******", confs[idx],
                               ["마스킹 문자 보정 적용"])
    return _make_field("", 0.0, ["법인번호 패턴을 찾지 못함"])


# ============================================================
# 3. 주소 — "주소(영업소)" 라벨 뒤 텍스트
# ============================================================
def _extract_address(texts: list[str], confs: list[float]) -> dict:
    pattern = re.compile(r"주소\s*\(영업소\)\s*[:：]\s*(.+)")
    for idx, text in enumerate(texts):
        m = pattern.search(text)
        if m:
            value = m.group(1).strip()
            value = re.split(r"등기\s*\(등록\)", value)[0].strip()
            return _make_field(value, confs[idx])
    return _make_field("", 0.0, ["주소 라벨을 찾지 못함"])


# ============================================================
# 4-6. 납세번호 표 — 세목/과세연도/월/과세번호
# ============================================================
def _extract_tax_no_table(ocr_lines: list[dict]) -> tuple[dict, dict, dict]:
    """
    납세번호 표의 데이터 행을 bbox y좌표 기반으로 찾아 추출.

    표 구조: [기관][검][회계][과목][세목][과세연도][월][구분][읍·면·동][과세번호][검]
                0    1    2    3   4(★) 5(★)    6(★)  7      8       9(★)    10
    """
    lines_with_y = []
    for line in ocr_lines:
        bbox = line["bbox"]
        if not bbox or len(bbox) < 1:
            continue
        y_top = min(p[1] for p in bbox)
        x_left = min(p[0] for p in bbox)
        lines_with_y.append({
            "text": line["text"].strip(),
            "y": y_top,
            "x": x_left,
            "confidence": line["confidence"],
        })

    lines_with_y.sort(key=lambda l: (l["y"], l["x"]))

    # y 차이 30px 이내를 같은 줄로 묶기
    rows = []
    current_row = []
    last_y = None
    for line in lines_with_y:
        if last_y is None or abs(line["y"] - last_y) <= 30:
            current_row.append(line)
        else:
            if current_row:
                rows.append(current_row)
            current_row = [line]
        last_y = line["y"]
    if current_row:
        rows.append(current_row)

    for row in rows:
        row.sort(key=lambda l: l["x"])

    # 데이터 행 후보: 9개 이상 셀이 있고 그 중 하나가 4자리 연도인 줄
    target_row = None
    for row in rows:
        if len(row) < 9:
            continue
        for i, cell in enumerate(row):
            if re.fullmatch(r"\d{4}", cell["text"]) and 3 <= i <= 6:
                target_row = row
                break
        if target_row:
            break

    if not target_row:
        err = ["납세번호 데이터 행을 찾지 못함"]
        return (_make_field("", 0.0, err),
                _make_field("", 0.0, err),
                _make_field("", 0.0, err))

    # 연도 셀 위치 기준으로 인덱스 보정
    year_idx = None
    for i, cell in enumerate(target_row):
        if re.fullmatch(r"\d{4}", cell["text"]):
            year_idx = i
            break

    if year_idx is None or year_idx < 1:
        err = ["연도 셀 인덱스 보정 실패"]
        return (_make_field("", 0.0, err),
                _make_field("", 0.0, err),
                _make_field("", 0.0, err))

    # 연도가 표 구조상 인덱스 5 위치
    base = year_idx - 5

    def get_cell(rel_idx):
        absolute_idx = base + rel_idx
        if 0 <= absolute_idx < len(target_row):
            return target_row[absolute_idx]
        return None

    tax_item_cell = get_cell(4)
    year_cell = target_row[year_idx]
    month_cell = get_cell(6)
    tax_no_cell = get_cell(9)

    if not all([tax_item_cell, year_cell, month_cell, tax_no_cell]):
        err = ["일부 셀 누락"]
        return (_make_field("", 0.0, err),
                _make_field("", 0.0, err),
                _make_field("", 0.0, err))

    month_str = month_cell["text"].lstrip("0") or "0"
    levy_period_value = f"{year_cell['text']}.{month_str}"

    return (
        _make_field(tax_item_cell["text"], tax_item_cell["confidence"]),
        _make_field(levy_period_value, min(year_cell["confidence"], month_cell["confidence"])),
        _make_field(tax_no_cell["text"], tax_no_cell["confidence"]),
    )


# ============================================================
# 7. 과세표준 — "과세표준:" 뒤 숫자
# ============================================================
def _extract_tax_base(texts: list[str], confs: list[float]) -> dict:
    pattern = re.compile(r"과세표준\s*[:：]?\s*([\d,]+)\s*원?")
    for idx, text in enumerate(texts):
        m = pattern.search(text)
        if m:
            raw = m.group(1).replace(",", "")
            try:
                int(raw)
                return _make_field(f"{int(raw):,}", confs[idx])
            except ValueError:
                continue
    return _make_field("", 0.0, ["과세표준 값을 찾지 못함"])


# ============================================================
# 8. 지방세 계 — "계" 라인 다음 숫자
# ============================================================
def _extract_tax_total(texts: list[str], confs: list[float]) -> dict:
    """
    "계" 텍스트 라인 다음에 나오는 숫자 = 지방세 합계.
    "201,600원" 또는 "201,600" + "원" 분리 케이스 모두 대응.
    """
    for idx, text in enumerate(texts):
        if text.strip() == "계":
            for j in range(idx + 1, min(idx + 4, len(texts))):
                m = re.search(r"([\d,]+)\s*원?", texts[j])
                if m:
                    raw = m.group(1).replace(",", "")
                    try:
                        amount = int(raw)
                        if amount > 0:
                            return _make_field(f"{amount:,}", confs[j])
                    except ValueError:
                        continue
    return _make_field("", 0.0, ["지방세 계 값을 찾지 못함"])


# ============================================================
# 9. 납부일 — "YYYY년 MM월 DD일" 패턴
# ============================================================
def _extract_paid_date(texts: list[str], confs: list[float]) -> dict:
    """
    "2025년 07월 25일" 또는 "2025년 7월 25일" 형태.
    납부확인서 본문에 2번 등장 — 첫 번째 채택.
    """
    pattern = re.compile(r"(\d{4})\s*년\s*(\d{1,2})\s*월\s*(\d{1,2})\s*일")
    for idx, text in enumerate(texts):
        m = pattern.search(text)
        if m:
            y, mo, d = m.group(1), m.group(2).zfill(2), m.group(3).zfill(2)
            return _make_field(f"{y}-{mo}-{d}", confs[idx])
    return _make_field("", 0.0, ["납부일 패턴을 찾지 못함"])


# ============================================================
# 10. 발급지자체 — "○○시장|○○구청장|○○군수|○○도지사"
# ============================================================
def _extract_issue_authority(texts: list[str], confs: list[float]) -> dict:
    """
    하단 도장 옆 "철원군수", "수원시영통구청장" 등.
    OCR이 "사 천 시 장" 처럼 띄워서 뽑을 수 있음 — 공백 제거 후 매칭.
    1차 실패 시 인접 라인을 합쳐 재시도.
    """
    pattern = re.compile(r"([가-힣]+(?:시\s*[가-힣]+구청장|시장|군수|도지사|구청장))")

    # 1차: 각 줄에서 공백 제거 후 매칭
    for idx, text in enumerate(texts):
        compact = re.sub(r"\s+", "", text)
        m = pattern.search(compact)
        if m:
            return _make_field(m.group(1), confs[idx])

    # 2차: 인접 라인을 합쳐서 매칭 (도장 옆 텍스트가 분할 OCR된 경우)
    for idx in range(len(texts)):
        for window in [2, 3]:
            if idx + window > len(texts):
                continue
            joined = "".join(texts[idx:idx + window])
            compact = re.sub(r"\s+", "", joined)
            m = pattern.search(compact)
            if m:
                avg_conf = sum(confs[idx:idx + window]) / window
                return _make_field(m.group(1), avg_conf, ["인접 라인 결합으로 추출"])

    return _make_field("", 0.0, ["발급지자체 패턴을 찾지 못함"])
