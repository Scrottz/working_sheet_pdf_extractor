# python
from __future__ import annotations
import re
from typing import Optional, List, Dict, Tuple, Any
from lib.logging import get_logger
from lib.pdf_document_object_model import PdfDocument
from lib.pdfIO import read_pdf

logger = get_logger(__name__)


def clean_header_text(s: Optional[str]) -> str:
    """
    Entfernt Steuerzeichen (z.B. \\x08), ersetzt sie durch Leerzeichen
    und reduziert mehrfaches Whitespace auf ein einzelnes Leerzeichen.
    """
    if not s:
        return ""
    # remove control chars (including \x08)
    s = re.sub(r"[\x00-\x1f\x7f]+", " ", s)
    # replace non breaking spaces
    s = s.replace("\xa0", " ")
    # collapse whitespace
    return re.sub(r"\s+", " ", s).strip()


def parse_ab_header(header_text: Optional[str], current_pdf_page: int = 0) -> Tuple[Optional[int], str, Optional[int], Optional[int]]:
    """
    Versucht in header_text folgende Informationen zu extrahieren:
      - AB id (int) oder None
      - name (string, eventuell leer)
      - curr (aktuelle Blattseite, z.B. 1 aus "1/2") oder None
      - total (Gesamtseitenzahl, z.B. 2 aus "1/2") oder None

    Wenn keine curr/total gefunden werden, bleiben curr und total None.
    """
    txt = clean_header_text(header_text or "")
    if not txt:
        return None, "", None, None

    # AB id (z.B. "AB 22")
    m_id = re.search(r"\bAB\s*(\d{1,4})\b", txt, flags=re.IGNORECASE)
    id_int = int(m_id.group(1)) if m_id else None

    # curr/total pattern anywhere in header (e.g. "1/2")
    m_frac = re.search(r"\b(\d{1,4})\s*/\s*(\d{1,4})\b", txt)
    curr = int(m_frac.group(1)) if m_frac else None
    total = int(m_frac.group(2)) if m_frac else None

    # name: remove AB <id> and trailing page counts
    name = re.sub(r"\bAB\s*\d{1,4}\b", "", txt, flags=re.IGNORECASE).strip()
    name = re.sub(r"\b\d{1,4}\s*/\s*\d{1,4}\b$", "", name).strip()
    # also strip any trailing pure page number
    name = re.sub(r"\b\d{1,4}$", "", name).strip()

    # if no page info, we keep None; caller may use current_pdf_page as fallback
    return id_int, name, curr, total


