# python
from __future__ import annotations
from pathlib import Path
from typing import List, Union, Optional, Any
from PyPDF2 import PdfReader, PdfWriter
from lib.logging import get_logger
from lib.pdf_document_object_model import PdfDocument

logger = get_logger(__name__)


def _sanitize_filename(s: str) -> str:
    keep = ("abcdefghijklmnopqrstuvwxyz"
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            "0123456789-_().")
    return "".join(ch if ch in keep else "_" for ch in s).strip("_")[:200] or "unnamed"


def read_pdf(pdf_path: Union[str, Path], max_pages: Optional[int] = None) -> List[str]:
    path = Path(str(pdf_path))
    if not path.exists():
        logger.error("read_pdf: file not found: %s", path)
        return []

    try:
        reader = PdfReader(str(path))
    except Exception:
        logger.exception("read_pdf: failed to open PDF %s", path)
        return []

    pages_text: List[str] = []
    total = len(getattr(reader, "pages", []))
    logger.info("read_pdf: finished reading %s (%d pages)", path.name, total)

    to_read = total if max_pages is None else min(total, max(0, int(max_pages)))
    for i in range(to_read):
        try:
            page = reader.pages[i]
            text = page.extract_text() or ""
            pages_text.append(text)
        except Exception:
            logger.exception("read_pdf: failed to extract text from page %d of %s", i + 1, path)
            pages_text.append("")

    return pages_text


def write_working_sheets_outputs(pdf_doc: PdfDocument, output_base: Union[str, Path] = ".data/output") -> List[Path]:
    """
    Für jede working-sheet-Definition in pdf_doc.working_sheets:
      - Seiten mit PdfDocument._normalize_pages vereinigen und sortieren
      - Ungültige Seiten (außerhalb der PDF) entfernen
      - Zusammenhängendes PDF mit den sortierten Seiten schreiben
    Output-Filename: `id_name.pdf` (sanitized)
    Returns list of written file paths.
    """
    out_paths: List[Path] = []
    out_base = Path(output_base)
    pdf_name_stem = Path(pdf_doc.pdf_filename).stem if pdf_doc.pdf_filename else Path(pdf_doc.pdf_path).stem
    target_dir = out_base / pdf_name_stem
    target_dir.mkdir(parents=True, exist_ok=True)
    logger.info("write_working_sheets_outputs: writing outputs to %s (resolved: %s)", target_dir, target_dir.resolve())

    # Quelle auflösen / Fallback
    src = Path(str(pdf_doc.pdf_path))
    if not src.exists():
        alt = Path("data/input") / f"{pdf_name_stem}.pdf"
        if alt.exists():
            src = alt
            logger.debug("write_working_sheets_outputs: using fallback source %s", src)
        else:
            logger.error("write_working_sheets_outputs: source PDF not found: %s (also tried %s)", pdf_doc.pdf_path, alt)
            return out_paths

    try:
        reader = PdfReader(str(src))
        total_pages = len(getattr(reader, "pages", []))
    except Exception:
        logger.exception("write_working_sheets_outputs: failed to open source PDF %s", src)
        return out_paths

    # iteriere über alle id buckets und innerhalb jedes buckets über alle Namen
    for id_key, names in (pdf_doc.working_sheets or {}).items():
        for name, pages_raw in (names or {}).items():
            # Normalisieren / entduplizieren / sortieren
            try:
                pages_list = PdfDocument._normalize_pages(pages_raw or [])
            except Exception:
                logger.exception("write_working_sheets_outputs: failed to normalize pages for %s/%s", id_key or "-", name)
                pages_list = []

            if not pages_list:
                logger.debug("skip %s/%s: no pages after normalization", id_key or "-", name)
                continue

            # nur gültige Seiten innerhalb der Quelle behalten
            valid_pages = [p for p in pages_list if 1 <= p <= total_pages]
            if not valid_pages:
                logger.warning("no valid pages for %s/%s (requested: %s)", id_key or "-", name, pages_list)
                continue

            writer = PdfWriter()
            for p in valid_pages:
                try:
                    writer.add_page(reader.pages[p - 1])
                except Exception:
                    logger.exception("failed to add page %d for %s/%s", p, id_key or "-", name)

            # neuer Dateiname: id_name.pdf
            safe_id = _sanitize_filename(str(id_key or "no-id"))
            safe_name = _sanitize_filename(str(name or "unnamed"))
            out_fname = f"{safe_id}_{safe_name}.pdf"
            out_path = target_dir / out_fname

            try:
                with out_path.open("wb") as fh:
                    writer.write(fh)
                out_paths.append(out_path)
                logger.info("wrote working sheet %s/%s -> %s (pages: %s)", id_key or "-", name, out_path, valid_pages)
            except Exception:
                logger.exception("failed to write output file %s for %s/%s", out_path, id_key or "-", name)

    logger.info("write_working_sheets_outputs: total written %d files to %s", len(out_paths), target_dir.resolve())
    return out_paths