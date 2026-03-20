"""Zion MySQL service — list open activities for the logged-in user.

Reads from ViewGrdAtividadesTarcisio in the Zion MySQL database.
"""

import logging

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def _get_connection():
    """Get MySQL connection to Zion database."""
    import mysql.connector

    return mysql.connector.connect(
        host=settings.zion_db_host,
        port=settings.zion_db_port,
        user=settings.zion_db_user,
        password=settings.zion_db_password,
        database=settings.zion_db_database,
    )


def listar_atividades(
    tipo: str | None = None,
    responsavel: str | None = None,
    limit: int = 50,
) -> list[dict]:
    """List open activities from Zion.

    Args:
        tipo: Filter by activity type (e.g., 'Verificar', 'Analisar Decisão')
        responsavel: Filter by responsible user name
        limit: Max results

    Returns:
        List of activity dicts with keys: id, tipo, assunto, responsavel, pasta, data_fatal
    """
    if not settings.zion_db_host:
        logger.warning("Zion DB not configured")
        return []

    try:
        conn = _get_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT
                activity_id as id,
                activity_type as tipo,
                activity_subject as assunto,
                user_profile_name as responsavel,
                activity_folder as pasta,
                activity_date as data,
                activity_fatal as data_fatal
            FROM ViewGrdAtividadesTarcisio
            WHERE activity_status = 'Aberta'
        """
        params = []

        if tipo:
            query += " AND activity_type LIKE %s"
            params.append(f"%{tipo}%")

        if responsavel:
            query += " AND user_profile_name LIKE %s"
            params.append(f"%{responsavel}%")

        query += " ORDER BY activity_fatal ASC LIMIT %s"
        params.append(limit)

        cursor.execute(query, params)
        results = cursor.fetchall()

        cursor.close()
        conn.close()

        # Convert dates to strings
        for r in results:
            for key in ("data", "data_fatal"):
                if r.get(key) and hasattr(r[key], "isoformat"):
                    r[key] = r[key].isoformat()

        return results

    except Exception as e:
        logger.error("Zion query failed: %s", e)
        return []
