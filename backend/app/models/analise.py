"""Central analysis model — stores the full decision analysis."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Analise(Base):
    __tablename__ = "analises"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))

    # Contexto
    area: Mapped[str] = mapped_column(String(30), nullable=False)
    fase_processual: Mapped[Optional[str]] = mapped_column(String(30))
    data_ciencia: Mapped[Optional[date]] = mapped_column(Date)
    papel_cliente: Mapped[Optional[str]] = mapped_column(String(30))
    tipo_decisao: Mapped[Optional[str]] = mapped_column(String(80))
    numero_processo: Mapped[Optional[str]] = mapped_column(String(30))
    cliente: Mapped[Optional[str]] = mapped_column(String(200))
    adverso: Mapped[Optional[str]] = mapped_column(String(200))
    local_vara: Mapped[Optional[str]] = mapped_column(String(200))

    # Análise
    resultado_sentenca: Mapped[Optional[str]] = mapped_column(String(50))
    valor_condenacao: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    obs_decisao: Mapped[Optional[str]] = mapped_column(Text)
    sintese_recurso: Mapped[Optional[str]] = mapped_column(Text)

    # Execução
    prazo_pagamento_dias: Mapped[Optional[int]] = mapped_column(Integer)
    opcao_art_916: Mapped[Optional[str]] = mapped_column(String(50))
    calc_principal: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    calc_inss_emp: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    calc_fgts: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    calc_hon_suc: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    calc_hon_per: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    calc_total: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    dep_anterior_valor: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    dep_anterior_detalhes: Mapped[Optional[str]] = mapped_column(Text)

    # ED / Recurso
    ed_status: Mapped[Optional[str]] = mapped_column(String(30))
    ed_justificativa: Mapped[Optional[str]] = mapped_column(Text)
    ed_analise_ia: Mapped[Optional[dict]] = mapped_column(JSONB)
    recurso_tipo: Mapped[Optional[str]] = mapped_column(String(80))
    recurso_justificativa: Mapped[Optional[str]] = mapped_column(Text)
    garantia_necessaria: Mapped[bool] = mapped_column(Boolean, default=False)
    status_custas: Mapped[Optional[str]] = mapped_column(String(50))
    valor_custas: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    status_deposito: Mapped[Optional[str]] = mapped_column(String(50))
    valor_deposito: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    guias_status: Mapped[Optional[str]] = mapped_column(String(30))
    local_guias: Mapped[Optional[str]] = mapped_column(Text)

    # Email
    email_assunto: Mapped[Optional[str]] = mapped_column(Text)
    email_corpo: Mapped[Optional[str]] = mapped_column(Text)

    # Meta
    obs_finais: Mapped[Optional[str]] = mapped_column(Text)
    pdf_path: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="rascunho")
    campos_confirmados: Mapped[Optional[list]] = mapped_column(JSONB, default=[])
    ai_confidence_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    dossie_pasta: Mapped[Optional[str]] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    pedidos = relationship("Pedido", back_populates="analise", cascade="all, delete-orphan")
    prazos = relationship("Prazo", back_populates="analise", cascade="all, delete-orphan")
    ai_logs = relationship("AILog", back_populates="analise")
