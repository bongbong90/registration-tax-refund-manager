from __future__ import annotations

from pathlib import Path

import fitz


def convert_pdf_to_images(
    pdf_path: Path | str,
    output_dir: Path | str,
    dpi: int = 300,
) -> list[Path]:
    pdf_path = Path(pdf_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF 파일이 없습니다: {pdf_path}")

    image_paths: list[Path] = []
    with fitz.open(pdf_path) as document:
        if document.page_count == 0:
            raise ValueError(f"페이지가 없는 PDF입니다: {pdf_path}")

        page = document.load_page(0)
        zoom = dpi / 72.0
        matrix = fitz.Matrix(zoom, zoom)
        pixmap = page.get_pixmap(matrix=matrix, alpha=False)

        output_path = output_dir / f"{pdf_path.stem}_page1.png"
        pixmap.save(output_path)
        image_paths.append(output_path)

    return image_paths

