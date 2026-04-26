"""
PDF 통합 모듈.
pypdf를 사용해 여러 PDF를 순서대로 합쳐 단일 PDF 생성.
"""
import logging
from pathlib import Path

from pypdf import PdfWriter, PdfReader

logger = logging.getLogger(__name__)


def merge_pdfs(pdf_paths: list[Path], output_path: Path) -> dict:
    """
    여러 PDF를 순서대로 합쳐 단일 PDF 생성.

    Parameters:
        pdf_paths: 합칠 PDF 경로 리스트 (순서 중요)
        output_path: 출력 PDF 경로

    Returns:
        {
            "success": bool,
            "output_path": Path,
            "total_pages": int,
            "error": str | None,
        }
    """
    result = {
        "success": False,
        "output_path": output_path,
        "total_pages": 0,
        "error": None,
    }

    missing = [p for p in pdf_paths if not p.exists()]
    if missing:
        result["error"] = f"PDF 파일 없음: {[str(p) for p in missing]}"
        logger.error(result["error"])
        return result

    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        writer = PdfWriter()

        for pdf_path in pdf_paths:
            reader = PdfReader(str(pdf_path))
            for page in reader.pages:
                writer.add_page(page)
            logger.debug(f"추가: {pdf_path.name} ({len(reader.pages)}페이지)")

        result["total_pages"] = len(writer.pages)

        with open(output_path, "wb") as f:
            writer.write(f)

        result["success"] = True
        logger.info(
            f"PDF 통합 완료: {output_path.name} "
            f"({result['total_pages']}페이지, {len(pdf_paths)}개 파일)"
        )

    except Exception as e:
        result["error"] = str(e)
        logger.exception(f"PDF 통합 중 예외: {e}")

    return result


def build_refund_pdf(
    form22_pdf: Path,
    form27_pdf: Path,
    form14_pdf: Path,
    source_pdf: Path,
    output_path: Path,
) -> dict:
    """
    환급서류 통합 PDF 생성.
    순서: 22호 → 27호 → 14호 → 납부확인서

    Parameters:
        form22_pdf: 제22호 환급청구서 PDF
        form27_pdf: 제27호 양도요구서 PDF
        form14_pdf: 제14호 경정청구서 PDF
        source_pdf: 납부확인서 원본 PDF
        output_path: 통합 PDF 저장 경로

    Returns:
        merge_pdfs() 반환값
    """
    pdf_paths = [form22_pdf, form27_pdf, form14_pdf, source_pdf]

    logger.info("환급서류 통합 PDF 생성 시작")
    logger.info(f"  22호: {form22_pdf.name}")
    logger.info(f"  27호: {form27_pdf.name}")
    logger.info(f"  14호: {form14_pdf.name}")
    logger.info(f"  납부확인서: {source_pdf.name}")

    return merge_pdfs(pdf_paths, output_path)
