# Working Sheet PDF Extractor

A Python tool for extracting individual working sheets from PDF documents of psychological therapy books. It automatically identifies and splits sheets based on predefined strategies for different book types.

## Features

- **Automatic Sheet Detection**: Parses PDF headers to identify working sheet pages
- **Name Extraction**: Extracts sheet names from table of contents pages
- **Multi-Book Support**: Configurable strategies for different book prefixes (e.g., F42 for OCD therapy materials)
- **PDF Splitting**: Uses PyMuPDF to create individual PDF files for each sheet
- **Logging**: Comprehensive logging for debugging and monitoring

## Installation

### Prerequisites
- Python 3.8+
- pip

### Setup
1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd working_sheet_pdf_extractor
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install the package in editable mode:
   ```bash
   pip install -e .
   ```

## Usage

1. Place your PDF files in the `data/input/` directory
2. Run the extraction script:
   ```bash
   python scr/working_sheet_extractor.py
   ```
3. Find the extracted individual sheets in `data/output/`

### Supported Books
- **F42**: Beltz TT Zwangsstörungen Fricke (OCD therapy worksheets)

## Project Structure

```
working_sheet_pdf_extractor/
├── data/
│   ├── input/          # Place PDF files here
│   └── output/         # Extracted sheets saved here
├── lib/
│   ├── logging.py      # Centralized logging setup
│   ├── pdfIO.py        # PDF reading/writing utilities
│   └── workbooks/      # Book-specific extraction strategies
│       ├── __init__.py
│       └── F42_Beltz_TT_Zwangsstörungen_Fricke.py
├── scr/
│   ├── __init__.py
│   └── working_sheet_extractor.py  # Main script
├── pyproject.toml      # Project configuration
└── README.md
```

## Configuration

### Adding New Book Strategies
1. Create a new file in `lib/workbooks/` (e.g., `F43.py`)
2. Implement extraction functions for names and pages
3. Add the strategy to `BOOK_STRATEGIES` in `__init__.py`

### Logging
- Console logging level: INFO (configurable in `lib/logging.py`)
- Debug logs available by changing root level to DEBUG

## Dependencies

- PyMuPDF (pymupdf): For PDF parsing and manipulation
- Standard library: pathlib, re, collections, logging