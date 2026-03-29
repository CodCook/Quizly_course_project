import PyPDF2
from io import BytesIO


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from a PDF file."""
    pdf_file = BytesIO(file_bytes)
    reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    
    for page in reader.pages:
        text += page.extract_text()
    
    return text.strip()
