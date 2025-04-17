# -*- coding: utf-8 -*-

# Placeholders Padrão
PLACEHOLDER_SELECT = "-- Selecione --"
PLACEHOLDER_RECURSO = "-- Selecione --"
PLACEHOLDER_STATUS = "-- Selecione --"

# Opções Gerais
CLIENTE_OPTIONS = ["Reclamante", "Reclamado", "Outro"]
RESULTADO_OPTIONS = [PLACEHOLDER_SELECT, "Favorável", "Desfavorável", "Parcialmente Favorável"]
ED_STATUS_OPTIONS = ["Cabe ED", "Não cabe ED"] # Radio não usa placeholder

# Opções de Tipo de Decisão por Fase
DECISAO_OPTIONS_CONHECIMENTO = [
    PLACEHOLDER_SELECT, "Sentença (Vara do Trabalho)",
    "Decisão Embargos Declaração (Sentença)", "Acórdão (TRT)",
    "Decisão Embargos Declaração (Acórdão TRT)", "Acórdão (TST - Turma)",
    "Decisão Embargos Declaração (Acórdão TST)", "Acórdão (TST - SDI)",
    "Decisão Monocrática (Relator TRT/TST)", "Despacho", "Outro"
]
DECISAO_OPTIONS_EXECUCAO = [
    PLACEHOLDER_SELECT, "Homologação de Cálculos", "Sentença de Liquidação",
    "Decisão Embargos à Execução / Impugnação", "Acórdão em Agravo de Petição (TRT)",
    "Decisão Monocrática em Execução (TRT/TST)",
    "Acórdão TST em Execução (AIRR-AP, RR)", "Despacho de Execução", "Outro"
]

# Opções de Recurso por Fase
RECURSO_OPTIONS_CONHECIMENTO = [
    PLACEHOLDER_RECURSO, "Não Interpor Recurso", "Recurso Ordinário (RO)",
    "Recurso de Revista (RR)", "Agravo de Instrumento em RO (AIRO)",
    "Agravo de Instrumento em RR (AIRR)", "Agravo Regimental / Agravo Interno",
    "Embargos de Divergência ao TST (SDI)", "Recurso Extraordinário (RE)", "Outro"
]
RECURSO_OPTIONS_EXECUCAO = [
    PLACEHOLDER_RECURSO, "Não Interpor Recurso",
    "Embargos à Execução / Impugnação à Sentença", "Agravo de Petição (AP)",
    "Agravo de Instrumento em AP (AIAP)",
    "Recurso de Revista (Execução - Art. 896 §2º CLT)",
    "Agravo de Instrumento em RR (Execução)", "Agravo Regimental / Agravo Interno",
    "Outro"
]

# Mapas para sugestão de recurso (Chave "Despacho" corrigida)
MAPA_DECISAO_RECURSO_CONHECIMENTO = {
    "Sentença (Vara do Trabalho)": 2, # RO
    "Decisão Embargos Declaração (Sentença)": 2, # RO
    "Acórdão (TRT)": 3, # RR
    "Decisão Embargos Declaração (Acórdão TRT)": 3, # RR
    "Acórdão (TST - Turma)": 7, # Embargos SDI
    "Decisão Embargos Declaração (Acórdão TST)": 7, # Embargos SDI
    "Acórdão (TST - SDI)": 8, # RE
    "Decisão Monocrática (Relator TRT/TST)": 6, # Agravo Regimental
    "Despacho": 1, # Não Interpor (Default para Despacho genérico)
    "Outro": 1
}
MAPA_DECISAO_RECURSO_EXECUCAO = {
    "Homologação de Cálculos": 2, # Embargos à Execução
    "Sentença de Liquidação": 2, # Embargos à Execução
    "Decisão Embargos à Execução / Impugnação": 3, # AP
    "Acórdão em Agravo de Petição (TRT)": 5, # RR Exec
    "Decisão Monocrática em Execução (TRT/TST)": 7, # Agravo Regimental
    "Acórdão TST em Execução (AIRR-AP, RR)": 1, # Não Interpor
    "Despacho de Execução": 1, # Não Interpor
    "Outro": 1
}

# Status Pagamentos
CUSTAS_OPTIONS = [PLACEHOLDER_STATUS, "A Recolher", "Isento", "Já Recolhidas", "Não se aplica"]
DEPOSITO_OPTIONS_CONHECIMENTO = [PLACEHOLDER_STATUS, "A Recolher/Complementar", "Isento", "Garantido por Depósitos Anteriores"]
DEPOSITO_OPTIONS_EXECUCAO = [PLACEHOLDER_STATUS, "Não Aplicável (Fase de Execução)", "Garantia do Juízo (Integral)", "Garantido por Depósitos Anteriores", "Isento", "A Recolher (Situação Específica)"]
DEPOSITO_DEFAULT_INDEX_EXEC = 1 # Indice de "Não Aplicável"

GUIAS_OPTIONS = ["Guias já elaboradas e salvas", "Guias pendentes de elaboração"] # Para Radio

# Prazos
TIPOS_PRAZO_COMUNS = [
    "", "Embargos de Declaração", "Recurso Ordinário", "Contrarrazões RO",
    "Recurso de Revista", "Contrarrazões RR", "Agravo de Instrumento",
    "Contraminuta AI", "Agravo de Petição", "Contraminuta AP",
    "Pagamento (Custas/Depósito/Acordo/Garantia)", "Ciência Despacho/Decisão",
    "Manifestação sobre Cálculos", "Embargos à Execução",
    "Impugnação à Sentença de Liquidação", "Manifestação Genérica",
    "Verificar Recurso Contrário", "Outro (Especificar)"
]

# Imagem Exemplo
IMAGE_PATH = "image_545e9d.png"

# Logging
LOGGING_LEVEL = "INFO" # Mudar para "DEBUG" para ver mais detalhes no terminal