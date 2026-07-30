"""
pdf_service.py
--------------
Handles extracting readable text out of an uploaded PDF file.
Kept separate from routes/upload.py because:
- Routes should only handle HTTP request/response logic
- Actual "business logic" (PDF parsing) belongs in services/
This separation makes the code easier to test and reuse later.
"""

from PyPDF2 import PdfReader


def extract_text_from_pdf(file_stream):
    """
    Takes an uploaded PDF file (in-memory stream) and returns
    all extracted text as a single string.

    file_stream: the file object Flask gives us from request.files
    """
    reader = PdfReader(file_stream)

    extracted_text = ""
    for page_num, page in enumerate(reader.pages):
        page_text = page.extract_text()
        if page_text:  # some pages (e.g. scanned images) may return None
            extracted_text += page_text + "\n"

    if not extracted_text.strip():
        # This happens if the PDF is scanned images with no real text layer
        raise ValueError(
            "No readable text found in this PDF. "
            "It might be a scanned/image-based PDF (OCR not supported yet)."
        )

    return extracted_text.strip()