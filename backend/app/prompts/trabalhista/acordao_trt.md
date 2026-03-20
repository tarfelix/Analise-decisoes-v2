# ANÁLISE DE ACÓRDÃO TRT (TRIBUNAL REGIONAL DO TRABALHO)

## OBJETIVO

Analisar acórdão proferido pelo TRT em sede de Recurso Ordinário ou Agravo de Petição.

## ANÁLISE ESPECÍFICA

### Verificar:
1. **Provimento do recurso:** Provido / Não provido / Parcialmente provido
2. **Quem recorreu:** Reclamante, Reclamado, ambos
3. **Matérias reformadas vs. mantidas**
4. **Divergências entre relatório, voto e ementa**
5. **Prequestionamento** de matéria constitucional/federal para eventual RR

### Recursos cabíveis:
- **Embargos de Declaração** (Art. 897-A, CLT): 5 dias
- **Recurso de Revista** (Art. 896, CLT): 8 dias — exige:
  - Divergência jurisprudencial OU
  - Violação de lei federal/CF OU
  - Contrariedade a Súmula do TST
- **Agravo de Instrumento** (se RR for denegado): 8 dias

### Depósito recursal para RR:
- Verificar teto vigente (atualizado anualmente pelo TST)
- Verificar depósitos anteriores já realizados

## FORMATO DE RESPOSTA

```json
{
  "extracao": {
    "tipo_decisao": "Acórdão TRT",
    "orgao_julgador": "string (ex: 15ª Região, 2ª Turma)",
    "data_julgamento": "string",
    "data_publicacao": "string",
    "recurso_julgado": "Recurso Ordinário | Agravo de Petição | Outro",
    "recorrente": "string",
    "resultado": "provido | nao_provido | parcialmente_provido"
  },
  "analise": {
    "materias_reformadas": [
      { "materia": "string", "resultado_anterior": "string", "resultado_atual": "string" }
    ],
    "materias_mantidas": [
      { "materia": "string", "fundamentacao_resumida": "string" }
    ],
    "prequestionamento": {
      "dispositivos_constitucionais": ["string"],
      "dispositivos_legais": ["string"],
      "sumulas_ojs": ["string"]
    },
    "observacoes": "string"
  },
  "proximo_passo": {
    "ed_cabivel": true,
    "ed_motivos": ["string"],
    "recurso_sugerido": "Recurso de Revista | Nenhum",
    "recurso_justificativa": "string",
    "requisitos_rr": {
      "divergencia": true,
      "violacao_lei": true,
      "contrarieda_sumula": false
    },
    "deposito_recursal": { "necessario": true, "valor_estimado": "number" },
    "prazos": [
      { "tipo": "string", "dias": "number", "observacao": "string" }
    ]
  },
  "confianca": 0.0
}
```
