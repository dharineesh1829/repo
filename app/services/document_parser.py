"""
Document extraction and sanitization service for PDF, DOCX, and TXT files.
"""
import io
import re
from typing import Tuple
from pypdf import PdfReader
from docx import Document
from app.config import MAX_UPLOAD_SIZE_MB

class DocumentParsingError(Exception):
    """Custom exception for user-friendly parsing error messages."""
    pass

def sanitize_text(text: str) -> str:
    """Removes null bytes, excessive whitespace, and non-printable control characters."""
    if not text:
        return ""
    # Remove null characters
    text = text.replace('\x00', '')
    # Normalize multiple line breaks to at most two
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Normalize tab and excessive spaces
    text = re.sub(r'[ \t]{2,}', ' ', text)
    return text.strip()

def parse_pdf(file_bytes: bytes) -> str:
    """Extracts text from PDF bytes using pypdf."""
    try:
        pdf_file = io.BytesIO(file_bytes)
        reader = PdfReader(pdf_file)
        if len(reader.pages) == 0:
            raise DocumentParsingError("The uploaded PDF file contains no pages.")
        
        extracted_pages = []
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            if page_text.strip():
                extracted_pages.append(page_text.strip())
        
        full_text = "\n\n".join(extracted_pages)
        if not full_text.strip():
            raise DocumentParsingError("Unable to extract text from this PDF. It might be scanned or image-based.")
        
        return sanitize_text(full_text)
    except DocumentParsingError:
        raise
    except Exception as e:
        raise DocumentParsingError(f"Corrupted or invalid PDF file: {str(e)}")

def parse_docx(file_bytes: bytes) -> str:
    """Extracts text from DOCX bytes using python-docx."""
    try:
        docx_file = io.BytesIO(file_bytes)
        doc = Document(docx_file)
        
        paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        
        # Also extract text from tables if present
        for table in doc.tables:
            for row in table.rows:
                row_text = " | ".join([cell.text.strip() for cell in row.cells if cell.text.strip()])
                if row_text:
                    paragraphs.append(row_text)
        
        full_text = "\n\n".join(paragraphs)
        if not full_text.strip():
            raise DocumentParsingError("The uploaded DOCX document contains no readable text.")
        
        return sanitize_text(full_text)
    except DocumentParsingError:
        raise
    except Exception as e:
        raise DocumentParsingError(f"Corrupted or invalid DOCX document: {str(e)}")

def parse_txt(file_bytes: bytes) -> str:
    """Extracts text from TXT bytes with multi-encoding fallback."""
    encodings = ['utf-8', 'utf-16', 'latin-1', 'cp1252']
    for enc in encodings:
        try:
            text = file_bytes.decode(enc)
            if text.strip():
                return sanitize_text(text)
        except UnicodeDecodeError:
            continue
    raise DocumentParsingError("Unable to decode the text file with supported encodings (UTF-8, UTF-16, Latin-1).")

def extract_document_text(filename: str, file_bytes: bytes) -> Tuple[str, str]:
    """
    Validates, extracts, and sanitizes text from uploaded files.
    Returns (clean_text, detected_file_type).
    """
    if not file_bytes or len(file_bytes) == 0:
        raise DocumentParsingError("Uploaded file is completely empty. Please select a valid file.")
    
    max_bytes = MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(file_bytes) > max_bytes:
        raise DocumentParsingError(f"File size ({len(file_bytes)/(1024*1024):.1f}MB) exceeds maximum limit of {MAX_UPLOAD_SIZE_MB}MB.")
    
    filename_lower = filename.lower()
    
    if filename_lower.endswith('.pdf'):
        return parse_pdf(file_bytes), "PDF"
    elif filename_lower.endswith('.docx') or filename_lower.endswith('.doc'):
        return parse_docx(file_bytes), "DOCX"
    elif filename_lower.endswith('.txt') or filename_lower.endswith('.md') or filename_lower.endswith('.rtf'):
        return parse_txt(file_bytes), "TXT"
    else:
        raise DocumentParsingError(
            f"Unsupported file format '{filename}'. Please upload a PDF, DOCX, or TXT file, or paste your text directly."
        )
