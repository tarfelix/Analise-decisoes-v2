"""Dashboard router — statistics and reporting."""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.analise import Analise
from app.models.ai_log import AILog
from app.models.usuario import Usuario
from app.routers.auth import get_current_user

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats")
def get_stats(
    days: int = Query(30, ge=1, le=365),
    user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get dashboard statistics for the last N days."""
    since = datetime.now(timezone.utc) - timedelta(days=days)

    # Total analyses
    total = db.query(func.count(Analise.id)).filter(Analise.created_at >= since).scalar()

    # By area
    by_area = (
        db.query(Analise.area, func.count(Analise.id))
        .filter(Analise.created_at >= since)
        .group_by(Analise.area)
        .all()
    )

    # By decision type
    by_tipo = (
        db.query(Analise.tipo_decisao, func.count(Analise.id))
        .filter(Analise.created_at >= since, Analise.tipo_decisao.isnot(None))
        .group_by(Analise.tipo_decisao)
        .all()
    )

    # By user
    by_user = (
        db.query(Usuario.nome, func.count(Analise.id))
        .join(Usuario, Analise.usuario_id == Usuario.id)
        .filter(Analise.created_at >= since)
        .group_by(Usuario.nome)
        .all()
    )

    # By status
    by_status = (
        db.query(Analise.status, func.count(Analise.id))
        .filter(Analise.created_at >= since)
        .group_by(Analise.status)
        .all()
    )

    # Daily count
    daily = (
        db.query(func.date(Analise.created_at), func.count(Analise.id))
        .filter(Analise.created_at >= since)
        .group_by(func.date(Analise.created_at))
        .order_by(func.date(Analise.created_at))
        .all()
    )

    # AI usage stats
    ai_total_tokens = (
        db.query(
            func.sum(AILog.tokens_input),
            func.sum(AILog.tokens_output),
            func.sum(AILog.custo_estimado),
        )
        .filter(AILog.created_at >= since)
        .first()
    )

    return {
        "period_days": days,
        "total_analyses": total or 0,
        "by_area": {area: count for area, count in by_area},
        "by_tipo_decisao": {tipo: count for tipo, count in by_tipo if tipo},
        "by_user": {nome: count for nome, count in by_user},
        "by_status": {status: count for status, count in by_status},
        "daily": [{"date": str(d), "count": c} for d, c in daily],
        "ai_usage": {
            "total_tokens_input": ai_total_tokens[0] or 0,
            "total_tokens_output": ai_total_tokens[1] or 0,
            "total_cost": float(ai_total_tokens[2] or 0),
        },
    }