class F42_Beltz_TT_Zwangsstörungen_Fricke:
    """
    Workbook handler for F42.

    The constructor accepts a PdfDocument (provided by the working_sheet_extractor),
    stores it and reads PDF pages via read_pdf.
    """

    def __init__(self, pdf_object: PdfDocument) -> None:
        self.pdf_object = pdf_object
        self.pages: Optional[List[str]] = None
        try:
            self.pages = read_pdf(pdf_path=pdf_object.pdf_path or "")
            logger.info("Loaded %d pages for %s", len(self.pages or []), pdf_object.pdf_filename)
        except Exception:
            logger.debug("Could not read PDF pages during init (non-fatal).", exc_info=True)
            self.pages = []

    def page_text(self, p: Any) -> str:
        """
        Normalize page input to a text string.
        """
        if isinstance(p, str):
            return p
        if isinstance(p, dict):
            return p.get("text", "") or p.get("page_text", "") or ""
        return str(p or "")

    def header_ab_on_page(self, text: str) -> Optional[int]:
        """
        Detect 'AB <n>' in the page header area and return the integer id or None.
        Uses cleaning to remove control chars and searches header area first,
        then falls back to whole page.
        """
        if not text:
            return None
        head = "\n".join(self.page_text(text).splitlines()[:12])[:400]
        head_clean = clean_header_text(head)
        m = re.search(r"\bAB\s*(\d{1,4})\b", head_clean, flags=re.IGNORECASE)
        if m:
            try:
                return int(m.group(1))
            except Exception:
                return None
        # fallback: search whole cleaned page text
        whole_clean = clean_header_text(self.page_text(text))
        m2 = re.search(r"\bAB\s*(\d{1,4})\b", whole_clean, flags=re.IGNORECASE)
        if m2:
            try:
                return int(m2.group(1))
            except Exception:
                return None
        return None

    def determine_last_page(self, start_page: int, current_id: Optional[int] = None, max_scan: Optional[int] = None) -> int:
        """
        Scan forward from start_page and determine the last page of the worksheet.
        Uses header AB boundaries and 'curr/total' patterns as heuristics.
        """
        if not self.pages:
            return start_page
        total_pages_doc = len(self.pages)
        max_scan = max_scan if max_scan is not None else (total_pages_doc - start_page + 1)
        for offset in range(0, max_scan):
            page_no = start_page + offset
            if page_no < 1 or page_no > total_pages_doc:
                break
            raw_pt = self.page_text(self.pages[page_no - 1]) or ""
            pt = clean_header_text(raw_pt)
            # header AB check: if a different AB appears in header, stop before that page
            hdr = self.header_ab_on_page(raw_pt)
            if hdr is not None and current_id is not None and hdr != current_id:
                last = max(start_page, page_no - 1)
                return min(last, total_pages_doc)
            # look for curr/total pattern on the page
            m = re.search(r"\b(\d{1,4})\s*/\s*(\d{1,4})\b", pt)
            if m:
                try:
                    curr = int(m.group(1))
                    second = int(m.group(2))
                except Exception:
                    continue
                # Case A: second number plausibly absolute page number (e.g. "40/43" -> 43)
                if second >= curr and second <= total_pages_doc and second - start_page < 500:
                    return min(second, total_pages_doc)
                # Case B: second number likely page count -> compute last page
                if second > 0 and second <= 400:
                    last = start_page + (second - curr)
                    return min(max(start_page, last), total_pages_doc)
        # fallback: only the start page
        return min(start_page, total_pages_doc)

    def existing_pages_for_id(self, id_int: int) -> set:
        """
        Return a set of pages already stored for the given id in the PdfDocument.
        """
        s = set()
        for names in (self.pdf_object.working_sheets.get(id_int) or {}).values():
            s.update(names or [])
        return s

    def _find_page_for_entry(self, id_int: Optional[int], name: Optional[str]) -> Optional[int]:
        """
        Attempt to locate a page for an entry that lacks an explicit page number.
        Strategy:
        1) If id_int provided, scan pages for header 'AB <id>'
        2) If not found and name provided, search pages for the name (case-insensitive)
        3) If exact name not found, search for long tokens from the name
        Returns 1-based page number or None.
        """
        if not self.pages:
            return None
        total = len(self.pages)
        # 1) search by AB header
        if id_int:
            for i in range(total):
                try:
                    hdr_id, hdr_name, curr, total_cnt = parse_ab_header(self.page_text(self.pages[i]), i + 1)
                    if hdr_id == id_int:
                        # prefer page where header matches; if curr provided, prefer that page, otherwise return this page
                        return i + 1
                except Exception:
                    continue
        # 2) search by full name substring (case-insensitive)
        if name:
            name_norm = re.sub(r"\s+", " ", name.strip()).lower()
            if name_norm:
                for i in range(total):
                    try:
                        txt = clean_header_text(self.page_text(self.pages[i]) or "").lower()
                        if name_norm in txt:
                            return i + 1
                    except Exception:
                        continue
                # 3) fallback: search by significant tokens from the name
                tokens = re.findall(r"\w{4,}", name_norm)
                for tok in tokens:
                    for i in range(total):
                        try:
                            txt = clean_header_text(self.page_text(self.pages[i]) or "").lower()
                            if tok in txt:
                                return i + 1
                        except Exception:
                            continue
        return None

    def identify_working_sheets(self) -> PdfDocument:
        """
        Combined strategy to identify working sheets:
        - Robust TOC parsing (handles page numbers attached to names or in next tokens)
        - Global scan for explicit 'AB id / Name page' patterns
        - Header-based pass that groups contiguous pages with the same 'AB n' header
          and merges them into the document model.
        """
        if not getattr(self, "pages", None):
            logger.info("No pages available to identify working sheets for %s", self.pdf_object.pdf_filename)
            return self.pdf_object

        pages = self.pages

        # --- TOC detection ---
        start_idx = None
        end_idx = None
        heading_start_re = re.compile(r"(^|\n)\s*Übersicht Arbeitsblätter\s*(\n|$)", flags=re.IGNORECASE)
        heading_end_re = re.compile(r"(^|\n)\s*Übersicht Informationsblätter\s*(\n|$)", flags=re.IGNORECASE)

        for i, txt in enumerate(pages):
            if txt and heading_start_re.search(self.page_text(txt)):
                start_idx = i
                break
        if start_idx is None:
            # try a last-resort search (some PDFs split headings)
            for i in range(len(pages) - 1, -1, -1):
                if pages[i] and "Übersicht Arbeitsblätter" in self.page_text(pages[i]):
                    start_idx = i
                    break
        if start_idx is not None:
            for j in range(start_idx, len(pages)):
                pt = self.page_text(pages[j]) or ""
                if heading_end_re.search(pt):
                    end_idx = j
                    break
            if end_idx is None:
                for j in range(start_idx, len(pages)):
                    if pages[j] and "Übersicht Informationsblätter" in self.page_text(pages[j]):
                        end_idx = j
                        break
            if end_idx is None:
                end_idx = min(start_idx + 8, len(pages) - 1)

        toc_text = ""
        if start_idx is not None and end_idx is not None:
            raw_toc = " ".join(self.page_text(p) for p in pages[start_idx:end_idx + 1])
            toc_text = raw_toc.replace("\xa0", " ")
            toc_text = re.sub(r"\s+", " ", toc_text).strip()

        logger.debug("TOC text snippet: %s", (toc_text or "")[:400])

        # --- Robust TOC parsing ---
        entries_found: List[Tuple[str, str, Optional[int]]] = []
        if toc_text:
            # accept 'AB <n>' optionally followed by '/' or '-' or nothing
            ab_token_re = re.compile(r"\bAB\s*(\d{1,4})\b(?:\s*[/\-]\s*)?", flags=re.IGNORECASE)
            matches = list(ab_token_re.finditer(toc_text))
            for idx, m in enumerate(matches):
                id_str = m.group(1)
                start = m.end()
                end = matches[idx + 1].start() if idx + 1 < len(matches) else len(toc_text)
                raw_name = toc_text[start:end].strip()
                page_num: Optional[int] = None
                # 1) if name ends with attached page number, separate it
                m_trail = re.search(r"(?P<n>.*?)[\s\-–—:]*(?P<p>\d{1,4})\s*$", raw_name)
                if m_trail:
                    name_candidate = (m_trail.group("n") or "").strip()
                    p_candidate = (m_trail.group("p") or "").strip()
                    if p_candidate.isdigit():
                        try:
                            page_num = int(p_candidate)
                        except Exception:
                            page_num = None
                    if name_candidate:
                        raw_name = name_candidate
                # 2) if still no page, look further ahead in the TOC text for a number
                if page_num is None:
                    lookahead = toc_text[start:start + 250]
                    m2 = re.search(r"\b(\d{1,4})\b", lookahead)
                    if m2:
                        try:
                            page_num = int(m2.group(1))
                        except Exception:
                            page_num = None
                name = raw_name.strip(" \t\-–—:;,.")
                entries_found.append((id_str, name, page_num))

        logger.debug("entries_found count=%d sample=%s", len(entries_found), entries_found[:20])

        # If TOC entries lacked page numbers, try to find pages by header or name
        if entries_found:
            fixed_entries: List[Tuple[str, str, Optional[int]]] = []
            for id_str, name, page_num in entries_found:
                if page_num is None:
                    try:
                        id_int = PdfDocument._coerce_id_to_int(id_str)
                    except Exception:
                        id_int = None
                    found = self._find_page_for_entry(id_int if id_int else None, name or None)
                    if found:
                        fixed_entries.append((id_str, name, found))
                    else:
                        # keep entry with None page so add_working_sheet still stores the name
                        fixed_entries.append((id_str, name, None))
                else:
                    fixed_entries.append((id_str, name, page_num))
            entries_found = fixed_entries

        # regex for global scan (more tolerant: optional slash, permit comma separators)
        global_re = re.compile(r"\bAB\s*(\d{1,4})\b(?:\s*[/\-]\s*)?(.+?)\s+(\d{1,4})\b", flags=re.IGNORECASE)

        # add entries parsed from TOC (store id as string to keep serialization consistent)
        for id_str, name, start_page in entries_found:
            try:
                current_id = PdfDocument._coerce_id_to_int(id_str)
            except Exception:
                current_id = None
            if start_page:
                last_page = self.determine_last_page(start_page, current_id=current_id)
                pages_list = list(range(start_page, last_page + 1)) if start_page <= last_page else []
            else:
                pages_list = []
            try:
                self.pdf_object.add_working_sheet(id_=str(current_id or id_str), name=name or f"AB {id_str}", pages=pages_list)
                logger.info("Identified sheet %s/%s -> pages %s", current_id or id_str, name, pages_list)
            except Exception:
                logger.debug("Failed to add working sheet %s/%s", id_str, name, exc_info=True)

        # --- Global scan fallback ---
        existing_ids = set(self.pdf_object.working_sheets.keys())

        for p_idx, p in enumerate(pages):
            txt = self.page_text(p)
            if not txt:
                continue
            for m in global_re.finditer(txt):
                id_str = m.group(1)
                try:
                    id_int = PdfDocument._coerce_id_to_int(id_str)
                except Exception:
                    id_int = 0
                if id_int in existing_ids:
                    continue
                raw_name = (m.group(2) or "").strip()
                try:
                    start_page = int(m.group(3))
                except Exception:
                    start_page = None
                name = raw_name.strip(" \t\-–—:;,")
                if start_page:
                    last_page = self.determine_last_page(start_page, current_id=id_int)
                    pages_list = list(range(start_page, last_page + 1)) if start_page <= last_page else []
                else:
                    # try to find page for this id/name
                    found = self._find_page_for_entry(id_int if id_int else None, name or None)
                    if found:
                        pages_list = [found]
                    else:
                        pages_list = []
                try:
                    self.pdf_object.add_working_sheet(id_=str(id_int), name=name, pages=pages_list)
                    existing_ids.add(PdfDocument._coerce_id_to_int(id_str))
                    logger.info("Global-scan added sheet %s/%s -> %s", id_str, name, pages_list)
                except Exception:
                    logger.debug("Failed to add working sheet from global scan %s/%s", id_str, name, exc_info=True)

        # --- Header-based pass to fill gaps ---
        total_pages = len(pages)
        header_map: List[int] = []
        for i in range(total_pages):
            raw = self.page_text(pages[i]) if pages[i] else ""
            hdr = self.header_ab_on_page(raw)
            header_map.append(hdr or 0)

        logger.debug("header_map sample: %s", header_map[:120])

        # if header_map is sparse, perform relaxed whole-page scan to pick up AB tokens
        if sum(1 for v in header_map if v) < max(2, total_pages // 30):
            logger.debug("header_map sparse -> performing relaxed whole-page scan")
            for i in range(total_pages):
                if header_map[i] == 0:
                    txt = self.page_text(pages[i]) if pages[i] else ""
                    id_int, name, curr, total_cnt = parse_ab_header(txt, i + 1)
                    if id_int:
                        header_map[i] = id_int
            logger.debug("header_map after relaxed scan sample: %s", header_map[:120])

        # build contiguous blocks with same AB id, using curr/total on block-start as heuristic
        blocks: List[Tuple[int, int, int]] = []  # (id, start_page, end_page) end_page inclusive (1-based)
        i = 0
        while i < total_pages:
            cur = header_map[i]
            if cur and cur > 0:
                start = i + 1  # 1-based start
                # check header on the start page for curr/total
                txt_start = self.page_text(pages[start - 1]) if pages[start - 1] else ""
                try:
                    _, _, curr, total_cnt = parse_ab_header(txt_start, start)
                except Exception:
                    curr, total_cnt = None, None

                if curr and total_cnt:
                    # calculate end page from curr/total
                    end_page = min(total_pages, start + (total_cnt - curr))
                    if end_page < start:
                        end_page = start
                    blocks.append((cur, start, end_page))
                    # move i to index after end_page (convert end_page 1-based -> 0-based index)
                    i = end_page
                else:
                    # fallback: contiguous detection
                    j = i + 1
                    while j < total_pages and header_map[j] == cur:
                        j += 1
                    end_page = j  # j is first index not equal -> equals inclusive 1-based end
                    blocks.append((cur, start, end_page))
                    i = j
            else:
                i += 1

        logger.debug("blocks detected: %s", blocks[:60])

        # map TOC names by int id
        toc_name_by_id: Dict[int, str] = {}
        for id_str, name, _ in entries_found:
            try:
                toc_name_by_id[PdfDocument._coerce_id_to_int(id_str)] = name
            except Exception:
                continue

        for id_int, start_page, end_page in blocks:
            if id_int <= 0:
                continue
            if end_page < start_page:
                continue
            block_pages = list(range(start_page, end_page + 1))
            already = self.existing_pages_for_id(id_int)
            # skip if all pages already present
            if set(block_pages).issubset(already) and already:
                continue
            # resolve name: prefer TOC, then existing model name, then heuristic from page
            name = toc_name_by_id.get(id_int)
            if not name:
                names_map = self.pdf_object.working_sheets.get(id_int) or {}
                if names_map:
                    name = next(iter(names_map.keys()))
            if not name:
                srch_re = re.compile(rf"\bAB\s*{id_int}\s*[/\-]\s*(.+?)(?:\n|$)", flags=re.IGNORECASE)
                found_name = None
                # scan a small page window around the block for a name
                for pg in range(max(1, start_page - 1), min(total_pages, end_page + 2)):
                    txt = self.page_text(pages[pg - 1]) if pages[pg - 1] else ""
                    cleaned = clean_header_text(txt)
                    m = srch_re.search(cleaned)
                    if m:
                        found_name = (m.group(1) or "").strip()
                        break
                if found_name:
                    name = found_name.strip(" \t\-–—:;,.")
            if not name:
                name = f"AB {id_int}"
            try:
                # store with string id to keep serialization consistent
                self.pdf_object.add_working_sheet(id_=str(id_int), name=name, pages=block_pages)
                logger.info("Header-pass added/merged AB %s -> pages %s", id_int, block_pages)
            except Exception:
                logger.debug("Header-pass failed for AB %s", id_int, exc_info=True)

        logger.info("identify_working_sheets: finished, %d id-buckets for %s",
                    len(self.pdf_object.working_sheets), self.pdf_object.pdf_filename)
        return self.pdf_object
