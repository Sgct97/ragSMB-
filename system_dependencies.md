# System-Level Dependencies for Enterprise-Grade RAG Pipeline

This document lists the system-level libraries required for the `unstructured` Python package to process all document types correctly. These must be installed on your operating system before running the full application.

## Rationale

The `unstructured` library relies on several powerful, underlying open-source tools to parse complex file formats like PDFs, images, and various Microsoft Office documents. These tools are not Python packages and must be managed by your system's package manager.

## Required Dependencies

- **`libmagic`**: For accurate file type detection.
- **`poppler`**: For robust PDF processing.
- **`tesseract`**: For Optical Character Recognition (OCR) to extract text from images and scanned documents.

## Installation Instructions

Please run the appropriate command for your operating system.

### For Debian/Ubuntu-based Linux:

```bash
sudo apt-get update && sudo apt-get install -y libmagic1 poppler-utils tesseract-ocr
```

### For macOS (using Homebrew):

If you do not have Homebrew, you can install it from [https://brew.sh/](https://brew.sh/).

```bash
brew install libmagic poppler tesseract
```

### For Windows (using Chocolatey or another package manager):

Installation on Windows can be more complex. Please refer to the official installation guides for each dependency.

- **Poppler for Windows:** Often included with other PDF tools or can be downloaded manually.
- **Tesseract for Windows:** Installers are available from the official Tesseract GitHub repository.

**Note:** Failing to install these dependencies may not cause an immediate crash, but it will lead to errors or poor-quality text extraction when processing certain file types. 