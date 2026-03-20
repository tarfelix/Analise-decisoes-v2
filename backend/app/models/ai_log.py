"""AI call log for cost tracking and auditing."""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AILog(Base):
    __tablename__ = "ai_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    analise_id: Mapped[Optional[int]] = mapped_column(ForeignKey("analises.id"))
    etapa: Mapped[str] = mapped_column(String(50))
    prompt_name: Mapped[Optional[str]] = mapped_column(String(100))
    modelo: Mapped[Optional[str]] = mapped_column(String(50))
    tokens_input: Mapped[Optional[int]] = mapped_column(Integer)
    tokens_output: Mapped[Optional[int]] = mapped_column(Integer)
    custo_estimado: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 4))
    duracao_ms: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    analise = relationship("Analise", back_populates="ai_logs")
