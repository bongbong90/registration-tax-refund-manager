"""거래처 마스터 CRUD 서비스."""
from dataclasses import dataclass
from typing import Optional

from app.db.database import db_session, get_connection
from app.utils.text_normalize import normalize_company_name


@dataclass
class Client:
    """거래처 도메인 모델."""

    id: Optional[int]
    client_name: str
    normalized_name: str
    corporation_no: Optional[str]
    business_no: Optional[str]
    representative_name: Optional[str]
    address: Optional[str]
    email: Optional[str]
    manager_name: Optional[str]
    manager_phone: Optional[str]
    memo: Optional[str]

    @classmethod
    def from_row(cls, row) -> "Client":
        return cls(
            id=row["id"],
            client_name=row["client_name"],
            normalized_name=row["normalized_name"],
            corporation_no=row["corporation_no"],
            business_no=row["business_no"],
            representative_name=row["representative_name"],
            address=row["address"],
            email=row["email"],
            manager_name=row["manager_name"],
            manager_phone=row["manager_phone"],
            memo=row["memo"],
        )


# ============================================================
# CRUD
# ============================================================


def create_client(
    client_name: str,
    corporation_no: Optional[str] = None,
    business_no: Optional[str] = None,
    representative_name: Optional[str] = None,
    address: Optional[str] = None,
    email: Optional[str] = None,
    manager_name: Optional[str] = None,
    manager_phone: Optional[str] = None,
    memo: Optional[str] = None,
) -> int:
    """거래처 신규 등록. 반환: 생성된 id."""
    if not client_name or not client_name.strip():
        raise ValueError("거래처명은 필수입니다.")

    normalized = normalize_company_name(client_name)

    with db_session() as conn:
        cursor = conn.execute(
            """
            INSERT INTO clients (
                client_name, normalized_name, corporation_no, business_no,
                representative_name, address, email, manager_name, manager_phone, memo
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                client_name.strip(),
                normalized,
                corporation_no,
                business_no,
                representative_name,
                address,
                email,
                manager_name,
                manager_phone,
                memo,
            ),
        )
        return cursor.lastrowid


def update_client(client_id: int, **fields) -> None:
    """거래처 수정. fields: 변경할 필드만 넘기면 됨."""
    if not fields:
        return

    if "client_name" in fields:
        fields["normalized_name"] = normalize_company_name(fields["client_name"])

    set_clauses = []
    values = []
    for k, v in fields.items():
        set_clauses.append(f"{k} = ?")
        values.append(v)

    set_clauses.append("updated_at = CURRENT_TIMESTAMP")
    values.append(client_id)

    with db_session() as conn:
        conn.execute(
            f"UPDATE clients SET {', '.join(set_clauses)} WHERE id = ?",
            values,
        )


def delete_client(client_id: int) -> None:
    """거래처 삭제."""
    with db_session() as conn:
        conn.execute("DELETE FROM clients WHERE id = ?", (client_id,))


def get_client(client_id: int) -> Optional[Client]:
    """ID로 거래처 단건 조회."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM clients WHERE id = ?",
            (client_id,),
        ).fetchone()
        return Client.from_row(row) if row else None
    finally:
        conn.close()


def list_clients(search: str = "") -> list[Client]:
    """거래처 목록 조회. search 있으면 client_name LIKE 검색."""
    conn = get_connection()
    try:
        if search:
            rows = conn.execute(
                "SELECT * FROM clients WHERE client_name LIKE ? OR normalized_name LIKE ? ORDER BY client_name",
                (f"%{search}%", f"%{normalize_company_name(search)}%"),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM clients ORDER BY client_name",
            ).fetchall()
        return [Client.from_row(r) for r in rows]
    finally:
        conn.close()


# ============================================================
# 매칭 (납부확인서 OCR 결과 -> 거래처 DB 연결)
# ============================================================


def find_matching_clients(
    payer_name: str,
    masked_corp_no: Optional[str] = None,
) -> list[Client]:
    """
    OCR로 추출된 납세자명으로 매칭되는 거래처 후보 검색.

    매칭 우선순위:
    1. client_name 완전일치
    2. normalized_name 완전일치
    3. normalized_name 부분일치
    4. (보조) 마스킹 법인번호 앞 6자리 일치

    반환: 후보 거래처 리스트. 자동확정 금지 - 항상 사용자 확인 필요.
    """
    if not payer_name:
        return []

    normalized = normalize_company_name(payer_name)
    masked_prefix = None
    if masked_corp_no:
        masked_prefix = masked_corp_no.split("-")[0] if "-" in masked_corp_no else None

    conn = get_connection()
    try:
        candidates = []
        seen_ids = set()

        # 1. 완전일치
        rows = conn.execute(
            "SELECT * FROM clients WHERE client_name = ?",
            (payer_name,),
        ).fetchall()
        for r in rows:
            if r["id"] not in seen_ids:
                candidates.append(Client.from_row(r))
                seen_ids.add(r["id"])

        # 2. 정규화 일치
        rows = conn.execute(
            "SELECT * FROM clients WHERE normalized_name = ?",
            (normalized,),
        ).fetchall()
        for r in rows:
            if r["id"] not in seen_ids:
                candidates.append(Client.from_row(r))
                seen_ids.add(r["id"])

        # 3. 부분일치
        rows = conn.execute(
            "SELECT * FROM clients WHERE normalized_name LIKE ?",
            (f"%{normalized}%",),
        ).fetchall()
        for r in rows:
            if r["id"] not in seen_ids:
                candidates.append(Client.from_row(r))
                seen_ids.add(r["id"])

        # 4. 법인번호 보조 매칭
        if masked_prefix and not candidates:
            rows = conn.execute(
                "SELECT * FROM clients WHERE corporation_no LIKE ?",
                (f"{masked_prefix}-%",),
            ).fetchall()
            for r in rows:
                if r["id"] not in seen_ids:
                    candidates.append(Client.from_row(r))
                    seen_ids.add(r["id"])

        return candidates
    finally:
        conn.close()


def verify_corp_no_match(client: Client, masked_corp_no: str) -> bool:
    """선택한 거래처의 법인번호와 OCR 마스킹 법인번호 앞 6자리 일치 검증."""
    if not client.corporation_no or not masked_corp_no:
        return True  # 검증 불가 - 사용자 판단

    client_prefix = client.corporation_no.split("-")[0] if "-" in client.corporation_no else ""
    masked_prefix = masked_corp_no.split("-")[0] if "-" in masked_corp_no else ""

    return client_prefix == masked_prefix

