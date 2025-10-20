from __future__ import annotations
from lib.logging import get_logger
from lib.pdfIO import read_pdf
logger = get_logger(__name__)

class F43_1_Beltz_TT_Postraumatische_Belastungsstörung_Lühr_et_al:
    """
    Workbook handler that reads a PDF and extracts entries listed under the
    heading 'Übersicht Arbeitsblätter' in the form 'AB id / NAME PAGE'.
    """

    def __init__(self, pdf_path: str) -> None:
        self.pags = read_pdf(pdf_path=pdf_path)
