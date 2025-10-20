from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Iterable, Any
import re
from pathlib import Path
from lib.logging import get_logger

logger = get_logger(__name__)

@dataclass
class PdfDocument:
    """
    pdf_filename: base filename
    pdf_path: full path
    working_sheets (exposed): mapping from int id -> {working_sheet_name: [1-based pages]}
    Internally stored as _working_sheets.
    """
    pdf_filename: str
    pdf_path: str | Path
    _working_sheets: Dict[int, Dict[str, List[int]]] = field(default_factory=dict, init=False, repr=False)

    @property
    def working_sheets(self) -> Dict[int, Dict[str, List[int]]]:
        return self._working_sheets

    @working_sheets.setter
    def working_sheets(self, value: Any) -> None:
        """
        Enforce new shape: top-level keys must be ints (or numeric strings) and values must be dict[name: list[int]].
        Legacy top-level name->pages shapes are rejected to force callers to use add_working_sheet.
        """
        if not isinstance(value, dict):
            raise ValueError("working_sheets must be a dict[int, dict[str, list[int]]]")
        normalized: Dict[int, Dict[str, List[int]]] = {}
        for raw_k, names in value.items():
            # top-level key must be int or numeric string
            if not (isinstance(raw_k, int) or (isinstance(raw_k, str) and raw_k.isdigit())):
                raise ValueError("working_sheets top-level keys must be int (or numeric strings). Legacy shape not allowed.")
            if not isinstance(names, dict):
                raise ValueError("working_sheets values must be dict[name: pages]. Legacy shape not allowed.")
            id_key = int(raw_k) if isinstance(raw_k, str) and raw_k.isdigit() else int(raw_k)
            normalized[id_key] = {}
            for name, pages in names.items():
                normalized[id_key][str(name)] = PdfDocument._normalize_pages(pages or [])
        self._working_sheets = normalized

    @staticmethod
    def _normalize_pages(pages: Iterable[Any]) -> List[int]:
        normalized: List[int] = []
        for p in pages or []:
            try:
                pi = int(p)
            except Exception:
                continue
            if pi > 0:
                normalized.append(pi)
        # preserve order, remove duplicates
        return sorted(dict.fromkeys(normalized))

    @staticmethod
    def _coerce_id_to_int(id_value: Any) -> int:
        if id_value is None:
            return 0
        if isinstance(id_value, int):
            return id_value
        s = str(id_value).strip()
        if not s:
            return 0
        try:
            return int(s)
        except Exception:
            m = re.match(r'^\s*(\d+)', s)
            if m:
                try:
                    return int(m.group(1))
                except Exception:
                    return 0
        return 0

    def add_working_sheet(self, id_: Any, name: str, pages: Iterable[Any]) -> None:
        """
        Store pages under working_sheets[int(id_)][name], merging if entry exists.
        If id_ cannot be converted to int, it is stored under id 0.
        Now: allows storing empty page lists so index names are preserved even if pages couldn't be resolved yet.
        """
        if not name:
            logger.debug("add_working_sheet: empty name, skipping (id=%s)", id_)
            return

        id_key = self._coerce_id_to_int(id_)
        new_pages = self._normalize_pages(pages)

        bucket = self._working_sheets.setdefault(id_key, {})
        if name in bucket:
            existing = bucket[name] or []
            merged = sorted(dict.fromkeys(existing + new_pages))
            bucket[name] = merged
            logger.info("Merged pages into working sheet %s/%s: %s", id_key, name, merged)
        else:
            # store even if new_pages == [] to preserve the identified name in the model
            bucket[name] = new_pages
            logger.info("Added working sheet %s/%s: %s", id_key, name, new_pages)

    def get_pages(self, id_: Any, name: str) -> List[int]:
        id_key = self._coerce_id_to_int(id_)
        return list(self._working_sheets.get(id_key, {}).get(name, []))

    def to_dict(self) -> Dict[str, Any]:
        serialized_ws: Dict[str, Dict[str, List[int]]] = {}
        for id_key, names in (self._working_sheets or {}).items():
            serialized_ws[str(id_key)] = {n: list(p) for n, p in names.items()}
        data = {
            "pdf_filename": self.pdf_filename,
            "pdf_path": self.pdf_path,
            "working_sheets": serialized_ws
        }
        logger.debug("to_dict: serialized %s with %d id buckets", self.pdf_filename, len(self._working_sheets))
        return data

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "PdfDocument":
        """
        Create PdfDocument from dict. Only accepts the new shape (id -> {name: [pages]}).
        Legacy name->pages entries are ignored and a warning is logged.
        """
        pdf_filename = str(data.get("pdf_filename", ""))
        pdf_path = str(data.get("pdf_path", ""))
        doc = PdfDocument(pdf_filename=pdf_filename, pdf_path=pdf_path)

        ws = data.get("working_sheets") or {}
        if not isinstance(ws, dict):
            logger.warning("from_dict: expected working_sheets dict, got %s; ignoring", type(ws).__name__)
            return doc

        for raw_id_key, val in ws.items():
            if not isinstance(val, dict):
                logger.warning("from_dict: skipping legacy or invalid entry for %s (expected dict, got %s)", raw_id_key, type(val).__name__)
                continue
            id_key = PdfDocument._coerce_id_to_int(raw_id_key)
            for name, pages in val.items():
                norm_pages = PdfDocument._normalize_pages(pages or [])
                # store even empty norm_pages if explicit empty list present? keep previous behaviour (only store when pages present)
                if norm_pages:
                    doc._working_sheets.setdefault(id_key, {})[str(name)] = norm_pages

        logger.info("from_dict: created PdfDocument %s with %d id buckets", pdf_filename, len(doc._working_sheets))
        return doc
