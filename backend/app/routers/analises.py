"""CRUD router for análises."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.analise import Analise
from app.models.pedido import Pedido
from app.models.prazo import Prazo
from app.models.usuario import Usuario
from app.routers.auth import get_current_user
from app.schemas.analise import (
    AnaliseCreate,
    AnaliseListItem,
    AnaliseOut,
    AnaliseUpdate,
)

router = APIRouter(prefix="/api/analises", tags=["analises"])


@router.get("", response_model=list[AnaliseListItem])
def list_analises(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    area: str | None = None,
    status: str | None = None,
    user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(Analise).filter(Analise.usuario_id == user.id)
    if area:
        q = q.filter(Analise.area == area)
    if status:
        q = q.filter(Analise.status == status)
    q = q.order_by(Analise.created_at.desc()).offset(skip).limit(limit)
    return [AnaliseListItem.model_validate(a) for a in q.all()]


@router.post("", response_model=AnaliseOut, status_code=201)
def create_analise(
    body: AnaliseCreate,
    user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    analise = Analise(usuario_id=user.id, **body.model_dump())
    db.add(analise)
    db.commit()
    db.refresh(analise)
    return AnaliseOut.model_validate(analise)


@router.get("/{analise_id}", response_model=AnaliseOut)
def get_analise(
    analise_id: int,
    user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    analise = db.query(Analise).filter(
        Analise.id == analise_id, Analise.usuario_id == user.id
    ).first()
    if not analise:
        raise HTTPException(status_code=404, detail="Análise não encontrada")
    return AnaliseOut.model_validate(analise)


@router.patch("/{analise_id}", response_model=AnaliseOut)
def update_analise(
    analise_id: int,
    body: AnaliseUpdate,
    user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    analise = db.query(Analise).filter(
        Analise.id == analise_id, Analise.usuario_id == user.id
    ).first()
    if not analise:
        raise HTTPException(status_code=404, detail="Análise não encontrada")

    update_data = body.model_dump(exclude_unset=True)

    # Handle nested pedidos
    pedidos_data = update_data.pop("pedidos", None)
    if pedidos_data is not None:
        db.query(Pedido).filter(Pedido.analise_id == analise_id).delete()
        for p in pedidos_data:
            db.add(Pedido(analise_id=analise_id, **p))

    # Handle nested prazos
    prazos_data = update_data.pop("prazos", None)
    if prazos_data is not None:
        db.query(Prazo).filter(Prazo.analise_id == analise_id).delete()
        for p in prazos_data:
            db.add(Prazo(analise_id=analise_id, **p))

    for key, value in update_data.items():
        setattr(analise, key, value)

    db.commit()
    db.refresh(analise)
    return AnaliseOut.model_validate(analise)


@router.delete("/{analise_id}", status_code=204)
def delete_analise(
    analise_id: int,
    user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    analise = db.query(Analise).filter(
        Analise.id == analise_id, Analise.usuario_id == user.id
    ).first()
    if not analise:
        raise HTTPException(status_code=404, detail="Análise não encontrada")
    db.delete(analise)
    db.commit()
