# python
from __future__ import annotations
from pathlib import Path
from lib.logging import setup_logger, get_logger
from lib.pdfIO import write_working_sheets_outputs
from lib.workbooks.F42_Beltz_TT_Zwangsstörungen_Fricke import F42_Beltz_TT_Zwangsstörungen_Fricke
from lib.pdf_document_object_model import PdfDocument
from pprint import pprint

setup_logger()
logger = get_logger(__name__)

PDF_PATHS = {
    "F42_Beltz_TT_Zwangsstörungen_Fricke": Path("/home/keilholz/code/working_sheet_pdf_extractor/data/input/F42_Beltz_TT_Zwangsstörungen_Fricke.pdf")
}

def main() -> None:
    """Main entry: detect working sheets and write per-sheet PDF outputs."""

    logger.info("Starting processing")

    pdf_obj = PdfDocument(pdf_filename="F42_Beltz_TT_Zwangsstörungen_Fricke", pdf_path=PDF_PATHS['F42_Beltz_TT_Zwangsstörungen_Fricke'])
    handler = F42_Beltz_TT_Zwangsstörungen_Fricke(pdf_object=pdf_obj)

    pdf_obj = handler.identify_working_sheets()

    pprint(pdf_obj.working_sheets)
    print("\n\n\n\”-------------------------\n\n\n")
    pprint(pdf_obj.to_dict())


if __name__ == "__main__":
    main()
