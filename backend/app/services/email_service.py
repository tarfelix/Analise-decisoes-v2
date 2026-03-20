"""Email generation service — migrated from utils_email.py v2.

Generates professional email subject and body for legal decision notifications.
Supports both template-based (deterministic) and LLM-enhanced generation.
"""

import logging
from dataclasses import dataclass
from datetime import date

logger = logging.getLogger(__name__)


@dataclass
class Prazo:
    descricao: str
    data_d: str
    data_fatal: str
    obs: str = ""


def format_date_br(d: date | str | None) -> str:
    """Format date as DD/MM/YYYY."""
    if d is None:
        return ""
    if isinstance(d, str):
        # Try ISO format
        try:
            from datetime import datetime
            d = datetime.fromisoformat(d).date()
        except ValueError:
            return d
    return d.strftime("%d/%m/%Y")


def format_prazos(prazos: list[Prazo]) -> str:
    """Format deadlines for email body."""
    if not prazos:
        return ""
    lines = []
    for i, p in enumerate(prazos, 1):
        line = f"{i}. {p.descricao}"
        if p.data_d:
            line += f"\n   D-: {p.data_d}"
        if p.data_fatal:
            line += f"\n   Fatal: {p.data_fatal}"
        if p.obs:
            line += f"\n   Obs: {p.obs}"
        lines.append(line)
    return "\n\n".join(lines)


def format_pedidos_email(pedidos: list[dict], tipo_decisao: str = "") -> str:
    """Format claims/requests for email body."""
    if not pedidos:
        return ""

    lines = []
    for i, p in enumerate(pedidos, 1):
        obj = p.get("Objetos") or p.get("objeto", "")
        parts = [f"{i}. {obj}"]

        situacao = p.get("Situacao") or p.get("situacao", "N/A")
        if situacao and situacao != "N/A":
            parts.append(f"   Situação: {situacao}")

        # Show results based on decision type context
        for label, key in [
            ("1ª Inst.", "Res1"), ("1ª Inst.", "res1"),
            ("2ª Inst.", "Res2"), ("2ª Inst.", "res2"),
            ("Inst. Sup.", "ResSup"), ("Inst. Sup.", "res_sup"),
        ]:
            val = p.get(key, "")
            if val and val not in ("N/A", "Aguardando julgamento", ""):
                parts.append(f"   {label}: {val}")

        lines.append("\n".join(parts))

    return "\n\n".join(lines)


def generate_email_subject(
    tipo_decisao: str,
    fase: str,
    area: str,
    adverso: str = "",
    cliente: str = "",
    numero_processo: str = "",
) -> str:
    """Generate email subject line."""
    area_prefix = area.upper() if area else "TRABALHISTA"
    fase_label = f"({fase})" if fase else ""
    parties = f"{adverso} X {cliente}" if adverso and cliente else ""
    proc = f"- Proc {numero_processo}" if numero_processo else ""

    parts = [f"{area_prefix}:", tipo_decisao, fase_label, "-", parties, proc]
    return " ".join(p for p in parts if p).strip()


