"""Process router — DataJuri lookup, PDF bookmarks, Zion activities."""

import logging
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from pydantic import BaseModel

from app.models.usuario import Usuario
from app.routers.auth import get_current_user
from app.services import datajuri_service, pdf_service, zion_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/processo", tags=["processo"])


class ProcessoSearch(BaseModel):
    pasta_ou_cnj: str


# --- DataJuri ---


@router.get("/buscar")
def buscar_processo(
    q: str = Query(..., description="Pasta number or CNJ"),
    user: Usuario = Depends(get_current_user),
):
    """Search for a case in DataJuri by pasta or CNJ."""
    result = datajuri_service.buscar_processo(q)
    if not result:
        raise HTTPException(404, f"Processo não encontrado: {q}")
    return result


@router.get("/partes/{processo_id}")
def get_partes(
    processo_id: str,
    user: Usuario = Depends(get_current_user),
):
    """Get parties for a case."""
    partes = datajuri_service.buscar_partes(processo_id)
    return {"partes": partes}


# --- PDF Bookmarks ---


@router.post("/pdf/bookmarks")
async def extract_pdf_bookmarks(
    file: UploadFile = File(...),
    user: Usuario = Depends(get_current_user),
):
    """Extract bookmarks/pieces from a PJe PDF.

    Returns list of pieces with title, type, page range for the user to select.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Arquivo deve ser PDF")

    content = await file.read()
    if len(content) > 100 * 1024 * 1024:  # 100MB limit for PJe PDFs
        raise HTTPException(400, "Arquivo muito grande (max 100MB)")

    bookmarks = pdf_service.extract_bookmarks(content)

    if not bookmarks:
        # No bookmarks — treat as single document
        text = pdf_service.extract_full_text(content)
        return {
            "has_bookmarks": False,
            "total_pages": len(text) > 0,
            "pieces": [],
            "text_preview": text[:500] if text else "",
        }

    # Categorize pieces for easy filtering
    decisoes = [p for p in bookmarks if p["type"].startswith("DECISAO")]
    pecas_cliente = [
        p for p in bookmarks
        if p["type"] in ("PECA_CONTESTACAO", "PECA_IMPUGNACAO", "PECA_RAZOES_FINAIS", "PECA_REPLICA")
    ]

    return {
        "has_bookmarks": True,
        "total_pieces": len(bookmarks),
        "pieces": bookmarks,
        "decisoes": decisoes,
        "pecas_cliente": pecas_cliente,
        "suggested_decision": decisoes[-1] if decisoes else None,  # Most recent decision
    }


@router.post("/pdf/extract-piece")
async def extract_piece_text(
    file: UploadFile = File(...),
    start_page: int = Query(..., ge=1),
    end_page: int = Query(..., ge=1),
    user: Usuario = Depends(get_current_user),
):
    """Extract text from a specific page range of a PDF (selected piece)."""
    content = await file.read()
    text = pdf_service.extract_text_from_pages(content, start_page, end_page)
    return {
        "text": text,
        "pages": end_page - start_page + 1,
        "chars": len(text),
    }


# --- Zion Activities ---


@router.get("/atividades")
def listar_atividades(
    tipo: str | None = Query(None, description="Filter by activity type"),
    limit: int = Query(30, ge=1, le=100),
    user: Usuario = Depends(get_current_user),
):
    """List open Zion activities for analysis.

    Filters for 'Verificar' type activities by default.
    """
    atividades = zion_service.listar_atividades(
        tipo=tipo or "Verificar",
        limit=limit,
    )
    return {"atividades": atividades, "count": len(atividades)}
