"""
등록면허세 환급관리 프로그램 엔트리포인트.
이번 단계에서는 DB 초기화만 수행.
GUI는 Phase 1-4에서 추가됨.
"""
from app.db.migrations import init_database


def main():
    print("DB 초기화 시작...")
    init_database()
    print("DB 초기화 완료.")
    print("GUI는 Phase 1-4에서 구현됩니다.")


if __name__ == "__main__":
    main()
