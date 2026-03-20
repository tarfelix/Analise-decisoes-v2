"""DataJuri REST API client — based on sp-zion-automacao/datajuri_client.py.

Provides case lookup by pasta (folder number) or CNJ.
Uses the same API contract as the sp-zion-automacao client.
All data endpoints use the /v1 prefix.
"""

import base64
import logging
import re
import time

import requests

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_token: str | None = None
_token_expiry: float = 0

# Fields to request from DataJuri process entity
CAMPOS_PROCESSO = (
    "id,pasta,numeroProcesso,adverso.nome,cliente.nome,"
    "faseAtual.numero,faseAtual.vara,faseAtual.numeroVara,faseAtual.localidade,"
    "faseAtual.forum,faseAtual.estado,faseAtual.numeroProcesso,"
    "faseProcesso.tipoFase,faseProcesso.vara,faseProcesso.numeroVara,"
    "faseProcesso.forum,faseProcesso.localidade,faseProcesso.numeroProcesso,"
    "proprietario.nome,responsavel,"
    "listaPartesProcessoStr,listaFasesProcesso,"
    "valorCampoPersonalizado(pasta__sharepoint),"
    "valorCampoPersonalizado(processo_digital),"
    "natureza,tipoAcao,assunto,observacao,status"
)


def _authenticate() -> bool:
    """Authenticate with DataJuri OAuth2 and cache the token."""
    global _token, _token_expiry

    if not settings.datajuri_base_url or not settings.datajuri_client_id:
        logger.warning("DataJuri not configured — skipping auth")
        return False

    credentials = f"{settings.datajuri_client_id}:{settings.datajuri_secret_id}"
    b64 = base64.b64encode(credentials.encode()).decode()

    try:
        resp = requests.post(
            f"{settings.datajuri_base_url}/oauth/token",
            headers={"Authorization": f"Basic {b64}", "Content-Type": "application/x-www-form-urlencoded"},
            data={
                "grant_type": "password",
                "username": settings.datajuri_username,
                "password": settings.datajuri_password,
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        _token = data["access_token"]
        _token_expiry = time.time() + 2400  # 40 min
        return True
    except Exception as e:
        logger.warning("DataJuri auth failed: %s", e)
        return False


def _ensure_token() -> str | None:
    """Ensure a valid token exists."""
    global _token, _token_expiry
    if not _token or time.time() >= _token_expiry:
        if not _authenticate():
            return None
    return _token


def _get(path: str, params: dict | None = None) -> dict | None:
    """Make authenticated GET request to DataJuri API."""
    token = _ensure_token()
    if not token:
        return None

    try:
        resp = requests.get(
            f"{settings.datajuri_base_url}{path}",
            headers={"Authorization": f"Bearer {token}"},
            params=params,
            timeout=30,
        )
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.warning("DataJuri GET %s failed: %s", path, e)
        return None


def buscar_processo_por_pasta(pasta: str) -> dict | None:
    """Search for a case by folder number using DataJuri criterio syntax.

    Uses /v1/entidades/Processo with criterio param (same as sp-zion-automacao).
    Pasta format: '414.280 (T)', '657 (C)', etc.
    """
    pasta_sem_sufixo = re.sub(r"\s*\([TCE]\)\s*$", "", pasta, flags=re.IGNORECASE).strip()

    strategies = [
        f"pasta | igual a | {pasta}",
        f"pasta | contém | {pasta_sem_sufixo}",
    ]

    for criterio in strategies:
        data = _get("/v1/entidades/Processo", params={
            "campos": CAMPOS_PROCESSO,
            "pageSize": 5,
            "criterio": criterio,
        })

        if data and isinstance(data, dict) and data.get("rows"):
            row = data["rows"][0]
            print(f"[DATAJURI DEBUG] Raw keys: {list(row.keys())}")
            print(f"[DATAJURI DEBUG] Raw row: {row}")
            return _normalize_processo(row)

    logger.warning("Processo pasta '%s' não encontrado no DataJuri", pasta)
    return None


def _normalize_processo(row: dict) -> dict:
    """Normalize DataJuri response to ensure consistent field names.

    DataJuri may return custom fields with long keys like
    'valorCampoPersonalizado(pasta__sharepoint)'. Normalize them to shorter keys.
    Also ensure CNJ number is available under a consistent key.
    """
    result = dict(row)

    # Normalize SharePoint link — try multiple possible key names
    for key in list(result.keys()):
        if "pasta__sharepoint" in key.lower():
            result["sharepoint_link"] = result[key]
            break
    # Also try just the shorthand
    if "sharepoint_link" not in result and "pasta__sharepoint" in result:
        result["sharepoint_link"] = result["pasta__sharepoint"]

    # Normalize processo digital link
    for key in list(result.keys()):
        if "processo_digital" in key.lower():
            result["processo_digital_link"] = result[key]
            break

    # Ensure CNJ number is available — try multiple fields
    cnj = (
        result.get("faseAtual.numero")
        or result.get("faseAtual.numeroProcesso")
        or result.get("numeroProcesso")
    )
    if cnj:
        result["numero_cnj"] = cnj

    return result


def buscar_processo_por_cnj(cnj: str) -> dict | None:
    """Search for a case by CNJ number."""
    return _get(f"/v1/processo/resumoProcesso/{cnj}", {"numeroDias": 30})


def buscar_partes(processo_id: str) -> list[dict]:
    """Get parties for a case by DataJuri process ID."""
    data = _get(f"/v1/entidades/Processo/{processo_id}/partes")
    if isinstance(data, list):
        return data
    return []


def _detectar_area(pasta: str) -> str:
    """Detect area from pasta suffix: (T)=trabalhista, (C)=civel."""
    match = re.search(r"\(([TCE])\)\s*$", pasta, re.IGNORECASE)
    if match:
        return {"T": "trabalhista", "C": "civel", "E": "empresarial"}.get(
            match.group(1).upper(), ""
        )
    return ""


def buscar_processo(pasta_ou_cnj: str) -> dict | None:
    """Smart search: try pasta first, then CNJ.

    DataJuri pastas include area suffix, e.g., '414.280 (T)'.
    """
    raw = pasta_ou_cnj.strip()
    area = _detectar_area(raw)

    # Try pasta search (exact + fallback)
    result = buscar_processo_por_pasta(raw)
    if result:
        if area:
            result["_area_detectada"] = area
        return result

    # Try CNJ (if it looks like one)
    if re.match(r"\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}", raw):
        result = buscar_processo_por_cnj(raw)
        if result and area:
            result["_area_detectada"] = area
        return result

    return None
