"""
HWP 치환 동작 검증 테스트.

목적: 한/글 2014가 표 셀의 자동 줄바꿈 치환자를 어떻게 처리하는지 실측.

실행:
    python -m scripts.test_hwp_replace

요구사항:
    - 한/글 2014 이상 설치
    - templates/hwp/제22호_환급청구서.hwp 파일 존재
"""
import shutil
import sys
import time
from pathlib import Path

import pythoncom
from win32com.client import Dispatch


PROJECT_ROOT = Path(__file__).parent.parent
TEMPLATE_PATH = PROJECT_ROOT / "templates" / "hwp" / "제22호_환급청구서.hwp"
TEST_DIR = PROJECT_ROOT / "data" / "hwp_test"


def setup_test_files() -> dict:
    """원본 양식 보호를 위해 테스트별 복사본 생성."""
    TEST_DIR.mkdir(parents=True, exist_ok=True)

    methods = [
        "method1_default",
        "method2_several_words",
        "method3_regex",
        "method4_extended_options",
    ]

    test_files = {}
    for method in methods:
        dest = TEST_DIR / f"{method}.hwp"
        shutil.copy(TEMPLATE_PATH, dest)
        test_files[method] = dest

    return test_files


def get_hwp_instance():
    """?/? ???? ??. ?? ?? ?? ??."""
    pythoncom.CoInitialize()
    hwp = Dispatch("HWPFrame.HwpObject")

    # ?? ?? ?? (??? Open ?? ??, ???? ??)
    try:
        hwp.RegisterModule("FilePathCheckDLL", "FilePathCheckerModule")
    except Exception as e:
        print(f"  [??] ?? ?? ?? ?? (?? ??): {e}")

    # ?/? ? ??? (??? ? ?? ???)
    try:
        hwp.XHwpWindows.Item(0).Visible = True
    except Exception:
        pass

    return hwp


def open_hwp_file(hwp, file_path: Path) -> bool:
    """
    ?/? ?? ?? Open ??.
    ?? ????? ?? ???? ?? ?? ???? ??? ??.
    """
    abs_path = str(file_path.resolve())

    # ?? 1: 3-?? (?? ??)
    e1 = None
    try:
        hwp.Open(abs_path, "HWP", "forceopen:true")
        return True
    except Exception as exc:
        e1 = exc

    # ?? 2: 2-??
    e2 = None
    try:
        hwp.Open(abs_path, "HWP")
        return True
    except Exception as exc:
        e2 = exc

    # ?? 3: 1-?? (???)
    try:
        hwp.Open(abs_path)
        return True
    except Exception as e3:
        print(f"  [??] ?? Open ?? ??")
        print(f"    3-??: {e1}")
        print(f"    2-??: {e2}")
        print(f"    1-??: {e3}")
        return False

def test_method_1_default(hwp_path: Path) -> dict:
    """방법 1: 기본 AllReplace (옵션 없음)."""
    print("\n" + "=" * 60)
    print("[방법 1] 기본 AllReplace (옵션 없이 그대로)")
    print("=" * 60)

    hwp = get_hwp_instance()
    result = {"method": "default", "replacements": {}}

    try:
        if not open_hwp_file(hwp, hwp_path):
            result["error"] = "Open ??"
            return result

        replacements = [
            ("{{세목}}", "002"),
            ("{{부과연월}}", "2026.4"),
            ("{{과세번호}}", "007794"),
            ("{{납부일_일}}", "24"),
            ("{{환급금}}", "201,600"),
            ("{{납세자_명칭}}", "주식회사 테스트"),
        ]

        for find_str, replace_str in replacements:
            try:
                hwp.HAction.GetDefault("AllReplace", hwp.HParameterSet.HFindReplace.HSet)
                hwp.HParameterSet.HFindReplace.FindString = find_str
                hwp.HParameterSet.HFindReplace.ReplaceString = replace_str
                hwp.HParameterSet.HFindReplace.IgnoreMessage = 1
                ret = hwp.HAction.Execute("AllReplace", hwp.HParameterSet.HFindReplace.HSet)

                result["replacements"][find_str] = bool(ret)
                print(f"  {find_str} -> {replace_str}: {'✓ 성공' if ret else '✗ 실패'}")
            except Exception as e:
                result["replacements"][find_str] = False
                print(f"  {find_str}: ✗ 예외 - {e}")

        # 결과 저장
        abs_path = str(hwp_path.resolve())
        try:
            hwp.SaveAs(abs_path, "HWP", "")
        except Exception:
            try:
                hwp.SaveAs(abs_path, "HWP")
            except Exception:
                hwp.SaveAs(abs_path)

    except Exception as e:
        print(f"  [에러] 처리 실패: {e}")
        result["error"] = str(e)
    finally:
        try:
            hwp.Quit()
        except Exception:
            pass

    return result


