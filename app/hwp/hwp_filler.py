"""
HWP 치환 엔진.
한/글 COM 자동화(pywin32)를 사용해 HWP 템플릿의 치환자를 실제 값으로 교체.

검증 완료:
- 방법 1 (기본 AllReplace) 채택
- 한/글 2018에서 표 셀 자동 줄바꿈 치환자도 정상 인식 확인
- Open() 다중 시그니처 fallback 적용 (한/글 버전 호환)
- 보안 모듈 AutomationModule 등록 시도

치환자 규칙:
- 표기: {{필드명}} (이중 중괄호, 한글)
- 예: {{납세자_명칭}}, {{환급금}}, {{청구일}}
"""
import shutil
import logging
from pathlib import Path
from datetime import date

import pythoncom
from win32com.client import Dispatch

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent.parent
TEMPLATE_DIR = PROJECT_ROOT / "templates" / "hwp"

TEMPLATE_FILES = {
    "form22": "제22호_환급청구서.hwp",
    "form14": "제14호_경정청구서.hwp",
    "form27": "제27호_양도요구서.hwp",
}


# ============================================================
# 한/글 인스턴스 관리
# ============================================================

def _get_hwp_instance():
    """한/글 COM 인스턴스 생성. 보안 모듈 등록 시도."""
    pythoncom.CoInitialize()
    hwp = Dispatch("HWPFrame.HwpObject")

    for module_name in ["AutomationModule", "FilePathCheckDLL"]:
        try:
            hwp.RegisterModule("FilePathCheckDLL", module_name)
            logger.debug(f"보안 모듈 등록 성공: {module_name}")
            break
        except Exception as e:
            logger.debug(f"보안 모듈 등록 실패 ({module_name}): {e}")

    return hwp


def _open_hwp_file(hwp, file_path: Path) -> bool:
    """
    한/글 버전 호환 Open 호출.
    3-인자 → 2-인자 → 1-인자 순서로 시도.
    """
    abs_path = str(file_path.resolve())

    for args in [
        (abs_path, "HWP", "forceopen:true"),
        (abs_path, "HWP"),
        (abs_path,),
    ]:
        try:
            hwp.Open(*args)
            logger.debug(f"Open 성공 ({len(args)}-인자): {abs_path}")
            return True
        except Exception as e:
            logger.debug(f"Open 실패 ({len(args)}-인자): {e}")

    logger.error(f"모든 Open 시도 실패: {abs_path}")
    return False


def _save_hwp_file(hwp, file_path: Path) -> bool:
    """
    한/글 버전 호환 SaveAs 호출.
    3-인자 → 2-인자 → 1-인자 순서로 시도.
    """
    abs_path = str(file_path.resolve())

    for args in [
        (abs_path, "HWP", ""),
        (abs_path, "HWP"),
        (abs_path,),
    ]:
        try:
            hwp.SaveAs(*args)
            logger.debug(f"SaveAs 성공 ({len(args)}-인자): {abs_path}")
            return True
        except Exception as e:
            logger.debug(f"SaveAs 실패 ({len(args)}-인자): {e}")

    logger.error(f"모든 SaveAs 시도 실패: {abs_path}")
    return False


def _quit_hwp(hwp):
    """한/글 종료. 실패해도 예외 무시."""
    try:
        hwp.Quit()
    except Exception:
        pass


# ============================================================
# 치환 핵심 함수
# ============================================================

def _replace_placeholder(hwp, placeholder: str, value: str) -> bool:
    """
    단일 치환자 치환.
    방법 1 (기본 AllReplace) 사용 — 검증 완료.
    반환: 성공 여부
    """
    try:
        hwp.HAction.GetDefault(
            "AllReplace", hwp.HParameterSet.HFindReplace.HSet
        )
        hwp.HParameterSet.HFindReplace.FindString = placeholder
        hwp.HParameterSet.HFindReplace.ReplaceString = value
        hwp.HParameterSet.HFindReplace.IgnoreMessage = 1
        hwp.HParameterSet.HFindReplace.UseWildCards = 0
        hwp.HParameterSet.HFindReplace.MatchCase = 0
        ret = hwp.HAction.Execute(
            "AllReplace", hwp.HParameterSet.HFindReplace.HSet
        )
        return bool(ret)
    except Exception as e:
        logger.warning(f"치환 실패 [{placeholder}]: {e}")
        return False


def _replace_all(hwp, replacements: dict) -> dict:
    """
    전체 치환자 일괄 치환.
    replacements: {"{{치환자}}": "값", ...}
    반환: {"{{치환자}}": True/False, ...}
    """
    results = {}
    for placeholder, value in replacements.items():
        if value is None:
            value = ""
        results[placeholder] = _replace_placeholder(hwp, placeholder, str(value))
    return results


# ============================================================
# 치환 데이터 빌더
# ============================================================

