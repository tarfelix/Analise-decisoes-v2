"""Loads and composes prompts from the prompts/ directory.

Prompts are Markdown files organized by area and decision type.
Composition: _base prompt + specific prompt, with dynamic context injection.
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


def load_prompt(name: str) -> str:
    """Load a prompt file by name (e.g., 'trabalhista/sentenca' or '_base_analise')."""
    path = PROMPTS_DIR / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(f"Prompt not found: {path}")
    return path.read_text(encoding="utf-8")


def compose_analysis_prompt(area: str, tipo_decisao: str, contexto: dict) -> str:
    """Compose a full analysis prompt from base + specific + context.

    Args:
        area: 'trabalhista', 'civel', 'empresarial'
        tipo_decisao: 'sentenca', 'acordao_trt', 'embargos_declaracao', etc.
        contexto: dict with keys like papel_cliente, partes, dossie_resumo, etc.

    Returns:
        Fully composed prompt string ready for LLM.
    """
    # Load base prompt
    base = load_prompt("_base_analise")

    # Try specific prompt, fall back to generic
    specific_name = f"{area}/{tipo_decisao}"
    try:
        specific = load_prompt(specific_name)
    except FileNotFoundError:
        logger.warning("No specific prompt for %s, using base only", specific_name)
        specific = ""

    # Build context section
    context_parts = []
    if contexto.get("papel_cliente"):
        context_parts.append(f"**Polo do Cliente:** {contexto['papel_cliente']}")
    if contexto.get("numero_processo"):
        context_parts.append(f"**Processo:** {contexto['numero_processo']}")
    if contexto.get("cliente"):
        context_parts.append(f"**Cliente:** {contexto['cliente']}")
    if contexto.get("adverso"):
        context_parts.append(f"**Parte Adversa:** {contexto['adverso']}")
    if contexto.get("fase_processual"):
        context_parts.append(f"**Fase:** {contexto['fase_processual']}")
    if contexto.get("dossie_resumo"):
        context_parts.append(f"\n**Dossiê do Processo:**\n{contexto['dossie_resumo']}")

    context_section = "\n".join(context_parts) if context_parts else ""

    # Compose full prompt
    full = f"{base}\n\n{specific}"
    if context_section:
        full += f"\n\n## CONTEXTO DO CASO\n\n{context_section}"

    return full


def compose_email_prompt(area: str, fase: str | None = None) -> str:
    """Compose prompt for email generation."""
    specific_name = f"gerador_email/{area}"
    if fase:
        specific_name = f"gerador_email/{area}_{fase}"

    try:
        return load_prompt(specific_name)
    except FileNotFoundError:
        return load_prompt("gerador_email/generico")


def compose_extraction_prompt() -> str:
    """Compose prompt for PDF data extraction."""
    return load_prompt("_base_extracao")


def list_available_prompts() -> dict[str, list[str]]:
    """List all available prompts organized by area."""
    result: dict[str, list[str]] = {}
    for path in sorted(PROMPTS_DIR.rglob("*.md")):
        rel = path.relative_to(PROMPTS_DIR)
        parts = rel.parts
        if len(parts) == 1:
            result.setdefault("_base", []).append(rel.stem)
        elif len(parts) == 2:
            area = parts[0]
            result.setdefault(area, []).append(Path(parts[1]).stem)
    return result