def test_method_2_several_words(hwp_path: Path) -> dict:
    """방법 2: SeveralWords 옵션 (여러 단어 = 줄바꿈/공백 흡수)."""
    print("\n" + "=" * 60)
    print("[방법 2] SeveralWords 옵션 활성화")
    print("=" * 60)

    hwp = get_hwp_instance()
    result = {"method": "several_words", "replacements": {}}

    try:
        if not open_hwp_file(hwp, hwp_path):
            result["error"] = "Open ??"
            return result

        replacements = [
            ("{{세목}}", "002"),
            ("{{부과연월}}", "2026.4"),
            ("{{과세번호}}", "007794"),
            ("{{납부일_일}}", "24"),
            ("{{환급금}}", "201,600"),
            ("{{납세자_명칭}}", "주식회사 테스트"),
        ]

        for find_str, replace_str in replacements:
            try:
                hwp.HAction.GetDefault("AllReplace", hwp.HParameterSet.HFindReplace.HSet)
                hwp.HParameterSet.HFindReplace.FindString = find_str
                hwp.HParameterSet.HFindReplace.ReplaceString = replace_str
                hwp.HParameterSet.HFindReplace.IgnoreMessage = 1
                hwp.HParameterSet.HFindReplace.SeveralWords = 1  # 핵심
                hwp.HParameterSet.HFindReplace.UseWildCards = 0
                hwp.HParameterSet.HFindReplace.MatchCase = 0
                ret = hwp.HAction.Execute("AllReplace", hwp.HParameterSet.HFindReplace.HSet)

                result["replacements"][find_str] = bool(ret)
                print(f"  {find_str} -> {replace_str}: {'✓ 성공' if ret else '✗ 실패'}")
            except Exception as e:
                result["replacements"][find_str] = False
                print(f"  {find_str}: ✗ 예외 - {e}")

        abs_path = str(hwp_path.resolve())
        try:
            hwp.SaveAs(abs_path, "HWP", "")
        except Exception:
            try:
                hwp.SaveAs(abs_path, "HWP")
            except Exception:
                hwp.SaveAs(abs_path)

    except Exception as e:
        print(f"  [에러] 처리 실패: {e}")
        result["error"] = str(e)
    finally:
        try:
            hwp.Quit()
        except Exception:
            pass

    return result


def test_method_3_regex(hwp_path: Path) -> dict:
    """방법 3: 정규식 모드 (UseRegExp = 1)."""
    print("\n" + "=" * 60)
    print("[방법 3] 정규식 모드 활성화")
    print("=" * 60)

    hwp = get_hwp_instance()
    result = {"method": "regex", "replacements": {}}

    try:
        if not open_hwp_file(hwp, hwp_path):
            result["error"] = "Open ??"
            return result

        # 정규식 모드: 치환자 글자 사이 공백/줄바꿈 허용
        # \{\{ 와 \}\} 사이에 [\s]* 삽입
        replacements = [
            (r"\{\{[\s]*세목[\s]*\}\}", "002"),
            (r"\{\{[\s]*부과연월[\s]*\}\}", "2026.4"),
            (r"\{\{[\s]*과세번호[\s]*\}\}", "007794"),
            (r"\{\{[\s]*납부일_일[\s]*\}\}", "24"),
            (r"\{\{[\s]*환급금[\s]*\}\}", "201,600"),
            (r"\{\{[\s]*납세자_명칭[\s]*\}\}", "주식회사 테스트"),
        ]

        for find_pattern, replace_str in replacements:
            try:
                hwp.HAction.GetDefault("AllReplace", hwp.HParameterSet.HFindReplace.HSet)
                hwp.HParameterSet.HFindReplace.FindString = find_pattern
                hwp.HParameterSet.HFindReplace.ReplaceString = replace_str
                hwp.HParameterSet.HFindReplace.IgnoreMessage = 1
                hwp.HParameterSet.HFindReplace.UseRegExp = 1  # 핵심
                hwp.HParameterSet.HFindReplace.MatchCase = 0
                ret = hwp.HAction.Execute("AllReplace", hwp.HParameterSet.HFindReplace.HSet)

                result["replacements"][find_pattern] = bool(ret)
                print(f"  {find_pattern} -> {replace_str}: {'✓ 성공' if ret else '✗ 실패'}")
            except Exception as e:
                result["replacements"][find_pattern] = False
                print(f"  {find_pattern}: ✗ 예외 - {e}")

        abs_path = str(hwp_path.resolve())
        try:
            hwp.SaveAs(abs_path, "HWP", "")
        except Exception:
            try:
                hwp.SaveAs(abs_path, "HWP")
            except Exception:
                hwp.SaveAs(abs_path)

    except Exception as e:
        print(f"  [에러] 처리 실패: {e}")
        result["error"] = str(e)
    finally:
        try:
            hwp.Quit()
        except Exception:
            pass

    return result


