import { useQuery } from '@tanstack/react-query'
import { dashboard } from '@/services/api'
import { BarChart3, FileText, Brain, TrendingUp } from 'lucide-react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts'

const COLORS = ['#1E3A8A', '#3B82F6', '#60A5FA', '#93C5FD', '#BFDBFE']

export default function Dashboard() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: () => dashboard.stats(30),
  })

  if (isLoading || !stats) {
    return <div className="text-center text-gray-400 py-12">Carregando dashboard...</div>
  }

  const areaData = Object.entries(stats.by_area).map(([name, value]) => ({
    name: name.charAt(0).toUpperCase() + name.slice(1),
    value,
  }))

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Dashboard</h1>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <KPICard
          icon={FileText}
          label="Total de Análises"
          value={stats.total_analyses}
          subtitle="últimos 30 dias"
        />
        <KPICard
          icon={BarChart3}
          label="Por Dia (média)"
          value={Math.round(stats.total_analyses / 30)}
          subtitle="média diária"
        />
        <KPICard
          icon={Brain}
          label="Tokens IA"
          value={`${Math.round((stats.ai_usage.total_tokens_input + stats.ai_usage.total_tokens_output) / 1000)}K`}
          subtitle="consumo total"
        />
        <KPICard
          icon={TrendingUp}
          label="Custo IA"
          value={`US$ ${stats.ai_usage.total_cost.toFixed(2)}`}
          subtitle="últimos 30 dias"
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Daily chart */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Análises por Dia</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={stats.daily}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="date"
                tickFormatter={(d) => new Date(d).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' })}
              />
              <YAxis />
              <Tooltip />
              <Bar dataKey="count" fill="#1E3A8A" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Area pie chart */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Por Área do Direito</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={areaData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={120}
                paddingAngle={5}
                dataKey="value"
                label={({ name, value }) => `${name}: ${value}`}
              >
                {areaData.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* By user */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Por Advogado</h3>
          <div className="space-y-3">
            {Object.entries(stats.by_user)
              .sort(([, a], [, b]) => b - a)
              .map(([name, count]) => (
                <div key={name} className="flex items-center justify-between">
                  <span className="text-sm text-gray-700">{name}</span>
                  <div className="flex items-center gap-2">
                    <div className="w-32 bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-primary-600 rounded-full h-2"
                        style={{ width: `${(count / stats.total_analyses) * 100}%` }}
                      />
                    </div>
                    <span className="text-sm font-medium text-gray-900 w-8 text-right">{count}</span>
                  </div>
                </div>
              ))}
          </div>
        </div>

        {/* By decision type */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Por Tipo de Decisão</h3>
          <div className="space-y-3">
            {Object.entries(stats.by_tipo_decisao)
              .sort(([, a], [, b]) => b - a)
              .map(([tipo, count]) => (
                <div key={tipo} className="flex items-center justify-between">
                  <span className="text-sm text-gray-700">{tipo}</span>
                  <span className="px-2 py-1 text-xs bg-gray-100 rounded-full">{count}</span>
                </div>
              ))}
          </div>
        </div>
      </div>
    </div>
  )
}

function KPICard({
  icon: Icon,
  label,
  value,
  subtitle,
}: {
  icon: React.ElementType
  label: string
  value: string | number
  subtitle: string
}) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <div className="flex items-center gap-3 mb-3">
        <div className="p-2 bg-primary-50 rounded-lg">
          <Icon className="h-5 w-5 text-primary-600" />
        </div>
        <span className="text-sm text-gray-500">{label}</span>
      </div>
      <div className="text-3xl font-bold text-gray-900">{value}</div>
      <div className="text-xs text-gray-400 mt-1">{subtitle}</div>
    </div>
  )
}
