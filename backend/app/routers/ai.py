"""AI router — PDF extraction, analysis, email generation with SSE streaming."""

import logging
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models.ai_log import AILog
from app.models.usuario import Usuario
from app.routers.auth import get_current_user
from app.services import ai_service, prompt_service

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter(prefix="/api/ai", tags=["ai"])


class ExtractionRequest(BaseModel):
    text: str
    model: str | None = None


class AnalysisRequest(BaseModel):
    area: str
    tipo_decisao: str
    texto_decisao: str
    papel_cliente: str = ""
    numero_processo: str = ""
    cliente: str = ""
    adverso: str = ""
    fase_processual: str = ""
    dossie_resumo: str = ""
    texto_pecas_cliente: str = ""
    model: str | None = None
    analise_id: int | None = None


class EmailRequest(BaseModel):
    area: str
    fase: str | None = None
    dados_analise: dict
    model: str | None = None
    analise_id: int | None = None


@router.post("/extract-pdf")
async def extract_pdf(
    file: UploadFile = File(...),
    model: str = Form(None),
    user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Extract structured data from a PDF decision."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Arquivo deve ser PDF")

    content = await file.read()
    if len(content) > 50 * 1024 * 1024:  # 50MB limit
        raise HTTPException(400, "Arquivo muito grande (max 50MB)")

    # Extract text from PDF
    try:
        import fitz  # PyMuPDF

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        doc = fitz.open(tmp_path)
        text_parts = []
        for page in doc:
            text_parts.append(page.get_text())
        doc.close()
        Path(tmp_path).unlink(missing_ok=True)

        pdf_text = "\n".join(text_parts)
        if len(pdf_text) > 200000:
            pdf_text = pdf_text[:200000] + "\n\n[... texto truncado por limite de tamanho ...]"

    except Exception as e:
        logger.error("PDF extraction failed: %s", e)
        raise HTTPException(500, f"Erro ao extrair texto do PDF: {e}")

    # Call LLM for structured extraction
    extraction_prompt = prompt_service.compose_extraction_prompt()
    result = await ai_service.chat_completion(
        system_prompt=extraction_prompt,
        user_message=f"Analise o seguinte documento judicial:\n\n{pdf_text}",
        model=model or settings.openai_model,  # OpenAI is better for structured extraction
        json_mode=True,
    )

    # Log AI call
    ai_log = AILog(
        etapa="extracao",
        prompt_name="_base_extracao",
        modelo=result.get("model"),
        tokens_input=result.get("tokens_input"),
        tokens_output=result.get("tokens_output"),
        duracao_ms=result.get("duration_ms"),
    )
    db.add(ai_log)
    db.commit()

    return {
        "extracted": result.get("parsed") or result.get("content"),
        "pdf_text_length": len(pdf_text),
        "model": result.get("model"),
        "tokens": {
            "input": result.get("tokens_input"),
            "output": result.get("tokens_output"),
        },
    }


@router.post("/analyze")
async def analyze_decision(
    body: AnalysisRequest,
    user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Analyze a decision (ED viability, resource suggestion, etc.)."""
    # Compose prompt
    system_prompt = prompt_service.compose_analysis_prompt(
        area=body.area,
        tipo_decisao=body.tipo_decisao,
        contexto={
            "papel_cliente": body.papel_cliente,
            "numero_processo": body.numero_processo,
            "cliente": body.cliente,
            "adverso": body.adverso,
            "fase_processual": body.fase_processual,
            "dossie_resumo": body.dossie_resumo,
        },
    )

    user_message = f"## DECISÃO JUDICIAL\n\n{body.texto_decisao}"
    if body.texto_pecas_cliente:
        user_message += f"\n\n## PEÇAS DO CLIENTE\n\n{body.texto_pecas_cliente}"

    result = await ai_service.chat_completion(
        system_prompt=system_prompt,
        user_message=user_message,
        model=body.model or settings.anthropic_model,  # Claude for deep analysis
        json_mode=False,
    )

    # Log
    ai_log = AILog(
        analise_id=body.analise_id,
        etapa="analise",
        prompt_name=f"{body.area}/{body.tipo_decisao}",
        modelo=result.get("model"),
        tokens_input=result.get("tokens_input"),
        tokens_output=result.get("tokens_output"),
        duracao_ms=result.get("duration_ms"),
    )
    db.add(ai_log)
    db.commit()

    return {
        "analysis": result.get("parsed") or result.get("content"),
        "raw": result.get("content"),
        "model": result.get("model"),
    }


@router.post("/analyze/stream")
async def analyze_decision_stream(
    body: AnalysisRequest,
    user: Usuario = Depends(get_current_user),
):
    """Stream analysis response via SSE."""
    system_prompt = prompt_service.compose_analysis_prompt(
        area=body.area,
        tipo_decisao=body.tipo_decisao,
        contexto={
            "papel_cliente": body.papel_cliente,
            "numero_processo": body.numero_processo,
            "cliente": body.cliente,
            "adverso": body.adverso,
            "fase_processual": body.fase_processual,
            "dossie_resumo": body.dossie_resumo,
        },
    )

    user_message = f"## DECISÃO JUDICIAL\n\n{body.texto_decisao}"
    if body.texto_pecas_cliente:
        user_message += f"\n\n## PEÇAS DO CLIENTE\n\n{body.texto_pecas_cliente}"

    async def event_generator():
        async for chunk in ai_service.stream_completion(
            system_prompt=system_prompt,
            user_message=user_message,
            model=body.model or settings.anthropic_model,
        ):
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/generate-email")
async def generate_email(
    body: EmailRequest,
    user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate email draft using LLM."""
    email_prompt = prompt_service.compose_email_prompt(body.area, body.fase)

    # Build context from analysis data
    dados = body.dados_analise
    context_text = f"""Dados da análise para gerar o email:

{_format_dados_for_llm(dados)}"""

    result = await ai_service.chat_completion(
        system_prompt=email_prompt,
        user_message=context_text,
        model=body.model or settings.anthropic_model,
    )

    # Log
    ai_log = AILog(
        analise_id=body.analise_id,
        etapa="geracao_email",
        prompt_name=f"gerador_email/{body.area}",
        modelo=result.get("model"),
        tokens_input=result.get("tokens_input"),
        tokens_output=result.get("tokens_output"),
        duracao_ms=result.get("duration_ms"),
    )
    db.add(ai_log)
    db.commit()

    return {
        "email_body": result.get("content"),
        "model": result.get("model"),
    }


@router.get("/prompts")
def list_prompts(user: Usuario = Depends(get_current_user)):
    """List all available analysis prompts."""
    return prompt_service.list_available_prompts()


def _format_dados_for_llm(dados: dict) -> str:
    """Format analysis data dict as readable text for LLM context."""
    parts = []
    for key, value in dados.items():
        if value is not None and value != "" and value != []:
            label = key.replace("_", " ").title()
            if isinstance(value, list):
                parts.append(f"**{label}:**")
                for item in value:
                    if isinstance(item, dict):
                        parts.append(f"  - {item}")
                    else:
                        parts.append(f"  - {item}")
            else:
                parts.append(f"**{label}:** {value}")
    return "\n".join(parts)
