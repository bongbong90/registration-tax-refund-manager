-- 거래처 마스터
CREATE TABLE IF NOT EXISTS clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_name TEXT NOT NULL,
    normalized_name TEXT NOT NULL,
    corporation_no TEXT,
    business_no TEXT,
    representative_name TEXT,
    address TEXT,
    email TEXT,
    manager_name TEXT,
    manager_phone TEXT,
    memo TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_clients_normalized ON clients(normalized_name);
CREATE INDEX IF NOT EXISTS idx_clients_corp_no ON clients(corporation_no);

-- 환급 사건 (다음 Phase에서 사용, 미리 정의)
CREATE TABLE IF NOT EXISTS refund_cases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER,
    payer_name TEXT,
    address TEXT,
    tax_item_code TEXT,
    tax_no TEXT,
    levy_period TEXT,
    tax_base INTEGER,
    tax_total INTEGER,
    paid_date DATE,
    issue_authority TEXT,
    refund_reason TEXT,
    refund_reason_detail TEXT,
    status TEXT DEFAULT 'CREATED',
    case_folder_path TEXT,
    source_pdf_path TEXT,
    memo TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(id)
);

CREATE INDEX IF NOT EXISTS idx_cases_client ON refund_cases(client_id);
CREATE INDEX IF NOT EXISTS idx_cases_paid_date ON refund_cases(paid_date);
CREATE INDEX IF NOT EXISTS idx_cases_status ON refund_cases(status);

-- 사건 이벤트 이력
CREATE TABLE IF NOT EXISTS case_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    event_date DATE NOT NULL,
    memo TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (case_id) REFERENCES refund_cases(id)
);

CREATE INDEX IF NOT EXISTS idx_events_case ON case_events(case_id);

-- 사건별 생성 문서
CREATE TABLE IF NOT EXISTS case_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id INTEGER NOT NULL,
    doc_type TEXT NOT NULL,
    file_path TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (case_id) REFERENCES refund_cases(id)
);
