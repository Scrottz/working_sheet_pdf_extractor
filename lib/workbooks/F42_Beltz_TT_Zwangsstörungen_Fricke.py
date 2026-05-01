import re
import pymupdf
from collections import defaultdict
from lib.logging import get_logger
logger = get_logger(__name__)


def F42_extract_working_sheet_numbers_names(doc: pymupdf.Document, overview_pages: list[int]) -> dict[int, str]:
    working_papaer_numbers_names = {}
    pattern = re.compile(r"AB\s+(\d+)\s*/\s*(.*)", re.IGNORECASE)

    for page_num in overview_pages:
        page = doc[page_num]
        text = page.get_text("text")

        for line in text.splitlines():
            match = pattern.search(line)
            if match:
                ab_num = int(match.group(1))
                ab_name = match.group(2).strip()
                ab_name = ab_name.replace("?", "")
                working_papaer_numbers_names[ab_num] = ab_name
                logger.debug(f"AB {ab_num} -> {ab_name}")

    return working_papaer_numbers_names

def F42_extract_working_sheet_pages(doc: pymupdf.Document) -> dict[int, list[int]]:
    working_sheets_pages = defaultdict(list)
    pattern = re.compile(r"AB\s+(\d+)", re.IGNORECASE | re.MULTILINE)
    for page_num in range(len(doc)):
        page = doc[page_num]
        header_rect = pymupdf.Rect(0, 0, page.rect.width, 80)
        header_text = page.get_text("text", clip=header_rect).strip()
        match = pattern.search(header_text)

        if match:
            ab_num = int(match.group(1))
            working_sheets_pages[ab_num].append(page_num)
    return working_sheets_pages
