"""
HWP → PDF 변환 모듈.
한/글 COM 자동화(pywin32)를 사용해 HWP 파일을 PDF로 변환.
"""
import logging
from pathlib import Path

import pythoncom
from win32com.client import Dispatch

logger = logging.getLogger(__name__)


def _get_hwp_instance():
    """한/글 COM 인스턴스 생성."""
    pythoncom.CoInitialize()
    hwp = Dispatch("HWPFrame.HwpObject")

    for module_name in ["AutomationModule", "FilePathCheckDLL"]:
        try:
            hwp.RegisterModule("FilePathCheckDLL", module_name)
            break
        except Exception:
            pass

    return hwp


def _open_hwp_file(hwp, file_path: Path) -> bool:
    """한/글 버전 호환 Open 호출. 3→2→1인자 fallback."""
    abs_path = str(file_path.resolve())

    for args in [
        (abs_path, "HWP", "forceopen:true"),
        (abs_path, "HWP"),
        (abs_path,),
    ]:
        try:
            hwp.Open(*args)
            return True
        except Exception:
            continue

    logger.error(f"Open 실패: {abs_path}")
    return False


def _quit_hwp(hwp):
    try:
        hwp.Quit()
    except Exception:
        pass


def hwp_to_pdf(hwp_path: Path, pdf_path: Path) -> dict:
    """
    HWP 파일을 PDF로 변환.

    Parameters:
        hwp_path: 변환할 HWP 파일 경로
        pdf_path: 저장할 PDF 파일 경로

    Returns:
        {"success": bool, "pdf_path": Path, "error": str | None}
    """
    result = {"success": False, "pdf_path": pdf_path, "error": None}

    if not hwp_path.exists():
        result["error"] = f"HWP 파일 없음: {hwp_path}"
        logger.error(result["error"])
        return result

    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    abs_pdf_path = str(pdf_path.resolve())

    hwp = None
    try:
        hwp = _get_hwp_instance()

        if not _open_hwp_file(hwp, hwp_path):
            result["error"] = "HWP 파일 열기 실패"
            return result

        # PDF로 저장 (3→2→1인자 fallback)
        saved = False
        for args in [
            (abs_pdf_path, "PDF", ""),
            (abs_pdf_path, "PDF"),
            (abs_pdf_path,),
        ]:
            try:
                hwp.SaveAs(*args)
                saved = True
                break
            except Exception:
                continue

        if not saved:
            result["error"] = "PDF 저장 실패"
            return result

        if not pdf_path.exists():
            result["error"] = f"PDF 파일이 생성되지 않음: {pdf_path}"
            return result

        result["success"] = True
        logger.info(f"PDF 변환 완료: {hwp_path.name} → {pdf_path.name}")

    except Exception as e:
        result["error"] = str(e)
        logger.exception(f"PDF 변환 중 예외: {e}")
    finally:
        if hwp:
            _quit_hwp(hwp)

    return result


def convert_all_hwp_to_pdf(hwp_dir: Path, pdf_dir: Path) -> dict:
    """
    폴더 내 HWP 파일 전체를 PDF로 변환.

    Parameters:
        hwp_dir: HWP 파일들이 있는 폴더
        pdf_dir: PDF 저장 폴더

    Returns:
        {"results": {파일명: hwp_to_pdf 반환값}, "all_success": bool}
    """
    results = {}

    hwp_files = sorted(hwp_dir.glob("*.hwp"))
    if not hwp_files:
        logger.warning(f"HWP 파일 없음: {hwp_dir}")
        return {"results": {}, "all_success": True}

    for hwp_path in hwp_files:
        pdf_path = pdf_dir / hwp_path.with_suffix(".pdf").name
        results[hwp_path.name] = hwp_to_pdf(hwp_path, pdf_path)

    all_success = all(r["success"] for r in results.values())
    return {"results": results, "all_success": all_success}
