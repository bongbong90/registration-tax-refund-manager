"""
실제 거래처 초기 등록 스크립트.
사용자가 수동 편집 후 실행. 테스트와 무관.

사용:
    python -m scripts.seed_clients
"""
from app.db.migrations import init_database
from app.services.client_service import create_client, find_matching_clients


# 사용자가 직접 편집할 영역
INITIAL_CLIENTS = [
    {
        "client_name": "주식회사 케이뱅크",
        "corporation_no": "110111-5938985",
        "business_no": "826-81-00172",
        "representative_name": "대표이사 최우형",
        "address": "서울특별시 중구 을지로 170, 동관 6층",
        "email": "forest@kbanknow.com",
    },
    # 여기 더 추가...
]


def main():
    init_database()

    print(f"거래처 {len(INITIAL_CLIENTS)}건 등록 시도...")

    for data in INITIAL_CLIENTS:
        # 중복 확인
        existing = find_matching_clients(data["client_name"])
        exact = next((c for c in existing if c.client_name == data["client_name"]), None)

        if exact:
            print(f"  스킵: {data['client_name']} (이미 존재, ID={exact.id})")
            continue

        new_id = create_client(**data)
        print(f"  생성: [{new_id}] {data['client_name']}")

    print("완료.")


if __name__ == "__main__":
    main()

