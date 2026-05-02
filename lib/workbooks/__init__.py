from .F42_Beltz_TT_Zwangsstörungen_Fricke import (F42_extract_working_sheet_numbers_names,
                                                  F42_extract_working_sheet_pages)
from .F43_1_Beltz_TT_Posttraumatische_Belastungsstörung_Lühr_et_al import (F43_1_extract_working_sheet_numbers_names,
                                                                           F43_1_extract_working_sheet_pages)


BOOK_STRATEGIES = {
    "F42": {
        "name_func": F42_extract_working_sheet_numbers_names,
        "page_func": F42_extract_working_sheet_pages,
        "toc_pages": [316, 317]
    },
    "F43_1": {
        "name_func": F43_1_extract_working_sheet_numbers_names,
        "page_func": F43_1_extract_working_sheet_pages,
        "toc_pages": [6, 7, 8, 9, 10, 11]
    }
}