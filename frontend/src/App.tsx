import { Routes, Route, Navigate } from 'react-router-dom'
import { AppShell } from './components/layout/AppShell'
import { ProtectedRoute } from './components/layout/ProtectedRoute'
import { LoginPage } from './pages/LoginPage'
import { DashboardPage } from './pages/DashboardPage'
import { AnalyzePage } from './pages/AnalyzePage'
import { ApprovalListPage } from './pages/ApprovalListPage'
import { ApprovalDetailPage } from './pages/ApprovalDetailPage'
import { AdminPage } from './pages/AdminPage'

export function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />

      <Route
        element={
          <ProtectedRoute>
            <AppShell />
          </ProtectedRoute>
        }
      >
        <Route index element={<DashboardPage />} />
        <Route path="analyze" element={<AnalyzePage />} />
        <Route path="approval" element={<ApprovalListPage />} />
        <Route path="approval/:id" element={<ApprovalDetailPage />} />
        <Route
          path="admin"
          element={
            <ProtectedRoute minRole="admin">
              <AdminPage />
            </ProtectedRoute>
          }
        />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
