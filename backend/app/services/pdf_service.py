"""PDF processing service — bookmark extraction and text extraction.

Based on portal-soares-picon/utils/pdf_intel.py.
"""

import io
import logging
import re
from typing import Any

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)

# PJe ID pattern at end of bookmark titles (hex hash)
PJE_ID_RE = re.compile(r"(?:[-–—]\s*)([0-9a-f]{6,12})\s*$", re.IGNORECASE)

# Piece type classification patterns
PIECE_PATTERNS: list[tuple[str, str]] = [
    (r"senten[cç]a", "DECISAO_SENTENCA"),
    (r"ac[oó]rd[aã]o", "DECISAO_ACORDAO"),
    (r"despacho", "DESPACHO"),
    (r"decis[aã]o\s+interlocut[oó]ria", "DECISAO"),
    (r"decis[aã]o", "DECISAO"),
    (r"embargo", "EMBARGOS"),
    (r"certid[aã]o", "CERTIDAO"),
    (r"intima[cç][aã]o", "INTIMACAO"),
    (r"notifica[cç][aã]o", "INTIMACAO"),
    (r"peti[cç][aã]o\s+inicial", "PECA_INICIAL"),
    (r"reclama[cç][aã]o\s+trabalhista", "PECA_INICIAL"),
    (r"contesta[cç][aã]o", "PECA_CONTESTACAO"),
    (r"defesa", "PECA_CONTESTACAO"),
    (r"r[eé]plica", "PECA_REPLICA"),
    (r"impugna[cç][aã]o", "PECA_IMPUGNACAO"),
    (r"raz[oõ]es\s+finais", "PECA_RAZOES_FINAIS"),
    (r"alega[cç][oõ]es\s+finais", "PECA_RAZOES_FINAIS"),
    (r"procura[cç][aã]o", "PROCURACAO"),
    (r"carta\s+de\s+preposi[cç][aã]o", "CARTA_PREPOSICAO"),
    (r"substabele", "PROCURACAO"),
    (r"ata\s+(?:de\s+)?audi[eê]ncia", "ATA_AUDIENCIA"),
    (r"laudo|per[ií]cia", "PROVA_TECNICA"),
    (r"c[aá]lculo", "CALCULOS"),
    (r"recurso\s+ordin[aá]rio", "RECURSO"),
    (r"recurso", "RECURSO"),
    (r"contrarraz[oõ]es", "CONTRARRAZOES"),
    (r"agravo", "AGRAVO"),
]


def guess_piece_type(title: str) -> str:
    """Classify a PDF bookmark title into a piece type."""
    lower = title.lower().strip()
    for pattern, piece_type in PIECE_PATTERNS:
        if re.search(pattern, lower):
            return piece_type
    return "OUTRO"


def extract_pje_id(title: str) -> str:
    """Extract PJe hex ID from bookmark title."""
    match = PJE_ID_RE.search(title)
    return match.group(1) if match else ""


def extract_bookmarks(pdf_bytes: bytes) -> list[dict[str, Any]]:
    """Extract bookmarks/TOC from a PJe PDF.

    Returns list of pieces with title, type, page range, etc.
    """
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as e:
        logger.error("Failed to open PDF: %s", e)
        return []

    toc = doc.get_toc(simple=True)  # [(level, title, page), ...]
    total_pages = len(doc)
    doc.close()

    if not toc:
        return []

    pieces = []
    for i, (level, title, start_page) in enumerate(toc):
        # Calculate end page (next bookmark's start - 1, or last page)
        if i + 1 < len(toc):
            end_page = toc[i + 1][2] - 1
        else:
            end_page = total_pages

        end_page = max(end_page, start_page)

        pieces.append({
            "index": i,
            "level": level,
            "title": title.strip(),
            "start_page": start_page,
            "end_page": end_page,
            "pages": end_page - start_page + 1,
            "type": guess_piece_type(title),
            "pje_id": extract_pje_id(title),
        })

    return pieces


def extract_text_from_pages(pdf_bytes: bytes, start_page: int, end_page: int) -> str:
    """Extract text from specific page range of a PDF.

    Pages are 1-indexed (matching bookmark data).
    """
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as e:
        logger.error("Failed to open PDF: %s", e)
        return ""

    text_parts = []
    # Convert to 0-indexed
    for page_num in range(start_page - 1, min(end_page, len(doc))):
        page = doc[page_num]
        text_parts.append(page.get_text())

    doc.close()
    text = "\n".join(text_parts)

    # Limit text size for LLM context
    if len(text) > 200000:
        text = text[:200000] + "\n\n[... texto truncado por limite de tamanho ...]"

    return text


def extract_full_text(pdf_bytes: bytes, max_chars: int = 200000) -> str:
    """Extract all text from a PDF."""
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as e:
        logger.error("Failed to open PDF: %s", e)
        return ""

    text_parts = []
    total = 0
    for page in doc:
        t = page.get_text()
        text_parts.append(t)
        total += len(t)
        if total > max_chars:
            break

    doc.close()
    text = "\n".join(text_parts)
    if len(text) > max_chars:
        text = text[:max_chars] + "\n\n[... texto truncado ...]"
    return text
