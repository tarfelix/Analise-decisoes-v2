import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from '@/stores/auth'
import Layout from '@/components/layout/Layout'
import Login from '@/pages/Login'
import NovaAnalise from '@/pages/NovaAnalise'
import Historico from '@/pages/Historico'
import Dashboard from '@/pages/Dashboard'

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const isAuth = useAuthStore((s) => s.isAuthenticated())
  if (!isAuth) return <Navigate to="/login" replace />
  return <>{children}</>
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/*"
        element={
          <PrivateRoute>
            <Layout>
              <Routes>
                <Route path="/" element={<Navigate to="/nova" replace />} />
                <Route path="/nova" element={<NovaAnalise />} />
                <Route path="/historico" element={<Historico />} />
                <Route path="/dashboard" element={<Dashboard />} />
              </Routes>
            </Layout>
          </PrivateRoute>
        }
      />
    </Routes>
  )
}