def build_replacement_data(case_data: dict, client_data: dict, office_data: dict) -> dict:
    """
    사건/거래처/사무소 데이터를 치환자 딕셔너리로 변환.

    Parameters:
        case_data: refund_cases 테이블 데이터 (또는 동일 구조 dict)
        client_data: clients 테이블 데이터 (또는 동일 구조 dict)
        office_data: office_info.json 데이터

    Returns:
        {"{{납세자_명칭}}": "주식회사 케이뱅크", ...}
    """
    paid_date_str = case_data.get("paid_date", "")
    paid_year = paid_month = paid_day = ""
    if paid_date_str:
        parts = str(paid_date_str).split("-")
        if len(parts) == 3:
            paid_year, paid_month, paid_day = parts

    claim_date = case_data.get("claim_date") or date.today().strftime("%Y년 %m월 %d일")

    if paid_date_str and len(paid_date_str) == 10:
        parts = paid_date_str.split("-")
        cause_date = f"{parts[0]}년 {parts[1]}월 {parts[2]}일"
    else:
        cause_date = paid_date_str

    return {
        # OCR 추출값
        "{{납세자_명칭}}": client_data.get("client_name", ""),
        "{{납세자_대표자}}": client_data.get("representative_name", ""),
        "{{납세자_법인번호}}": client_data.get("corporation_no", ""),
        "{{납세자_사업자번호}}": client_data.get("business_no", ""),
        "{{납세자_주소}}": client_data.get("address", ""),
        "{{납세자_이메일}}": client_data.get("email", ""),
        "{{세목}}": case_data.get("tax_item_code", ""),
        "{{부과연월}}": case_data.get("levy_period", ""),
        "{{과세번호}}": case_data.get("tax_no", ""),
        "{{과세표준}}": case_data.get("tax_base", ""),
        "{{환급금}}": case_data.get("tax_total", ""),
        "{{납부일_연}}": paid_year,
        "{{납부일_월}}": paid_month,
        "{{납부일_일}}": paid_day,
        "{{발급지자체}}": case_data.get("issue_authority", ""),
        # 사용자 입력
        "{{환급사유}}": case_data.get("refund_reason", ""),
        "{{청구일}}": claim_date,
        "{{사유발생일}}": cause_date,
        # 사무소 고정값
        "{{사무소_명칭}}": office_data.get("사무소_명칭", ""),
        "{{사무소_법무사}}": office_data.get("사무소_법무사", ""),
        "{{사무소_대표}}": office_data.get("사무소_대표", ""),
        "{{사무소_주민번호}}": office_data.get("사무소_주민번호", ""),
        "{{사무소_사업자번호}}": office_data.get("사무소_사업자번호", ""),
        "{{사무소_주소}}": office_data.get("사무소_주소", ""),
        "{{사무소_전화}}": office_data.get("사무소_전화", ""),
        "{{사무소_이메일}}": office_data.get("사무소_이메일", ""),
        "{{사무소_은행}}": office_data.get("사무소_은행", ""),
        "{{사무소_계좌}}": office_data.get("사무소_계좌", ""),
        "{{위임받은자_관계}}": office_data.get("위임받은자_관계", "법무사"),
    }


# ============================================================
# HWP 파일 생성 (메인 공개 API)
# ============================================================

def fill_hwp(
    form_key: str,
    replacements: dict,
    output_path: Path,
) -> dict:
    """
    HWP 템플릿 복사 후 치환자 채워 저장.

    Parameters:
        form_key: "form22" | "form14" | "form27"
        replacements: build_replacement_data() 반환값
        output_path: 생성할 HWP 파일 경로

    Returns:
        {
            "success": bool,
            "output_path": Path,
            "results": {"{{치환자}}": True/False, ...},
            "unfilled": ["{{치환자}}", ...],
            "error": str | None,
        }
    """
    result = {
        "success": False,
        "output_path": output_path,
        "results": {},
        "unfilled": [],
        "error": None,
    }

    template_filename = TEMPLATE_FILES.get(form_key)
    if not template_filename:
        result["error"] = f"알 수 없는 form_key: {form_key}"
        logger.error(result["error"])
        return result

    template_path = TEMPLATE_DIR / template_filename
    if not template_path.exists():
        result["error"] = f"템플릿 파일 없음: {template_path}"
        logger.error(result["error"])
        return result

    output_path.parent.mkdir(parents=True, exist_ok=True)

    shutil.copy(template_path, output_path)
    logger.info(f"템플릿 복사: {template_path} → {output_path}")

    hwp = None
    try:
        hwp = _get_hwp_instance()

        if not _open_hwp_file(hwp, output_path):
            result["error"] = "HWP 파일 열기 실패"
            return result

        replace_results = _replace_all(hwp, replacements)
        result["results"] = replace_results

        result["unfilled"] = [
            k for k, v in replace_results.items() if not v
        ]

        if not _save_hwp_file(hwp, output_path):
            result["error"] = "HWP 파일 저장 실패"
            return result

        result["success"] = True
        logger.info(f"HWP 생성 완료: {output_path}")

    except Exception as e:
        result["error"] = str(e)
        logger.exception(f"HWP 생성 중 예외 발생: {e}")
    finally:
        if hwp:
            _quit_hwp(hwp)

    return result


def fill_all_forms(
    case_data: dict,
    client_data: dict,
    office_data: dict,
    output_dir: Path,
    file_prefix: str = "",
) -> dict:
    """
    3종 HWP 양식 일괄 생성.

    Parameters:
        case_data: 환급 사건 데이터
        client_data: 거래처 데이터
        office_data: 사무소 정보
        output_dir: 생성 파일 저장 폴더
        file_prefix: 파일명 앞에 붙을 접두사 (예: "20250725_케이뱅크")

    Returns:
        {
            "form22": fill_hwp() 반환값,
            "form14": fill_hwp() 반환값,
            "form27": fill_hwp() 반환값,
            "all_success": bool,
        }
    """
    replacements = build_replacement_data(case_data, client_data, office_data)

    prefix = f"{file_prefix}_" if file_prefix else ""

    results = {}
    for form_key, filename in TEMPLATE_FILES.items():
        form_no = filename.split("호")[0].replace("제", "")
        output_filename = f"{prefix}제{form_no}호_{form_key}.hwp"
        output_path = output_dir / output_filename

        results[form_key] = fill_hwp(form_key, replacements, output_path)

    results["all_success"] = all(
        r["success"] for r in results.values() if isinstance(r, dict)
    )

    return results
