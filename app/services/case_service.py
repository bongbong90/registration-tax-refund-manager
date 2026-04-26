"""환급 사건 CRUD + 상세 + 상태 전이 서비스."""
from app.db.database import db_session, get_connection

STATUS_FLOW = [
    "CREATED",
    "SENT_TO_BANK",
    "BANK_RETURNED",
    "SUBMITTED",
    "REFUND_DECIDED",
    "DEPOSITED",
    "CLOSED",
]

STATUS_LABELS = {
    "CREATED": "서류생성",
    "SENT_TO_BANK": "은행송부",
    "BANK_RETURNED": "은행회신",
    "SUBMITTED": "구청접수",
    "REFUND_DECIDED": "환급결정",
    "DEPOSITED": "입금확인",
    "CLOSED": "종결",
}


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


def get_case(case_id: int) -> dict | None:
    """사건 상세 단건 조회."""
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT
                rc.id,
                rc.client_id,
                c.client_name,
                rc.payer_name,
                rc.paid_date,
                rc.tax_total,
                rc.refund_reason,
                rc.refund_reason_detail AS handler,
                rc.memo,
                rc.status,
                rc.created_at,
                rc.updated_at
            FROM refund_cases rc
            LEFT JOIN clients c ON c.id = rc.client_id
            WHERE rc.id = ?
            """,
            (case_id,),
        ).fetchone()
        return dict(row) if row else None
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


def update_case_basic(
    case_id: int,
    payer_name: str,
    paid_date: str,
    tax_total: int,
    refund_reason: str,
    client_id: int | None,
    handler: str | None,
) -> None:
    """기본정보 탭 항목 업데이트."""
    with db_session() as conn:
        conn.execute(
            """
            UPDATE refund_cases
            SET
                payer_name = ?,
                paid_date = ?,
                tax_total = ?,
                refund_reason = ?,
                client_id = ?,
                refund_reason_detail = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                payer_name.strip(),
                paid_date,
                tax_total,
                refund_reason.strip(),
                client_id,
                (handler or "").strip(),
                case_id,
            ),
        )


def update_case_memo(case_id: int, memo: str | None) -> None:
    """메모 탭 내용 저장."""
    with db_session() as conn:
        conn.execute(
            """
            UPDATE refund_cases
            SET
                memo = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            ((memo or "").strip(), case_id),
        )


def list_case_events(case_id: int) -> list[dict]:
    """사건 진행 이력 조회."""
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT
                id,
                created_at,
                event_date,
                event_type AS content,
                COALESCE(memo, '') AS actor
            FROM case_events
            WHERE case_id = ?
            ORDER BY id DESC
            """,
            (case_id,),
        ).fetchall()

        events: list[dict] = []
        for row in rows:
            item = dict(row)
            processed_at = item.get("created_at") or item.get("event_date") or ""
            events.append(
                {
                    "id": item["id"],
                    "processed_at": processed_at,
                    "event_date": item.get("event_date", ""),
                    "content": item.get("content", ""),
                    "actor": item.get("actor", ""),
                }
            )
        return events
    finally:
        conn.close()


def add_case_event(
    case_id: int,
    event_date: str,
    content: str,
    actor: str | None = None,
) -> None:
    """사건 이력 1건 추가."""
    with db_session() as conn:
        conn.execute(
            """
            INSERT INTO case_events (case_id, event_type, event_date, memo)
            VALUES (?, ?, ?, ?)
            """,
            (case_id, content.strip(), event_date, (actor or "").strip()),
        )


def get_next_status(current_status: str) -> str | None:
    """현재 상태의 다음 상태 코드 반환. 마지막 상태면 None."""
    if current_status not in STATUS_FLOW:
        return None

    idx = STATUS_FLOW.index(current_status)
    if idx >= len(STATUS_FLOW) - 1:
        return None
    return STATUS_FLOW[idx + 1]


def advance_case_status(case_id: int, event_date: str, actor: str | None = None) -> str | None:
    """
    라이프사이클 다음 단계로 진행하고 이력 자동 기록.
    반환: 변경된 새 상태 코드. 종결 상태면 None.
    """
    with db_session() as conn:
        row = conn.execute(
            "SELECT status FROM refund_cases WHERE id = ?",
            (case_id,),
        ).fetchone()
        if not row:
            raise ValueError("사건을 찾을 수 없습니다.")

        current = row["status"] or "CREATED"
        nxt = get_next_status(current)
        if nxt is None:
            return None

        conn.execute(
            """
            UPDATE refund_cases
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (nxt, case_id),
        )

        from_label = STATUS_LABELS.get(current, current)
        to_label = STATUS_LABELS.get(nxt, nxt)
        conn.execute(
            """
            INSERT INTO case_events (case_id, event_type, event_date, memo)
            VALUES (?, ?, ?, ?)
            """,
            (case_id, f"{from_label} → {to_label}", event_date, (actor or "").strip()),
        )
        return nxt


def get_case_stats() -> dict:
    """{"total": int, "in_progress": int, "closed": int}"""
    conn = get_connection()
    try:
        total = conn.execute("SELECT COUNT(*) FROM refund_cases").fetchone()[0]
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
