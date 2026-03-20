"""DataJuri REST API client — simplified from sp-zion-automacao/datajuri_client.py.

Provides case lookup by pasta (folder number) or CNJ.
"""

import base64
import logging
import time

import requests

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_token: str | None = None
_token_expiry: float = 0


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
        logger.error("DataJuri auth failed: %s", e)
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
        logger.error("DataJuri GET %s failed: %s", path, e)
        return None


def buscar_processo_por_pasta(pasta: str) -> dict | None:
    """Search for a case by folder number (pasta).

    Returns dict with case data including: numero_processo, partes, vara, etc.
    """
    data = _get("/entidades/Processo", params={"pasta": pasta, "limit": 1})
    if data and isinstance(data, list) and len(data) > 0:
        return data[0]
    if data and isinstance(data, dict) and "items" in data:
        items = data["items"]
        return items[0] if items else None
    return data


def buscar_processo_por_cnj(cnj: str) -> dict | None:
    """Search for a case by CNJ number."""
    return _get(f"/processo/resumoProcesso/{cnj}")


def buscar_partes(processo_id: str) -> list[dict]:
    """Get parties for a case by DataJuri process ID."""
    data = _get(f"/entidades/Processo/{processo_id}/partes")
    if isinstance(data, list):
        return data
    return []


def buscar_processo(pasta_ou_cnj: str) -> dict | None:
    """Smart search: try pasta first, then CNJ."""
    # If it looks like a pasta (numeric, short), search by pasta
    clean = pasta_ou_cnj.strip().replace(".", "").replace("-", "")
    if clean.isdigit() and len(clean) <= 10:
        result = buscar_processo_por_pasta(pasta_ou_cnj.strip())
        if result:
            return result

    # Otherwise try CNJ
    return buscar_processo_por_cnj(pasta_ou_cnj.strip())
