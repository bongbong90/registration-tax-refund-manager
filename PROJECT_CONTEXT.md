# 등록면허세 환급관리 프로그램 — PROJECT CONTEXT

## 프로젝트 기본 정보

- 위치: C:\Users\User\Desktop\refund_manager
- GitHub: bongbong90/registration-tax-refund-manager (private)
- 개발자: 법무사사무소 실무자 (코딩 비전문자)
- 스택: Python 3.13 / PySide6 / SQLite / PyMuPDF / PaddleOCR / pywin32
- 사무소: 다이렉트로합동법무사사무소 (개인사업자)

---

## 완료된 작업

### Phase 1-1: 기반 구축
- 폴더 구조 생성
- DB 스키마 설계 및 생성
- OCR 이식 (PaddleOCR)

### Phase 1-2: 거래처 마스터 CRUD
- 거래처 백엔드 서비스 구현
- clients 테이블 CRUD 완료

### Phase 1-3-A: 사무소 정보 서비스 + HWP 치환 엔진
- 사무소 정보 서비스 구현
- HWP 파일 내 치환 엔진 구현

### Phase 1-3-B: PDF 변환 + 통합
- HWP to PDF 변환 기능
- 통합 파이프라인 구성

### Phase 1-3-C: HWP 수정 + 통합 PDF 재생성
- HWP 수정 기능
- 통합 PDF 재생성

### Phase 1-4: 메인 UI 전면 재작성 (완료, 커밋: 5217944)
- app/ui/ 폴더 전면 재작성
- theme.py get_stylesheet() 함수로 QSS 통합 관리
- 사이드바: 260px 고정, #1B2A3B 네이비, QPalette 강제 지정
- 메뉴 아이콘 + 텍스트, 활성 시 #2E86AB 둥근 카드 하이라이트
- 진행현황: 카드형 위젯, 전체/진행중/완료 배지
- 상단 컨트롤: 검색창 + 검색버튼 + 상태 콤보박스 + 새 사건 버튼
- 메인 콘텐츠: 흰색 카드 패널, 빈 상태 안내 아이콘 + 문구
- 앱 아이콘: assets/icons/app_icon.ico 적용
- 사이드바 로고: assets/icons/sidebar_logo.png 적용
- Fusion 스타일 + 맑은 고딕 10pt 기본 폰트

### Phase 1-5: 기능 구현 (완료)

완료 항목:
- 새 사건 등록 다이얼로그 (case_create_dialog.py)
- 사건 목록 DB 연동 (테이블 실데이터 표시)
- 납세자명 검색 + 검색 버튼 (Enter 키 동작 포함)
- 상태 콤보박스 필터
- 진행현황 배지 숫자 자동 업데이트

완료 항목(추가):
- 사건 상세 다이얼로그 (기본정보/진행이력/메모 탭)
- 라이프사이클 7단계 상태 변경 버튼 + 날짜 입력 팝업
- 상태 변경 시 진행이력 자동 기록(case_events)
- 메인 테이블 더블클릭 → 사건 상세 모달 연결
- 우클릭 컨텍스트 메뉴 `사건 복사` + 새 사건 등록 프리필

버그 수정 완료:
- 달력 닫힘 시 빈 공간 잔존 문제 해결 (`setMaximumHeight` 방식)
- 상태 뱃지 렌더링 delegate 방식 정리 및 고정 스타일 적용
- 콤보박스 드롭다운 화살표 렌더링 스타일 보완

---

## 확정 스펙

### 컬러
- 사이드바 배경:            #1B2A3B
- 메뉴 활성:                #2E86AB
- 메뉴 호버:                #243447
- 앱 배경:                  #F0F2F5
- 콘텐츠 배경:              #FFFFFF
- 포인트 버튼:              #2E86AB
- 텍스트:                   #2D2D2D
- 서브텍스트:               #7F8C8D
- 테두리:                   #DDE1E7

### 폰트
- 기본: 맑은 고딕 10pt
- 앱 스타일: Fusion

### 창 크기
- 메인: 1280x780 (최소 1024x600)
- 사건등록 다이얼로그: 480x500px

### 라이프사이클 7단계
CREATED → SENT_TO_BANK → BANK_RETURNED → SUBMITTED → REFUND_DECIDED → DEPOSITED → CLOSED

### 상태 한글 매핑
- CREATED:         서류생성
- SENT_TO_BANK:    은행송부
- BANK_RETURNED:   은행회신
- SUBMITTED:       구청접수
- REFUND_DECIDED:  환급결정
- DEPOSITED:       입금확인
- CLOSED:          종결

### 상태 뱃지 색상
- 서류생성:                    배경 #E8F4FD / 텍스트 #2E86AB
- 은행송부, 은행회신, 구청접수: 배경 #FEF9E7 / 텍스트 #F39C12
- 환급결정, 입금확인:          배경 #E8F8F5 / 텍스트 #27AE60
- 종결:                        배경 #F2F3F4 / 텍스트 #7F8C8D

### 환급사유 확정 4종
대출취소 / 중복납부 / 착오납부 / 기타

### 사건 목록 테이블 컬럼 및 정렬
- 납부일 (110px 고정, 가운데 정렬)
- 납세자 (Stretch, 좌측 정렬)
- 세액 (110px 고정, 우측 정렬)
- 환급사유 (130px 고정, 가운데 정렬)
- 상태 (100px 고정, 가운데 정렬, delegate 방식 뱃지)

### 아이콘 및 로고 파일 위치
- assets/icons/app_icon.ico
- assets/icons/sidebar_logo.png
- assets/icons/taxrefund.ico
- assets/icons/taxrefund_icon_256.png
- assets/icons/taxrefund_logo_preview_dark.png

---

## 주요 파일 구조

refund_manager/
├ main.py
├ app/
│  ├ ui/
│  │  ├ main_window.py
│  │  ├ styles/
│  │  │  └ theme.py
│  │  ├ widgets/
│  │  │  ├ sidebar.py
│  │  │  ├ case_table.py
│  │  │  └ summary_widget.py
│  │  └ dialogs/
│  │     ├ case_create_dialog.py
│  │     └ case_detail_dialog.py
│  ├ database/
│  └ services/
├ assets/
│  └ icons/
└ tests/
   └ test_ui.py

---

## 미완료 및 추후 작업

### Phase 1-5 잔여
- 없음 (Phase 1-5 완료)

### 이후 Phase
- 거래처 관리 다이얼로그 UI 연결
- 사무소 정보 다이얼로그 UI 연결
- PDF 뷰어 (PyMuPDF 렌더링)
- HWP 서류 자동생성 연결
- 사건 상세 다이얼로그 내 파일/문서 이력 연동 확장

---

## 운영 규칙

- 작업 완료 시마다 이 파일 업데이트 후 커밋에 포함
- Phase 완료 시: 전체 섹션 업데이트
- 중간 수정 시: 해당 항목만 수정
- 확정 스펙 변경 시: 즉시 반영
- 노션 정리는 별도 채팅방에서 별도 요청 시에만 수행
