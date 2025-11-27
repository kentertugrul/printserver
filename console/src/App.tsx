import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import JobDetail from './pages/JobDetail'
import TemplateEditor from './pages/TemplateEditor'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<Dashboard />} />
        <Route path="/job/:jobId" element={<JobDetail />} />
        <Route path="/template/:templateId/edit" element={<TemplateEditor />} />
      </Routes>
    </BrowserRouter>
  )
}

