from pathlib import Path
import re
from lib.logging import setup_logger, get_logger
from lib import pdfIO
from lib.workbooks import BOOK_STRATEGIES

setup_logger()
logger = get_logger(__name__)

SCRIPT_DIR = Path(__file__).parent
INPUT_DIR = SCRIPT_DIR / ".." / "data" / "input"
OUTPUT_DIR = SCRIPT_DIR / ".." / "data" / "output"

def sanitize_filename(name: str) -> str:
    clean = re.sub(r'[<>:"/\\|?*]', '', name)
    return clean.replace(" ", "_").strip("_")


def main() -> None:
    logger.info("Starting processing")

    for filepath in INPUT_DIR.glob("*.pdf"):
        prefix = filepath.stem.split("_")[0]

        if prefix not in BOOK_STRATEGIES:
            continue

        strategy = BOOK_STRATEGIES[prefix]

        logger.info(f"Processing {filepath.stem}")

        pdf = pdfIO.PDFIO(pdf_filepath=filepath)
        pdf.pdf_read()

        working_paper_numbers_names = strategy["name_func"](doc=pdf.doc, overview_pages=strategy["toc_pages"])
        working_papers_pages = strategy["page_func"](doc=pdf.doc)

        for ab_num, pages in working_papers_pages.items():
            working_pdf = pdf.pdf_extract_working_pages(page_numbers=pages)
            output_path = SCRIPT_DIR / ".." / "data" / "output" / filepath.stem
            output_path.mkdir(exist_ok=True)
            output_filepath = output_path / f"{ab_num}_{working_paper_numbers_names[ab_num]}.pdf"
            working_pdf.pdf_write(output_path=output_filepath)


if __name__ == "__main__":
    main()
