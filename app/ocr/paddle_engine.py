from __future__ import annotations

import os
from pathlib import Path
from typing import Any

os.environ["FLAGS_use_mkldnn"] = "0"
os.environ["FLAGS_enable_pir_in_executor"] = "0"
os.environ["FLAGS_use_mkldnn"] = "false"

from paddleocr import PaddleOCR

_OCR_ENGINE: PaddleOCR | None = None


def _get_ocr_engine() -> PaddleOCR:
    global _OCR_ENGINE
    if _OCR_ENGINE is None:
        _OCR_ENGINE = PaddleOCR(
            lang="korean",
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
            enable_mkldnn=False,
            cpu_threads=4,
        )
    return _OCR_ENGINE


def _bbox_center(bbox: list[list[float]]) -> tuple[float, float]:
    xs = [point[0] for point in bbox]
    ys = [point[1] for point in bbox]
    return (sum(xs) / len(xs), sum(ys) / len(ys))


def _normalize_bbox(raw_bbox: Any) -> list[list[float]] | None:
    if not isinstance(raw_bbox, (list, tuple)) or len(raw_bbox) != 4:
        return None

    normalized: list[list[float]] = []
    for point in raw_bbox:
        if not isinstance(point, (list, tuple)) or len(point) < 2:
            return None
        normalized.append([float(point[0]), float(point[1])])
    return normalized


def _normalize_predict_output(raw_output: Any) -> list[dict[str, Any]]:
    if not isinstance(raw_output, list):
        raise TypeError(f"PaddleOCR predict() 반환 형식이 예상과 다릅니다: {type(raw_output)!r}")

    results: list[dict[str, Any]] = []
    for page_result in raw_output:
        if not isinstance(page_result, dict):
            raise TypeError(f"PaddleOCR 페이지 결과 형식이 예상과 다릅니다: {type(page_result)!r}")

        texts = page_result.get("rec_texts") or []
        scores = page_result.get("rec_scores") or []
        polys = page_result.get("dt_polys") or []

        for text, score, poly in zip(texts, scores, polys):
            bbox = _normalize_bbox(poly)
            if bbox is None:
                continue
            results.append(
                {
                    "text": str(text) if text is not None else "",
                    "bbox": bbox,
                    "confidence": float(score),
                }
            )

    results.sort(key=lambda item: (_bbox_center(item["bbox"])[1], _bbox_center(item["bbox"])[0]))
    return results


def run_ocr(image_path: Path) -> list[dict]:
    ocr_engine = _get_ocr_engine()
    raw_output = ocr_engine.predict(str(image_path))

    results = []
    for page_result in raw_output:
        # OCRResult 객체에서 .json 속성으로 dict 추출
        page_data = page_result.json.get('res', {})

        texts = page_data.get('rec_texts', [])
        scores = page_data.get('rec_scores', [])
        polys = page_data.get('rec_polys', [])

        # 안전을 위해 길이 맞추기
        min_len = min(len(texts), len(scores), len(polys))

        for i in range(min_len):
            text = texts[i]
            score = scores[i]
            poly = polys[i]

            # poly는 numpy array일 수 있으므로 list로 변환
            if hasattr(poly, 'tolist'):
                poly_list = poly.tolist()
            else:
                poly_list = poly

            bbox = [[float(p[0]), float(p[1])] for p in poly_list]

            results.append({
                "text": str(text),
                "bbox": bbox,
                "confidence": float(score)
            })

    return results
