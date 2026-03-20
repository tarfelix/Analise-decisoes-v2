export interface User {
  id: number
  email: string
  nome: string
  role: string
  first_access: boolean
}

export interface TokenResponse {
  access_token: string
  token_type: string
  user: User
}

export interface Pedido {
  id?: number
  objeto: string
  situacao: string
  res1: string
  res2: string
  res_sup: string
  confirmado_advogado: boolean
}

export interface Prazo {
  id?: number
  tipo: string
  descricao: string
  data_d_menos: string | null
  data_fatal: string | null
  obs: string
}

export interface Analise {
  id: number
  usuario_id: number
  area: string
  fase_processual: string | null
  data_ciencia: string | null
  papel_cliente: string | null
  tipo_decisao: string | null
  numero_processo: string | null
  cliente: string | null
  adverso: string | null
  local_vara: string | null
  resultado_sentenca: string | null
  valor_condenacao: number | null
  obs_decisao: string | null
  sintese_recurso: string | null
  ed_status: string | null
  ed_analise_ia: Record<string, unknown> | null
  recurso_tipo: string | null
  email_assunto: string | null
  email_corpo: string | null
  obs_finais: string | null
  status: string
  campos_confirmados: string[] | null
  ai_confidence_score: number | null
  dossie_pasta: string | null
  created_at: string
  updated_at: string
  pedidos: Pedido[]
  prazos: Prazo[]
}

export interface AnaliseListItem {
  id: number
  area: string
  tipo_decisao: string | null
  numero_processo: string | null
  cliente: string | null
  adverso: string | null
  status: string
  created_at: string
}

export interface DashboardStats {
  period_days: number
  total_analyses: number
  by_area: Record<string, number>
  by_tipo_decisao: Record<string, number>
  by_user: Record<string, number>
  by_status: Record<string, number>
  daily: Array<{ date: string; count: number }>
  ai_usage: {
    total_tokens_input: number
    total_tokens_output: number
    total_cost: number
  }
}

// Wizard step status
export type WizardStep = 1 | 2 | 3 | 4 | 5 | 6

export interface AIFieldState {
  value: unknown
  source: 'ai' | 'user' | 'system'
  confirmed: boolean
  confidence?: number
}
