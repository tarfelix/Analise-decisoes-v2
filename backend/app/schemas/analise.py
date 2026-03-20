"""Analysis request/response schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class PedidoOut(BaseModel):
    id: int
    objeto: Optional[str] = None
    situacao: Optional[str] = None
    res1: Optional[str] = None
    res2: Optional[str] = None
    res_sup: Optional[str] = None
    confirmado_advogado: bool = False

    model_config = {"from_attributes": True}


class PedidoCreate(BaseModel):
    objeto: Optional[str] = None
    situacao: Optional[str] = None
    res1: Optional[str] = None
    res2: Optional[str] = None
    res_sup: Optional[str] = None
    confirmado_advogado: bool = False


class PrazoOut(BaseModel):
    id: int
    tipo: Optional[str] = None
    descricao: Optional[str] = None
    data_d_menos: Optional[date] = None
    data_fatal: Optional[date] = None
    obs: Optional[str] = None

    model_config = {"from_attributes": True}


class PrazoCreate(BaseModel):
    tipo: Optional[str] = None
    descricao: Optional[str] = None
    data_d_menos: Optional[date] = None
    data_fatal: Optional[date] = None
    obs: Optional[str] = None


class AnaliseCreate(BaseModel):
    area: str
    fase_processual: Optional[str] = None
    data_ciencia: Optional[date] = None
    papel_cliente: Optional[str] = None
    tipo_decisao: Optional[str] = None
    numero_processo: Optional[str] = None
    cliente: Optional[str] = None
    adverso: Optional[str] = None
    local_vara: Optional[str] = None


class AnaliseUpdate(BaseModel):
    area: Optional[str] = None
    fase_processual: Optional[str] = None
    data_ciencia: Optional[date] = None
    papel_cliente: Optional[str] = None
    tipo_decisao: Optional[str] = None
    numero_processo: Optional[str] = None
    cliente: Optional[str] = None
    adverso: Optional[str] = None
    local_vara: Optional[str] = None
    resultado_sentenca: Optional[str] = None
    valor_condenacao: Optional[Decimal] = None
    obs_decisao: Optional[str] = None
    sintese_recurso: Optional[str] = None
    prazo_pagamento_dias: Optional[int] = None
    opcao_art_916: Optional[str] = None
    calc_principal: Optional[Decimal] = None
    calc_inss_emp: Optional[Decimal] = None
    calc_fgts: Optional[Decimal] = None
    calc_hon_suc: Optional[Decimal] = None
    calc_hon_per: Optional[Decimal] = None
    calc_total: Optional[Decimal] = None
    dep_anterior_valor: Optional[Decimal] = None
    dep_anterior_detalhes: Optional[str] = None
    ed_status: Optional[str] = None
    ed_justificativa: Optional[str] = None
    ed_analise_ia: Optional[dict] = None
    recurso_tipo: Optional[str] = None
    recurso_justificativa: Optional[str] = None
    garantia_necessaria: Optional[bool] = None
    status_custas: Optional[str] = None
    valor_custas: Optional[Decimal] = None
    status_deposito: Optional[str] = None
    valor_deposito: Optional[Decimal] = None
    guias_status: Optional[str] = None
    local_guias: Optional[str] = None
    email_assunto: Optional[str] = None
    email_corpo: Optional[str] = None
    obs_finais: Optional[str] = None
    status: Optional[str] = None
    campos_confirmados: Optional[list] = None
    dossie_pasta: Optional[str] = None
    pedidos: Optional[list[PedidoCreate]] = None
    prazos: Optional[list[PrazoCreate]] = None


class AnaliseOut(BaseModel):
    id: int
    usuario_id: int
    area: str
    fase_processual: Optional[str] = None
    data_ciencia: Optional[date] = None
    papel_cliente: Optional[str] = None
    tipo_decisao: Optional[str] = None
    numero_processo: Optional[str] = None
    cliente: Optional[str] = None
    adverso: Optional[str] = None
    local_vara: Optional[str] = None
    resultado_sentenca: Optional[str] = None
    valor_condenacao: Optional[Decimal] = None
    obs_decisao: Optional[str] = None
    sintese_recurso: Optional[str] = None
    ed_status: Optional[str] = None
    ed_analise_ia: Optional[dict] = None
    recurso_tipo: Optional[str] = None
    email_assunto: Optional[str] = None
    email_corpo: Optional[str] = None
    obs_finais: Optional[str] = None
    status: str
    campos_confirmados: Optional[list] = None
    ai_confidence_score: Optional[Decimal] = None
    dossie_pasta: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    pedidos: list[PedidoOut] = []
    prazos: list[PrazoOut] = []

    model_config = {"from_attributes": True}


class AnaliseListItem(BaseModel):
    id: int
    area: str
    tipo_decisao: Optional[str] = None
    numero_processo: Optional[str] = None
    cliente: Optional[str] = None
    adverso: Optional[str] = None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
