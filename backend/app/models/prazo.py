"""Prazo (deadline) model."""

from datetime import date
from typing import Optional

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Prazo(Base):
    __tablename__ = "prazos"

    id: Mapped[int] = mapped_column(primary_key=True)
    analise_id: Mapped[int] = mapped_column(ForeignKey("analises.id", ondelete="CASCADE"))
    tipo: Mapped[Optional[str]] = mapped_column(String(80))
    descricao: Mapped[Optional[str]] = mapped_column(Text)
    data_d_menos: Mapped[Optional[date]] = mapped_column(Date)
    data_fatal: Mapped[Optional[date]] = mapped_column(Date)
    obs: Mapped[Optional[str]] = mapped_column(Text)

    analise = relationship("Analise", back_populates="prazos")
