"""
HWP 수정 + PDF 재생성 기능 검증 스크립트.

사전 조건:
    - data/hwp_test_output/ 에 HWP 3종 존재
    - data/sample_pdf/ 에 납부확인서 샘플 PDF 존재

사용:
    python -m tests.test_hwp_editor

동작:
    1. 22호 HWP 한/글로 열림 → 봉봉이 직접 수정 후 저장하고 닫기
    2. 27호 HWP 열림 → 수정 또는 그냥 닫기
    3. 14호 HWP 열림 → 수정 또는 그냥 닫기
    4. 통합 PDF 재생성 후 결과 확인
"""
import sys
from pathlib import Path

from app.hwp.hwp_editor import open_and_edit_hwp_files, regenerate_pdf

PROJECT_ROOT = Path(__file__).parent.parent
HWP_TEST_DIR = PROJECT_ROOT / "data" / "hwp_test_output"
PDF_REGEN_DIR = PROJECT_ROOT / "data" / "pdf_regen_output"
PDF_TEMP_DIR = PROJECT_ROOT / "data" / "pdf_regen_temp"
SAMPLE_PDF_DIR = PROJECT_ROOT / "data" / "sample_pdf"


def find_test_hwp(form_key: str) -> Path | None:
    files = list(HWP_TEST_DIR.glob(f"*{form_key}*.hwp"))
    return files[0] if files else None


def find_sample_pdf() -> Path | None:
    files = list(SAMPLE_PDF_DIR.glob("*.pdf")) + \
            list(SAMPLE_PDF_DIR.glob("*.PDF"))
    return files[0] if files else None


def main():
    print("=" * 60)
    print("HWP 수정 + PDF 재생성 검증")
    print("=" * 60)

    form22 = find_test_hwp("form22")
    form27 = find_test_hwp("form27")
    form14 = find_test_hwp("form14")
    sample_pdf = find_sample_pdf()

    for name, path in [
        ("22호 HWP", form22), ("27호 HWP", form27),
        ("14호 HWP", form14), ("납부확인서 PDF", sample_pdf),
    ]:
        status = f"✓ {path.name}" if path else "✗ 없음"
        print(f"  {name}: {status}")

    if not all([form22, form27, form14, sample_pdf]):
        print("\n✗ 필요한 파일 없음. 중단.")
        sys.exit(1)

    # HWP 순차 열기 + 수정
    print("\n[1] HWP 3종 순차 열기")
    print("    각 파일이 열리면 수정 후 저장하고 닫으세요.")
    print("    수정 없이 그냥 닫아도 됩니다.\n")

    edit_results = open_and_edit_hwp_files(
        form22_path=form22,
        form27_path=form27,
        form14_path=form14,
        wait_seconds=600,  # 파일당 최대 10분 대기
    )

    for form_key in ["form22", "form27", "form14"]:
        r = edit_results.get(form_key, {})
        modified = "수정됨" if r.get("modified") else "수정 없음"
        status = "✓" if r.get("success") else "✗"
        print(f"  {status} {form_key}: {modified}")

    if not edit_results["all_success"]:
        print("\n✗ HWP 편집 실패. 중단.")
        sys.exit(1)

    # PDF 재생성
    print("\n[2] 통합 PDF 재생성")
    output_pdf = PDF_REGEN_DIR / "테스트_재생성_통합.pdf"

    result = regenerate_pdf(
        form22_hwp=form22,
        form27_hwp=form27,
        form14_hwp=form14,
        source_pdf=sample_pdf,
        output_pdf=output_pdf,
        pdf_temp_dir=PDF_TEMP_DIR,
    )

    print("=" * 60)
    if result["success"]:
        print(f"✓ 통합 PDF 재생성 완료")
        print(f"  경로: {result['output_pdf']}")
        print(f"  총 페이지: {result['total_pages']}페이지")
    else:
        print(f"✗ 실패: {result['error']}")
    print("=" * 60)


if __name__ == "__main__":
    main()
