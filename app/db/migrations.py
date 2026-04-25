"""스키마 초기화 및 업그레이드."""
from pathlib import Path
from app.db.database import get_connection

SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def init_database():
    """schema.sql 실행하여 테이블 생성. 이미 있으면 스킵."""
    SCHEMA_PATH.parent.parent.parent.joinpath("data").mkdir(exist_ok=True)

    with open(SCHEMA_PATH, encoding="utf-8") as f:
        schema_sql = f.read()

    conn = get_connection()
    try:
        conn.executescript(schema_sql)
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    init_database()
    print("데이터베이스 초기화 완료")
