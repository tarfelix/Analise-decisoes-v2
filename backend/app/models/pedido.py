"""Pedido (claim/request) model."""

from typing import Optional

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Pedido(Base):
    __tablename__ = "pedidos"

    id: Mapped[int] = mapped_column(primary_key=True)
    analise_id: Mapped[int] = mapped_column(ForeignKey("analises.id", ondelete="CASCADE"))
    objeto: Mapped[Optional[str]] = mapped_column(Text)
    situacao: Mapped[Optional[str]] = mapped_column(String(50))
    res1: Mapped[Optional[str]] = mapped_column(String(100))
    res2: Mapped[Optional[str]] = mapped_column(String(100))
    res_sup: Mapped[Optional[str]] = mapped_column(String(100))
    confirmado_advogado: Mapped[bool] = mapped_column(Boolean, default=False)

    analise = relationship("Analise", back_populates="pedidos")
