from pathlib import Path
import pymupdf
from lib.logging import get_logger

logger = get_logger(__name__)


class PDFIO():
    def __init__(self, pdf_filepath: Path|None):
        self.pdf_filepath = pdf_filepath
        self.doc = None

    def __enter__(self):
        self.pdf_read()
        return self  # Wichtig: Gibt die Instanz an die Variable nach 'as' zurück

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.doc:
            self.doc.close()

    def pdf_read(self):
        self.doc =pymupdf.open(self.pdf_filepath)
        logger.debug(f"PDF succesfully imported {self.pdf_filepath}")

    def pdf_extract_pages(self, page_numbers: list[int], ignore_toc: list[int]):
        working_sheet_pdf = PDFIO(pdf_filepath=None)
        working_sheet_pdf.doc = pymupdf.open()
        for page_num in page_numbers:
            if page_num not in ignore_toc:
                working_sheet_pdf.doc.insert_pdf(self.doc, from_page=page_num, to_page=page_num)
        logger.debug(f"Extraktion of {len(page_numbers)} pages successful")
        return working_sheet_pdf

    def pdf_write(self, output_path=str):
        self.doc.save(
            output_path,
            garbage=3,
            deflate=True
        )
        logger.debug(f"File successfully saved to {output_path}")

