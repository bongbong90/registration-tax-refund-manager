"""
HWP 치환 엔진 검증 스크립트.
더미 데이터로 3종 HWP 생성 후 콘솔로 결과 확인.

사용:
    python -m tests.test_hwp_filler

요구사항:
    - 한/글 2014 이상 설치
    - templates/hwp/ 에 양식 3종 존재
    - config/office_info.json 실제값 채워져 있음
"""
from pathlib import Path
from app.db.migrations import init_database
from app.services.office_info_service import load_office_info, is_locked
from app.hwp.hwp_filler import fill_all_forms

PROJECT_ROOT = Path(__file__).parent.parent
TEST_OUTPUT_DIR = PROJECT_ROOT / "data" / "hwp_test_output"


# ============================================================
# 더미 데이터 (실제 환급 사건 형태와 동일한 구조)
# ============================================================

DUMMY_CASE = {
    "paid_date": "2026-04-24",
    "tax_item_code": "002",
    "tax_no": "007794",
    "levy_period": "2026.4",
    "tax_base": "84,000,000",
    "tax_total": "201,600",
    "issue_authority": "사천시장",
    "refund_reason": "대출취소",
    "claim_date": None,  # None이면 오늘 날짜 자동 입력
}

DUMMY_CLIENT = {
    "client_name": "주식회사 국민은행",
    "representative_name": "대표이사 이재근",
    "corporation_no": "110111-1234567",
    "business_no": "204-81-48478",
    "address": "서울특별시 영등포구 국제금융로8길 26 (여의도동)",
    "email": "test@kbstar.com",
}


def main():
    print("=" * 60)
    print("HWP 치환 엔진 검증 시작")
    print("=" * 60)

    # 1. DB 초기화
    init_database()

    # 2. 사무소 정보 로드
    print("\n[1] 사무소 정보 로드")
    if is_locked():
        print("  ⚠ 사무소 정보가 잠금 상태입니다.")

    office_data = load_office_info()
    if not office_data:
        print("  ✗ 사무소 정보 없음. config/office_info.json 을 채워주세요.")
        return

    print(f"  ✓ 사무소명: {office_data.get('사무소_명칭', '(없음)')}")
    print(f"  ✓ 담당법무사: {office_data.get('사무소_법무사', '(없음)')}")

    # 3. 출력 폴더 준비
    TEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\n[2] 출력 폴더: {TEST_OUTPUT_DIR}")

    # 4. HWP 3종 생성
    print("\n[3] HWP 3종 생성 시작 (한/글 보안 다이얼로그 뜨면 [모두 허용] 클릭)")
    print("    한/글이 3번 자동으로 켜졌다 꺼집니다. 정상입니다.\n")

    results = fill_all_forms(
        case_data=DUMMY_CASE,
        client_data=DUMMY_CLIENT,
        office_data=office_data,
        output_dir=TEST_OUTPUT_DIR,
        file_prefix="테스트_국민은행_20260424",
    )

    # 5. 결과 출력
    print("\n" + "=" * 60)
    print("생성 결과")
    print("=" * 60)

    form_names = {
        "form22": "제22호 환급청구서",
        "form14": "제14호 경정청구서",
        "form27": "제27호 양도요구서",
    }

    for form_key, name in form_names.items():
        r = results.get(form_key, {})
        status = "✓ 성공" if r.get("success") else "✗ 실패"
        print(f"\n[{name}] {status}")

        if r.get("error"):
            print(f"  에러: {r['error']}")

        if r.get("output_path"):
            print(f"  경로: {r['output_path']}")

        if r.get("unfilled"):
            print(f"  ⚠ 치환 실패 치환자 ({len(r['unfilled'])}개):")
            for u in r["unfilled"]:
                print(f"    - {u}")
        else:
            if r.get("success"):
                print(f"  모든 치환자 정상 처리")

    print("\n" + "=" * 60)
    overall = "✓ 전체 성공" if results.get("all_success") else "✗ 일부 실패"
    print(f"최종 결과: {overall}")
    print("=" * 60)

    print(f"\n생성된 파일 위치: {TEST_OUTPUT_DIR}")
    print("각 HWP 파일을 한/글로 열어 치환자가 올바르게 채워졌는지 직접 확인하세요.")


if __name__ == "__main__":
    main()
