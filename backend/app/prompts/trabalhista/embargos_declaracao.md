# ANÁLISE DE VIABILIDADE DE EMBARGOS DE DECLARAÇÃO — TRABALHISTA

## OBJETIVO

Analisar a decisão judicial sob a ótica do polo do cliente para identificar a viabilidade de Embargos de Declaração (ED), conforme o Art. 897-A da CLT e, subsidiariamente, o Art. 1.022 do CPC.

## VÍCIOS A IDENTIFICAR

Foque EXCLUSIVAMENTE em identificar:

### 1. Omissão (Art. 897-A, CLT)
- A decisão deixou de analisar argumentos relevantes de defesa?
- Há preliminares, prejudiciais ou teses jurídicas importantes que não foram apreciadas?
- Algum pedido ou impugnação específica ficou sem resposta?
- Detalhe QUAL argumento foi omitido e ONDE ele estava nas peças (contestação, razões finais, etc.)

### 2. Contradição (Art. 897-A, CLT)
- Há conflitos lógicos dentro da própria decisão (fundamentação vs. dispositivo)?
- A decisão se contradiz entre partes da fundamentação?
- Há contradição entre a decisão e as provas (laudo pericial, documentos)?
- Especifique a contradição referenciando os trechos pertinentes

### 3. Obscuridade (Art. 897-A, CLT)
- Trechos confusos ou ambíguos que dificultam a compreensão?
- Falta de justificativa clara para rejeição de argumentos específicos?
- Linguagem que não permite compreender os motivos da decisão

### 4. Erro Material (Art. 897-A, CLT)
- Erros de digitação, cálculo, nomes, datas
- Referências incorretas a leis, CCTs, documentos
- Erros em valores de condenação ou verbas trabalhistas

### 5. Manifesto Equívoco no Exame dos Pressupostos Extrínsecos (Art. 897-A, §2º, CLT)
- Se a decisão for acórdão que julgou recurso: houve erro claro na análise de tempestividade, representação ou preparo?

## REGRAS IMPORTANTES

- **NÃO REAVALIE O MÉRITO** — foque nos vícios formais
- **CITE TRECHOS** — para cada vício, referencie o trecho exato da decisão
- **COMPARE COM AS PEÇAS** — quando alegar omissão, indique onde o argumento omitido estava nas peças do cliente
- **SEJA CONSERVADOR** — só indique ED quando houver fundamento sólido

## FORMATO DE RESPOSTA

```json
{
  "analise_ed": {
    "viabilidade_geral": "cabivel | nao_cabivel | parcialmente_cabivel",
    "confianca": 0.0,
    "resumo": "string (2-3 frases sobre a viabilidade)",
    "pontos_analisados": [
      {
        "ponto_decisao": "string (trecho ou tema da decisão)",
        "vicio_identificado": "omissao | contradicao | obscuridade | erro_material | equivoco_pressupostos | nenhum",
        "fundamentacao": "string (explicação detalhada)",
        "trecho_decisao": "string (citação do trecho relevante)",
        "trecho_peca_cliente": "string (citação da peça do cliente, se aplicável)",
        "gravidade": "alta | media | baixa",
        "recomendacao": "embargar | nao_embargar"
      }
    ],
    "pontos_sem_vicio": [
      {
        "ponto_decisao": "string",
        "motivo": "string (por que não há vício)"
      }
    ],
    "sugestao_final": "string (recomendação consolidada)"
  }
}
```
