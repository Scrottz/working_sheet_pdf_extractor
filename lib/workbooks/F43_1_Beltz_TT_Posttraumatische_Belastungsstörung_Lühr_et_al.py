import re
import pymupdf
from collections import defaultdict
from lib.logging import get_logger
logger = get_logger(__name__)


def F43_1_extract_working_sheet_numbers_names(doc: pymupdf.Document, overview_pages: list[int]) -> dict[int, str]:
    working_sheet_numbers_names = {}
    last_sheet_num = None
    pattern = re.compile(r"^AB\s+(\d+)$", re.IGNORECASE)

    for page_num in overview_pages:
        page = doc[page_num]
        text = page.get_text("text")

        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue

            match = pattern.match(line)
            if match:
                last_sheet_num = int(match.group(1))
                continue

            if last_sheet_num is not None:
                name = line.strip()
                working_sheet_numbers_names[last_sheet_num] = name
                logger.debug(f"Found: AB {last_sheet_num} -> {name}")
                last_sheet_num = None

    return working_sheet_numbers_names

def F43_1_extract_working_sheet_pages(doc: pymupdf.Document) -> dict[int, list[int]]:
    working_sheets_pages = defaultdict(list)
    pattern = re.compile(r"AB\s+(\d+)", re.IGNORECASE | re.MULTILINE)
    for page_num in range(len(doc)):
        page = doc[page_num]
        header_rect = pymupdf.Rect(0, 0, page.rect.width, 80)
        header_text = page.get_text("text", clip=header_rect).strip()
        match = pattern.search(header_text)

        if match:
            sheet_num = int(match.group(1))
            logger.debug(f"sheet: {sheet_num} -> page: {page_num}")
            working_sheets_pages[sheet_num].append(page_num)

    return working_sheets_pages
