"""
필드 추출 후 추가 검증/보정.
field_extractor가 1차 검증까지 처리하므로 여기서는 보조 검증만.
"""

from __future__ import annotations


def validate_required_fields(fields: dict) -> dict:
    """필수 필드 누락 여부 최종 점검. 누락된 경우 needs_review=True로 강제."""
    required_keys = [
        "payer_name", "corp_no_masked", "address",
        "tax_item_code", "levy_period", "tax_no",
        "tax_base", "tax_total", "paid_date", "issue_authority",
    ]

    for key in required_keys:
        if key not in fields:
            fields[key] = {
                "value": "",
                "confidence": 0.0,
                "needs_review": True,
                "errors": [f"{key} 필드 누락"],
            }
        elif not fields[key].get("value"):
            fields[key]["needs_review"] = True

    return fields