def generate_email_body(
    *,
    # Contexto
    area: str = "trabalhista",
    fase_processual: str = "",
    tipo_decisao: str = "",
    data_ciencia: str = "",
    papel_cliente: str = "",
    numero_processo: str = "",
    cliente: str = "",
    adverso: str = "",
    local_vara: str = "",
    # Análise
    resultado_sentenca: str = "",
    valor_condenacao: str = "",
    obs_decisao: str = "",
    sintese_recurso: str = "",
    # ED / Recurso
    ed_status: str = "",
    ed_justificativa: str = "",
    recurso_selecionado: str = "",
    recurso_justificativa: str = "",
    garantia_necessaria: bool = False,
    status_custas: str = "",
    valor_custas: str = "",
    status_deposito: str = "",
    valor_deposito: str = "",
    guias_status: str = "",
    local_guias: str = "",
    # Execução
    calc_total: str = "",
    calc_obs: str = "",
    dep_anterior_valor: str = "",
    dep_anterior_detalhes: str = "",
    prazo_pagamento_dias: str = "",
    opcao_art_916: str = "",
    # Pedidos e Prazos
    pedidos: list[dict] | None = None,
    prazos: list[Prazo] | None = None,
    obs_finais: str = "",
) -> tuple[str, str]:
    """Generate email subject and body (template-based).

    Returns:
        (subject, body) tuple.
    """
    # Subject
    subject = generate_email_subject(
        tipo_decisao, fase_processual, area, adverso, cliente, numero_processo
    )

    # Body sections
    sections = []

    # Header
    sections.append("Prezados(as),")
    sections.append("")
    sections.append(
        f"Segue análise da decisão proferida no processo nº {numero_processo or '[Nº PROCESSO]'}, "
        f"em trâmite na {local_vara or '[LOCAL/VARA]'}, "
        f"envolvendo {cliente or '[CLIENTE]'} x {adverso or '[ADVERSO]'}."
    )

    # Publication date
    if data_ciencia:
        sections.append(f"\n**Data de ciência:** {format_date_br(data_ciencia)}")

    # Decision type & result
    if tipo_decisao:
        sections.append(f"\n**Tipo de decisão:** {tipo_decisao}")
    if resultado_sentenca:
        sections.append(f"**Resultado:** {resultado_sentenca}")
    if valor_condenacao:
        sections.append(f"**Valor da condenação/execução:** R$ {valor_condenacao}")

    # Pedidos
    if pedidos:
        pedidos_text = format_pedidos_email(pedidos, tipo_decisao)
        if pedidos_text:
            sections.append(f"\n**Pedidos analisados:**\n\n{pedidos_text}")

    # Decision observations
    if obs_decisao:
        sections.append(f"\n**Observações sobre a decisão:**\n{obs_decisao}")

    # Synthesis for appeal
    if sintese_recurso:
        sections.append(f"\n**Síntese/Objeto do recurso:**\n{sintese_recurso}")

    # ED section
    if ed_status == "Cabe ED":
        sections.append(f"\n**Embargos de Declaração:** Cabíveis")
        if ed_justificativa:
            sections.append(f"Justificativa: {ed_justificativa}")
    elif ed_status == "Não cabe ED":
        sections.append(f"\n**Embargos de Declaração:** Não cabíveis no caso")

    # Resource section
    if recurso_selecionado:
        sections.append(f"\n**Recurso sugerido:** {recurso_selecionado}")
        if recurso_justificativa:
            sections.append(f"Justificativa: {recurso_justificativa}")
        if garantia_necessaria:
            sections.append("**Atenção:** Garantia do juízo necessária para este recurso.")

    # Costs / Deposit
    cost_parts = []
    if status_custas and status_custas != "Selecione...":
        cost_parts.append(f"Custas: {status_custas}")
        if valor_custas:
            cost_parts.append(f" (R$ {valor_custas})")
    if status_deposito and status_deposito != "Selecione...":
        cost_parts.append(f"\nDepósito recursal: {status_deposito}")
        if valor_deposito:
            cost_parts.append(f" (R$ {valor_deposito})")
    if guias_status:
        cost_parts.append(f"\nGuias: {guias_status}")
        if local_guias:
            cost_parts.append(f" - {local_guias}")
    if cost_parts:
        sections.append(f"\n**Custas e depósito:**\n{''.join(cost_parts)}")

    # Execution details
    if calc_total:
        sections.append(f"\n**Total homologado:** R$ {calc_total}")
    if dep_anterior_valor:
        sections.append(
            f"**Depósitos anteriores:** R$ {dep_anterior_valor}"
            + (f" ({dep_anterior_detalhes})" if dep_anterior_detalhes else "")
        )

    # Deadlines
    if prazos:
        prazos_text = format_prazos(prazos)
        sections.append(f"\n**Prazos:**\n\n{prazos_text}")

    # Final observations
    if obs_finais:
        sections.append(f"\n**Observações finais:**\n{obs_finais}")

    # Signature
    sections.append("\n\nAtenciosamente,")
    sections.append("[NOME ADVOGADO(A)]")

    body = "\n".join(sections)
    return subject, body