def test_method_4_extended_options(hwp_path: Path) -> dict:
    """방법 4: 모든 옵션 조합 (SeveralWords + AllWordForms + 기타)."""
    print("\n" + "=" * 60)
    print("[방법 4] 다중 옵션 조합")
    print("=" * 60)

    hwp = get_hwp_instance()
    result = {"method": "extended_options", "replacements": {}}

    try:
        if not open_hwp_file(hwp, hwp_path):
            result["error"] = "Open ??"
            return result

        replacements = [
            ("{{세목}}", "002"),
            ("{{부과연월}}", "2026.4"),
            ("{{과세번호}}", "007794"),
            ("{{납부일_일}}", "24"),
            ("{{환급금}}", "201,600"),
            ("{{납세자_명칭}}", "주식회사 테스트"),
        ]

        for find_str, replace_str in replacements:
            try:
                hwp.HAction.GetDefault("AllReplace", hwp.HParameterSet.HFindReplace.HSet)
                hwp.HParameterSet.HFindReplace.FindString = find_str
                hwp.HParameterSet.HFindReplace.ReplaceString = replace_str
                hwp.HParameterSet.HFindReplace.IgnoreMessage = 1
                hwp.HParameterSet.HFindReplace.SeveralWords = 1
                hwp.HParameterSet.HFindReplace.AllWordForms = 0
                hwp.HParameterSet.HFindReplace.MatchCase = 0
                hwp.HParameterSet.HFindReplace.UseRegExp = 0
                hwp.HParameterSet.HFindReplace.UseWildCards = 0
                hwp.HParameterSet.HFindReplace.WholeWordOnly = 0
                hwp.HParameterSet.HFindReplace.AutoSpell = 1
                hwp.HParameterSet.HFindReplace.Direction = 0  # 양방향
                ret = hwp.HAction.Execute("AllReplace", hwp.HParameterSet.HFindReplace.HSet)

                result["replacements"][find_str] = bool(ret)
                print(f"  {find_str} -> {replace_str}: {'✓ 성공' if ret else '✗ 실패'}")
            except Exception as e:
                result["replacements"][find_str] = False
                print(f"  {find_str}: ✗ 예외 - {e}")

        abs_path = str(hwp_path.resolve())
        try:
            hwp.SaveAs(abs_path, "HWP", "")
        except Exception:
            try:
                hwp.SaveAs(abs_path, "HWP")
            except Exception:
                hwp.SaveAs(abs_path)

    except Exception as e:
        print(f"  [에러] 처리 실패: {e}")
        result["error"] = str(e)
    finally:
        try:
            hwp.Quit()
        except Exception:
            pass

    return result


def print_summary(results: list[dict]):
    """전체 결과 요약."""
    print("\n" + "=" * 60)
    print("최종 결과 요약")
    print("=" * 60)

    for r in results:
        method = r["method"]
        if "error" in r:
            print(f"\n[{method}] ✗ 처리 자체 실패: {r['error']}")
            continue

        total = len(r["replacements"])
        success = sum(1 for v in r["replacements"].values() if v)
        print(f"\n[{method}] {success}/{total} 성공")
        for find_str, ok in r["replacements"].items():
            mark = "✓" if ok else "✗"
            print(f"  {mark} {find_str}")

    print("\n" + "=" * 60)
    print("결과 파일 위치:")
    print(f"  {TEST_DIR}")
    print("\n각 method*.hwp 파일을 한/글로 직접 열어")
    print("실제로 치환자가 어떻게 바뀌었는지 눈으로 확인하세요.")
    print("=" * 60)


def main():
    if not TEMPLATE_PATH.exists():
        print(f"[에러] 템플릿 파일이 없습니다: {TEMPLATE_PATH}")
        sys.exit(1)

    print("HWP 치환 검증 테스트 시작")
    print(f"원본: {TEMPLATE_PATH}")
    print(f"테스트 폴더: {TEST_DIR}")

    # 테스트 파일 준비
    test_files = setup_test_files()

    # 4가지 방법 순차 실행
    results = []
    results.append(test_method_1_default(test_files["method1_default"]))
    time.sleep(2)  # 한/글 인스턴스 정리 시간

    results.append(test_method_2_several_words(test_files["method2_several_words"]))
    time.sleep(2)

    results.append(test_method_3_regex(test_files["method3_regex"]))
    time.sleep(2)

    results.append(test_method_4_extended_options(test_files["method4_extended_options"]))

    # 요약
    print_summary(results)


if __name__ == "__main__":
    main()

