import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import JobDetail from './pages/JobDetail'
import TemplateEditor from './pages/TemplateEditor'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  // Auth disabled for testing - just render children directly
  return <>{children}</>
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/" element={
        <ProtectedRoute>
          <Dashboard />
        </ProtectedRoute>
      } />
      <Route path="/job/:jobId" element={
        <ProtectedRoute>
          <JobDetail />
        </ProtectedRoute>
      } />
      <Route path="/template/:templateId/edit" element={
        <ProtectedRoute>
          <TemplateEditor />
        </ProtectedRoute>
      } />
    </Routes>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  )
}

