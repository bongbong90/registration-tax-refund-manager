"""
HWP 수정 + 통합 PDF 재생성 모듈.

동작 흐름:
1. 사건 폴더의 HWP 3종을 한/글에서 순차적으로 열기
2. 사용자가 한/글에서 직접 수정 후 저장
3. 저장 완료 확인 후 다음 파일로 진행
4. 3종 모두 완료되면 통합 PDF 재생성

GUI 연결 포인트:
- open_and_edit_hwp_files(): GUI에서 "HWP 수정" 버튼 클릭 시 호출
- regenerate_pdf(): GUI에서 "PDF 재생성" 버튼 클릭 시 호출
"""
import logging
import time
from pathlib import Path

import pythoncom
from win32com.client import Dispatch

from app.hwp.hwp_to_pdf import hwp_to_pdf
from app.utils.pdf_merger import build_refund_pdf

logger = logging.getLogger(__name__)


# ============================================================
# 한/글 인스턴스 관리 (hwp_filler.py와 동일 패턴)
# ============================================================

def _get_hwp_instance():
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


# ============================================================
# HWP 열기 + 사용자 수정 대기
# ============================================================

def open_hwp_for_edit(hwp_path: Path, wait_seconds: int = 300) -> dict:
    """
    HWP 파일을 한/글에서 열고 사용자 수정을 기다린다.
    사용자가 한/글에서 저장하고 닫으면 완료로 처리.

    Parameters:
        hwp_path: 수정할 HWP 파일 경로
        wait_seconds: 최대 대기 시간 (초, 기본 5분)

    Returns:
        {"success": bool, "modified": bool, "error": str | None}
    """
    result = {"success": False, "modified": False, "error": None}

    if not hwp_path.exists():
        result["error"] = f"HWP 파일 없음: {hwp_path}"
        return result

    mtime_before = hwp_path.stat().st_mtime

    hwp = None
    try:
        hwp = _get_hwp_instance()

        try:
            hwp.XHwpWindows.Item(0).Visible = True
        except Exception:
            pass

        if not _open_hwp_file(hwp, hwp_path):
            result["error"] = "HWP 파일 열기 실패"
            return result

        logger.info(f"한/글에서 열림: {hwp_path.name}")
        logger.info("사용자 수정 대기 중... (수정 후 저장하고 닫으세요)")

        elapsed = 0
        interval = 2
        while elapsed < wait_seconds:
            time.sleep(interval)
            elapsed += interval

            try:
                window_count = hwp.XHwpWindows.Count
                if window_count == 0:
                    break
            except Exception:
                break

        mtime_after = hwp_path.stat().st_mtime
        result["modified"] = mtime_after > mtime_before
        result["success"] = True

        if result["modified"]:
            logger.info(f"수정 감지됨: {hwp_path.name}")
        else:
            logger.info(f"수정 없음: {hwp_path.name}")

    except Exception as e:
        result["error"] = str(e)
        logger.exception(f"HWP 편집 중 예외: {e}")
    finally:
        if hwp:
            _quit_hwp(hwp)

    return result


# ============================================================
# HWP 3종 순차 열기 + 수정
# ============================================================

def open_and_edit_hwp_files(
    form22_path: Path,
    form27_path: Path,
    form14_path: Path,
    wait_seconds: int = 300,
) -> dict:
    """
    HWP 3종을 순차적으로 열어 사용자 수정을 받는다.
    22호 → 27호 → 14호 순서.

    Parameters:
        form22_path: 제22호 HWP 경로
        form27_path: 제27호 HWP 경로
        form14_path: 제14호 HWP 경로
        wait_seconds: 파일당 최대 대기 시간 (초)

    Returns:
        {
            "form22": open_hwp_for_edit 반환값,
            "form27": open_hwp_for_edit 반환값,
            "form14": open_hwp_for_edit 반환값,
            "all_success": bool,
            "any_modified": bool,
        }
    """
    results = {}

    for form_key, hwp_path in [
        ("form22", form22_path),
        ("form27", form27_path),
        ("form14", form14_path),
    ]:
        logger.info(f"[{form_key}] 수정 시작")
        results[form_key] = open_hwp_for_edit(hwp_path, wait_seconds)

        if not results[form_key]["success"]:
            logger.error(f"[{form_key}] 실패: {results[form_key]['error']}")
            break

    results["all_success"] = all(
        results.get(k, {}).get("success", False)
        for k in ["form22", "form27", "form14"]
    )
    results["any_modified"] = any(
        results.get(k, {}).get("modified", False)
        for k in ["form22", "form27", "form14"]
    )

    return results


# ============================================================
# 통합 PDF 재생성
# ============================================================

def regenerate_pdf(
    form22_hwp: Path,
    form27_hwp: Path,
    form14_hwp: Path,
    source_pdf: Path,
    output_pdf: Path,
    pdf_temp_dir: Path,
) -> dict:
    """
    HWP 3종을 PDF로 변환 후 납부확인서와 통합 PDF 재생성.

    Parameters:
        form22_hwp: 제22호 HWP 경로
        form27_hwp: 제27호 HWP 경로
        form14_hwp: 제14호 HWP 경로
        source_pdf: 납부확인서 원본 PDF 경로
        output_pdf: 통합 PDF 저장 경로
        pdf_temp_dir: 임시 PDF 저장 폴더

    Returns:
        {
            "success": bool,
            "output_pdf": Path,
            "total_pages": int,
            "error": str | None,
        }
    """
    result = {
        "success": False,
        "output_pdf": output_pdf,
        "total_pages": 0,
        "error": None,
    }

    pdf_temp_dir.mkdir(parents=True, exist_ok=True)

    pdf_paths = {}
    for form_key, hwp_path in [
        ("form22", form22_hwp),
        ("form27", form27_hwp),
        ("form14", form14_hwp),
    ]:
        pdf_path = pdf_temp_dir / hwp_path.with_suffix(".pdf").name
        r = hwp_to_pdf(hwp_path, pdf_path)

        if not r["success"]:
            result["error"] = f"{form_key} PDF 변환 실패: {r['error']}"
            logger.error(result["error"])
            return result

        pdf_paths[form_key] = pdf_path
        logger.info(f"{form_key} PDF 변환 완료")

    merge_result = build_refund_pdf(
        form22_pdf=pdf_paths["form22"],
        form27_pdf=pdf_paths["form27"],
        form14_pdf=pdf_paths["form14"],
        source_pdf=source_pdf,
        output_path=output_pdf,
    )

    if not merge_result["success"]:
        result["error"] = f"PDF 통합 실패: {merge_result['error']}"
        return result

    result["success"] = True
    result["total_pages"] = merge_result["total_pages"]
    logger.info(f"통합 PDF 재생성 완료: {output_pdf.name} ({result['total_pages']}페이지)")

    return result
