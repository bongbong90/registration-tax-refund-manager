"""
거래처 서비스 동작 검증.
GUI 없이 CRUD/매칭/엑셀 기능을 콘솔로 확인.

사용:
    python -m tests.test_client_service
"""
from pathlib import Path

from app.db.migrations import init_database
from app.services.client_service import (
    create_client,
    update_client,
    delete_client,
    get_client,
    list_clients,
    find_matching_clients,
    verify_corp_no_match,
)
from app.utils.excel_io import export_to_excel, import_from_excel


def main():
    print("=" * 60)
    print("거래처 서비스 검증 시작")
    print("=" * 60)

    # 0. DB 초기화
    init_database()

    # 1. 기존 거래처 모두 정리 (테스트 격리)
    print("\n[0] 기존 거래처 정리")
    for c in list_clients():
        delete_client(c.id)
    print(f"  -> {len(list_clients())}건 (정리 후)")

    # 2. 생성
    print("\n[1] 거래처 생성")
    id1 = create_client(
        client_name="주식회사 케이뱅크",
        corporation_no="110111-5938985",
        business_no="826-81-00172",
        representative_name="대표이사 최우형",
        address="서울특별시 중구 을지로 170, 동관 6층",
        email="forest@kbanknow.com",
    )
    id2 = create_client(
        client_name="삼성화재해상보험 주식회사",
        corporation_no="110111-2348765",
        representative_name="대표이사 홍길동",
    )
    id3 = create_client(client_name="(주)카카오뱅크")
    print(f"  -> 생성 ID: {id1}, {id2}, {id3}")

    # 3. 조회
    print("\n[2] 단건 조회")
    c = get_client(id1)
    print(f"  -> {c.client_name} / {c.corporation_no}")

    print("\n[3] 전체 목록")
    for c in list_clients():
        print(f"  - [{c.id}] {c.client_name}")

    # 4. 검색
    print("\n[4] 검색 ('카카오')")
    for c in list_clients(search="카카오"):
        print(f"  - {c.client_name} (정규화: {c.normalized_name})")

    # 5. 수정
    print("\n[5] 수정")
    update_client(id3, manager_name="김담당", manager_phone="02-0000-0000")
    c = get_client(id3)
    print(f"  -> {c.client_name} / {c.manager_name} / {c.manager_phone}")

    # 6. 매칭 (정규화 효과 확인)
    print("\n[6] 매칭 — '케이뱅크' 검색")
    matches = find_matching_clients("케이뱅크", masked_corp_no="110111-*******")
    for c in matches:
        print(f"  - {c.client_name} (corp: {c.corporation_no})")

    print("\n[7] 매칭 — '㈜카카오뱅크' 검색 (특수기호)")
    matches = find_matching_clients("㈜카카오뱅크")
    for c in matches:
        print(f"  - {c.client_name}")

    # 7. 법인번호 검증
    print("\n[8] 법인번호 검증")
    c = get_client(id1)
    print(
        "  케이뱅크(110111-5938985) vs 마스킹 110111-***** : "
        f"{verify_corp_no_match(c, '110111-*******')}"
    )
    print(
        "  케이뱅크(110111-5938985) vs 마스킹 999999-***** : "
        f"{verify_corp_no_match(c, '999999-*******')}"
    )

    # 8. 엑셀 내보내기
    print("\n[9] 엑셀 내보내기")
    export_path = Path("data") / "test_export.xlsx"
    count = export_to_excel(export_path)
    print(f"  -> {count}건 내보냄: {export_path}")

    # 9. 엑셀 가져오기 (방금 내보낸 거 그대로)
    print("\n[10] 엑셀 가져오기 (동일 파일 — 모두 update 되어야 함)")
    result = import_from_excel(export_path)
    print(f"  -> 신규 {result['created']} / 수정 {result['updated']} / 스킵 {result['skipped']}")

    # 10. 정리
    print("\n[11] 테스트 데이터 정리")
    for c in list_clients():
        delete_client(c.id)
    if export_path.exists():
        export_path.unlink()
    print(f"  -> {len(list_clients())}건 (정리 후)")

    print("\n" + "=" * 60)
    print("검증 완료")
    print("=" * 60)


if __name__ == "__main__":
    main()

