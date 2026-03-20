import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { analises } from '@/services/api'
import type { AnaliseListItem } from '@/types'
import { Search, FileText } from 'lucide-react'

export default function Historico() {
  const [area, setArea] = useState<string>('')
  const [search, setSearch] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['analises', area],
    queryFn: () => analises.list({ area: area || undefined, limit: 100 }),
  })

  const filtered = (data || []).filter((a: AnaliseListItem) => {
    if (!search) return true
    const s = search.toLowerCase()
    return (
      a.numero_processo?.toLowerCase().includes(s) ||
      a.cliente?.toLowerCase().includes(s) ||
      a.adverso?.toLowerCase().includes(s) ||
      a.tipo_decisao?.toLowerCase().includes(s)
    )
  })

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Histórico de Análises</h1>

      {/* Filters */}
      <div className="flex gap-4 mb-6">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Buscar por processo, cliente, adverso..."
            className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 outline-none"
          />
        </div>
        <select
          value={area}
          onChange={(e) => setArea(e.target.value)}
          className="px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 outline-none"
        >
          <option value="">Todas as áreas</option>
          <option value="trabalhista">Trabalhista</option>
          <option value="civel">Cível</option>
          <option value="empresarial">Empresarial</option>
        </select>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        {isLoading ? (
          <div className="p-8 text-center text-gray-400">Carregando...</div>
        ) : filtered.length === 0 ? (
          <div className="p-8 text-center text-gray-400">
            <FileText className="h-12 w-12 mx-auto mb-3 opacity-30" />
            <p>Nenhuma análise encontrada</p>
          </div>
        ) : (
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Processo</th>
                <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Área</th>
                <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Tipo</th>
                <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Partes</th>
                <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Data</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {filtered.map((a: AnaliseListItem) => (
                <tr key={a.id} className="hover:bg-gray-50 cursor-pointer transition-colors">
                  <td className="px-6 py-4 text-sm font-mono">{a.numero_processo || '—'}</td>
                  <td className="px-6 py-4">
                    <span className="px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-800 capitalize">
                      {a.area}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-600">{a.tipo_decisao || '—'}</td>
                  <td className="px-6 py-4 text-sm">
                    <div>{a.cliente || '—'}</div>
                    <div className="text-gray-400">vs {a.adverso || '—'}</div>
                  </td>
                  <td className="px-6 py-4">
                    <span
                      className={`px-2 py-1 text-xs rounded-full ${
                        a.status === 'finalizada'
                          ? 'bg-green-100 text-green-800'
                          : 'bg-yellow-100 text-yellow-800'
                      }`}
                    >
                      {a.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {new Date(a.created_at).toLocaleDateString('pt-BR')}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
