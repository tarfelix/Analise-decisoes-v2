import { Link, useLocation } from 'react-router-dom'
import { useAuthStore } from '@/stores/auth'
import { FileText, History, BarChart3, LogOut, PlusCircle } from 'lucide-react'

const navItems = [
  { to: '/nova', label: 'Nova Análise', icon: PlusCircle },
  { to: '/historico', label: 'Histórico', icon: History },
  { to: '/dashboard', label: 'Dashboard', icon: BarChart3 },
]

export default function Layout({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuthStore()
  const location = useLocation()

  return (
    <div className="min-h-screen flex">
      {/* Sidebar */}
      <aside className="w-64 bg-primary-600 text-white flex flex-col">
        <div className="p-6">
          <div className="flex items-center gap-2">
            <FileText className="h-6 w-6" />
            <h1 className="text-lg font-bold">Análise de Decisões</h1>
          </div>
          <p className="text-xs text-blue-200 mt-1">Soares & Picon</p>
        </div>

        <nav className="flex-1 px-3">
          {navItems.map((item) => {
            const isActive = location.pathname === item.to
            return (
              <Link
                key={item.to}
                to={item.to}
                className={`flex items-center gap-3 px-4 py-3 rounded-lg mb-1 transition-colors ${
                  isActive
                    ? 'bg-white/20 text-white font-medium'
                    : 'text-blue-200 hover:bg-white/10 hover:text-white'
                }`}
              >
                <item.icon className="h-5 w-5" />
                {item.label}
              </Link>
            )
          })}
        </nav>

        <div className="p-4 border-t border-white/20">
          <div className="text-sm text-blue-200">{user?.nome}</div>
          <div className="text-xs text-blue-300">{user?.role}</div>
          <button
            onClick={logout}
            className="mt-3 flex items-center gap-2 text-sm text-blue-300 hover:text-white transition-colors"
          >
            <LogOut className="h-4 w-4" />
            Sair
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto">
        <div className="p-8">{children}</div>
      </main>
    </div>
  )
}
