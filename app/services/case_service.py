"""환급 사건 CRUD 서비스."""
from app.db.database import db_session, get_connection


def list_cases() -> list[dict]:
    """전체 사건 목록. paid_date 최신순."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT id, paid_date, payer_name, tax_total, refund_reason, status "
            "FROM refund_cases ORDER BY paid_date DESC, id DESC"
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def create_case(
    payer_name: str,
    paid_date: str,
    tax_total: int,
    refund_reason: str,
    client_id: int | None = None,
    handler: str | None = None,
    memo: str | None = None,
) -> int:
    """사건 생성. 반환: 생성된 id."""
    # 담당자는 refund_reason_detail에, 메모는 memo에 저장
    memo_text = memo or ""
    handler_text = handler or ""

    with db_session() as conn:
        cursor = conn.execute(
            """
            INSERT INTO refund_cases
                (payer_name, paid_date, tax_total, refund_reason,
                 client_id, refund_reason_detail, memo, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'CREATED')
            """,
            (
                payer_name.strip(),
                paid_date,
                tax_total,
                refund_reason,
                client_id,
                handler_text,
                memo_text,
            ),
        )
        return cursor.lastrowid


def get_case_stats() -> dict:
    """{"total": int, "in_progress": int, "closed": int}"""
    conn = get_connection()
    try:
        total = conn.execute(
            "SELECT COUNT(*) FROM refund_cases"
        ).fetchone()[0]
        closed = conn.execute(
            "SELECT COUNT(*) FROM refund_cases WHERE status = 'CLOSED'"
        ).fetchone()[0]
        return {
            "total": total,
            "in_progress": total - closed,
            "closed": closed,
        }
    finally:
        conn.close()
