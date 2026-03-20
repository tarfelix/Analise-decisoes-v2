# ANÁLISE DE SENTENÇA TRABALHISTA

## OBJETIVO

Analisar sentença proferida por Vara do Trabalho, identificando:
1. Resultado geral e por pedido
2. Valores de condenação
3. Viabilidade de Embargos de Declaração
4. Sugestão de recurso (Recurso Ordinário)
5. Prazos aplicáveis

## ANÁLISE ESPECÍFICA

### Para cada pedido da inicial:
- Resultado: Deferido / Indeferido / Parcialmente Deferido
- Fundamentação resumida do juiz
- Pontos favoráveis e desfavoráveis ao cliente

### Custas e depósito recursal:
- Valor das custas processuais
- Necessidade e valor do depósito recursal (verificar teto TST vigente)
- Isenções aplicáveis (ex: beneficiário da justiça gratuita)

### Recursos cabíveis:
- **Embargos de Declaração** (Art. 897-A, CLT): 5 dias
- **Recurso Ordinário** (Art. 895, CLT): 8 dias
- Ambos podem ser cabíveis simultaneamente

## FORMATO DE RESPOSTA

```json
{
  "extracao": {
    "tipo_decisao": "Sentença",
    "orgao_julgador": "string",
    "data_decisao": "string",
    "resultado_geral": "favoravel | desfavoravel | parcialmente_favoravel",
    "valor_condenacao_total": "number ou null",
    "custas": { "valor": "number", "responsavel": "string" },
    "honorarios": { "percentual": "number", "beneficiario": "string" }
  },
  "analise": {
    "pedidos": [
      {
        "descricao": "string",
        "resultado": "deferido | indeferido | parcialmente_deferido",
        "valor": "number ou null",
        "fundamentacao": "string",
        "favorabilidade": "favoravel | desfavoravel"
      }
    ],
    "pontos_fortes": ["string"],
    "pontos_fracos": ["string"],
    "observacoes": "string"
  },
  "proximo_passo": {
    "ed_cabivel": true,
    "ed_motivos": ["string"],
    "recurso_sugerido": "Recurso Ordinário | Nenhum",
    "recurso_justificativa": "string",
    "deposito_recursal": { "necessario": true, "valor_estimado": "number" },
    "custas_recurso": { "valor": "number" },
    "prazos": [
      { "tipo": "string", "dias": "number", "observacao": "string" }
    ]
  },
  "confianca": 0.0
}
```
