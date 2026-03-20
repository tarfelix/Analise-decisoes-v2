"""Parser service — migrated and improved from parser.py v2.

Parses legal claim/request tables from CSV, Excel, TXT, or pasted text.
"""

import io
import logging
from dataclasses import asdict, dataclass

import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class PedidoData:
    Objetos: str = ""
    Situacao: str = "N/A"
    Res1: str = "N/A"
    Res2: str = "N/A"
    ResSup: str = "N/A"


# Column name mappings (flexible matching)
COLUMN_MAP = {
    "objetos": ["objeto", "pedido", "objetos", "descrição", "descricao"],
    "situacao": ["situação", "situacao", "status"],
    "res1": ["resultado 1ª instância", "resultado 1a instancia", "res1", "1ª inst", "1a inst"],
    "res2": ["resultado 2ª instância", "resultado 2a instancia", "res2", "2ª inst", "2a inst"],
    "res_sup": [
        "resultado instância superior",
        "resultado instancia superior",
        "res_sup",
        "inst superior",
        "instância sup",
    ],
}


def _match_column(col_name: str) -> str | None:
    """Match a column name to a known field."""
    normalized = col_name.strip().lower()
    for field, variants in COLUMN_MAP.items():
        if any(v in normalized for v in variants):
            return field
    return None


def _df_to_pedidos(df: pd.DataFrame) -> list[PedidoData]:
    """Convert a DataFrame to a list of PedidoData."""
    # Map columns
    col_mapping = {}
    for col in df.columns:
        match = _match_column(str(col))
        if match:
            col_mapping[col] = match

    if "objetos" not in col_mapping.values():
        return []

    pedidos = []
    for _, row in df.iterrows():
        data = {"Objetos": "", "Situacao": "N/A", "Res1": "N/A", "Res2": "N/A", "ResSup": "N/A"}
        for orig_col, mapped in col_mapping.items():
            val = str(row.get(orig_col, "")).strip()
            if not val or val.lower() == "nan":
                val = "N/A"
            field_map = {
                "objetos": "Objetos",
                "situacao": "Situacao",
                "res1": "Res1",
                "res2": "Res2",
                "res_sup": "ResSup",
            }
            data[field_map[mapped]] = val

        if data["Objetos"] and data["Objetos"] != "N/A":
            pedidos.append(PedidoData(**data))

    return sorted(pedidos, key=lambda p: p.Objetos)


def parse_file(file_bytes: bytes, filename: str) -> list[PedidoData] | str:
    """Parse an uploaded file (CSV, Excel, TXT) into PedidoData list.

    Returns list of PedidoData on success, or error message string on failure.
    """
    try:
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

        if ext in ("xlsx", "xls"):
            df = pd.read_excel(io.BytesIO(file_bytes))
        elif ext == "csv":
            # Try different delimiters
            text = file_bytes.decode("utf-8", errors="replace")
            for sep in ["\t", ";", ","]:
                df = pd.read_csv(io.StringIO(text), sep=sep)
                if len(df.columns) > 1:
                    break
        elif ext == "txt":
            text = file_bytes.decode("utf-8", errors="replace")
            df = pd.read_csv(io.StringIO(text), sep="\t")
            if len(df.columns) <= 1:
                df = pd.read_csv(io.StringIO(text), sep=r"\s{2,}", engine="python")
        else:
            return f"Formato não suportado: {ext}"

        pedidos = _df_to_pedidos(df)
        if not pedidos:
            return "Nenhum pedido encontrado. Verifique o formato da tabela."
        return pedidos

    except Exception as e:
        logger.error("Error parsing file %s: %s", filename, e)
        return f"Erro ao processar arquivo: {e}"


def parse_text(text: str) -> list[PedidoData] | str:
    """Parse pasted text into PedidoData list."""
    if not text or not text.strip():
        return "Texto vazio."

    try:
        # Try tab-delimited first
        df = pd.read_csv(io.StringIO(text), sep="\t")
        if len(df.columns) <= 1:
            df = pd.read_csv(io.StringIO(text), sep=r"\s{2,}", engine="python")

        pedidos = _df_to_pedidos(df)
        if not pedidos:
            return "Nenhum pedido encontrado. Verifique o formato do texto."
        return pedidos

    except Exception as e:
        logger.error("Error parsing text: %s", e)
        return f"Erro ao processar texto: {e}"


def pedidos_to_dicts(pedidos: list[PedidoData]) -> list[dict]:
    """Convert PedidoData list to serializable dicts."""
    return [asdict(p) for p in pedidos]
