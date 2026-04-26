"""
PDF 변환 + 통합 파이프라인 검증 스크립트.
Phase 1-3-A에서 생성된 테스트 HWP 파일을 사용.

사전 조건:
    - python -m tests.test_hwp_filler 실행 완료
    - data/hwp_test_output/ 에 HWP 3종 존재
    - 납부확인서 샘플 PDF 1개 (data/sample_pdf/ 에 복사해둘 것)

사용:
    python -m tests.test_pdf_pipeline
"""
import sys
from pathlib import Path

from app.hwp.hwp_to_pdf import hwp_to_pdf
from app.utils.pdf_merger import build_refund_pdf

PROJECT_ROOT = Path(__file__).parent.parent
HWP_TEST_DIR = PROJECT_ROOT / "data" / "hwp_test_output"
PDF_TEST_DIR = PROJECT_ROOT / "data" / "pdf_test_output"
SAMPLE_PDF_DIR = PROJECT_ROOT / "data" / "sample_pdf"


def find_test_hwp(form_key: str) -> Path | None:
    """테스트 HWP 파일 찾기."""
    pattern = f"*{form_key}*.hwp"
    files = list(HWP_TEST_DIR.glob(pattern))
    return files[0] if files else None


def find_sample_pdf() -> Path | None:
    """납부확인서 샘플 PDF 찾기."""
    files = list(SAMPLE_PDF_DIR.glob("*.pdf")) + list(SAMPLE_PDF_DIR.glob("*.PDF"))
    return files[0] if files else None


def main():
    print("=" * 60)
    print("PDF 변환 + 통합 파이프라인 검증")
    print("=" * 60)

    # 1. 사전 조건 확인
    print("\n[1] 사전 조건 확인")

    form22_hwp = find_test_hwp("form22")
    form27_hwp = find_test_hwp("form27")
    form14_hwp = find_test_hwp("form14")
    sample_pdf = find_sample_pdf()

    for name, path in [
        ("22호 HWP", form22_hwp),
        ("27호 HWP", form27_hwp),
        ("14호 HWP", form14_hwp),
        ("납부확인서 PDF", sample_pdf),
    ]:
        status = f"✓ {path.name}" if path else "✗ 없음"
        print(f"  {name}: {status}")

    if not all([form22_hwp, form27_hwp, form14_hwp]):
        print("\n  ✗ HWP 파일 없음. 먼저 python -m tests.test_hwp_filler 실행 필요.")
        sys.exit(1)

    if not sample_pdf:
        print("\n  ✗ 납부확인서 샘플 PDF 없음.")
        print(f"    data/sample_pdf/ 폴더에 납부확인서 PDF 1개 복사 후 재실행.")
        sys.exit(1)

    # 2. HWP → PDF 변환
    print("\n[2] HWP → PDF 변환 (한/글 보안 다이얼로그 뜨면 [모두 허용])")
    PDF_TEST_DIR.mkdir(parents=True, exist_ok=True)

    pdf_results = {}
    for form_key, hwp_path in [
        ("form22", form22_hwp),
        ("form27", form27_hwp),
        ("form14", form14_hwp),
    ]:
        pdf_path = PDF_TEST_DIR / hwp_path.with_suffix(".pdf").name
        r = hwp_to_pdf(hwp_path, pdf_path)
        pdf_results[form_key] = r
        status = "✓ 성공" if r["success"] else f"✗ 실패: {r['error']}"
        print(f"  {form_key}: {status}")

    if not all(r["success"] for r in pdf_results.values()):
        print("\n  ✗ PDF 변환 실패. 중단.")
        sys.exit(1)

    # 3. PDF 통합
    print("\n[3] PDF 통합 (22호→27호→14호→납부확인서)")

    output_pdf = PDF_TEST_DIR / "테스트_국민은행_20260424_통합.pdf"

    result = build_refund_pdf(
        form22_pdf=pdf_results["form22"]["pdf_path"],
        form27_pdf=pdf_results["form27"]["pdf_path"],
        form14_pdf=pdf_results["form14"]["pdf_path"],
        source_pdf=sample_pdf,
        output_path=output_pdf,
    )

    print("=" * 60)
    if result["success"]:
        print(f"✓ 통합 PDF 생성 완료")
        print(f"  경로: {result['output_path']}")
        print(f"  총 페이지: {result['total_pages']}페이지")
    else:
        print(f"✗ 통합 PDF 생성 실패: {result['error']}")
    print("=" * 60)

    print(f"\n생성된 파일: {PDF_TEST_DIR}")
    print("통합 PDF를 열어 페이지 순서와 내용을 직접 확인하세요.")
    print("순서: 22호(2페이지) → 27호 → 14호 → 납부확인서")


if __name__ == "__main__":
    main()
