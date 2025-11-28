import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import JobDetail from './pages/JobDetail'
import TemplateEditor from './pages/TemplateEditor'
import TemplateList from './pages/TemplateList'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<Dashboard />} />
        <Route path="/job/:jobId" element={<JobDetail />} />
        <Route path="/templates" element={<TemplateList />} />
        <Route path="/template/new" element={<TemplateEditor />} />
        <Route path="/template/:templateId/edit" element={<TemplateEditor />} />
      </Routes>
    </BrowserRouter>
  )
}

