from .F42_Beltz_TT_Zwangsstörungen_Fricke import (
    F42_extract_working_sheet_numbers_names,
    F42_extract_working_sheet_pages
)

BOOK_STRATEGIES = {
    "F42": {
        "name_func": F42_extract_working_sheet_numbers_names,
        "page_func": F42_extract_working_sheet_pages,
        "toc_pages": [316, 317]
    }
}