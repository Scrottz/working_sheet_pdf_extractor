from pathlib import Path
from lib.logging import setup_logger, get_logger
from lib import pdfIO
from lib.workbooks import BOOK_STRATEGIES

setup_logger()
logger = get_logger(__name__)

SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "data"
INPUT_DIR = DATA_DIR / "input"
OUTPUT_DIR = DATA_DIR / "output"


def main() -> None:

    for filepath in INPUT_DIR.glob("*.pdf"):
        output_path = OUTPUT_DIR / filepath.stem
        prefix = filepath.stem.split("_")[0].replace(".", "_")

        if prefix not in BOOK_STRATEGIES:
            continue

        strategy = BOOK_STRATEGIES[prefix]

        logger.info(f"Processing {filepath.stem}")

        pdf = pdfIO.PDFIO(pdf_filepath=filepath)
        pdf.pdf_read()

        working_sheet_numbers_names = strategy["name_func"](doc=pdf.doc, overview_pages=strategy["toc_pages"])
        working_sheets_pages = strategy["page_func"](doc=pdf.doc)

        for ab_num, pages in working_sheets_pages.items():
            working_pdf = pdf.pdf_extract_pages(page_numbers=pages, ignore_toc=strategy["toc_pages"])
            output_path.mkdir(exist_ok=True)
            sheet_name = working_sheet_numbers_names[ab_num].strip("?")
            output_filepath = output_path / f"{ab_num}_{sheet_name}.pdf"
            working_pdf.pdf_write(output_path=output_filepath)
        logger.info(f"{len(working_sheets_pages.items())} Files saved to {output_path.resolve()}")


if __name__ == "__main__":
    main()
