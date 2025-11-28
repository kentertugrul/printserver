import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import api from '../lib/api'
import {
  Plus,
  Upload,
  Grid3X3,
  ArrowLeft,
  FileText,
  Edit,
  X
} from 'lucide-react'

interface Template {
  id: string
  name: string
  description?: string
  bed_width: number
  bed_height: number
  template_pdf_path?: string
  created_at: string
}

export default function TemplateList() {
  const [showUploadModal, setShowUploadModal] = useState(false)
  const [uploadFile, setUploadFile] = useState<File | null>(null)
  const [newTemplate, setNewTemplate] = useState({
    id: '',
    name: '',
    description: '',
    bed_width: 210,
    bed_height: 297,
    hot_folder_type: 'default'
  })

  const queryClient = useQueryClient()

  // Fetch templates
  const { data: templates, isLoading } = useQuery({
    queryKey: ['templates'],
    queryFn: async () => {
      const response = await api.get('/api/templates/')
      return response.data as Template[]
    }
  })

  // Create template mutation
  const createTemplate = useMutation({
    mutationFn: async (data: typeof newTemplate) => {
      console.log('Creating template:', data)
      const response = await api.post('/api/templates/', data)
      console.log('Template created:', response.data)
      return response.data
    },
    onSuccess: (createdTemplate) => {
      console.log('Success! Template:', createdTemplate)
      queryClient.invalidateQueries({ queryKey: ['templates'] })
      // For now, skip PDF upload - just close modal
      setShowUploadModal(false)
      resetForm()
      alert('Template created: ' + createdTemplate.id)
    },
    onError: (error: any) => {
      console.error('Error creating template:', error)
      alert('Error: ' + (error.response?.data?.detail || error.message))
    }
  })

  // Upload jig PDF mutation
  const uploadJigPdfMutation = useMutation({
    mutationFn: async ({ templateId, file }: { templateId: string; file: File }) => {
      const formData = new FormData()
      formData.append('file', file)
      const response = await api.post(`/api/templates/editor/${templateId}/upload-jig`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] })
      setShowUploadModal(false)
      resetForm()
    }
  })

  const uploadJigPdf = (templateId: string) => {
    if (uploadFile) {
      uploadJigPdfMutation.mutate({ templateId, file: uploadFile })
    }
  }

  const resetForm = () => {
    setNewTemplate({ id: '', name: '', description: '', bed_width: 210, bed_height: 297, hot_folder_type: 'default' })
    setUploadFile(null)
  }

  // Generate ID from name
  const generateId = (name: string) => {
    return name.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '')
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const templateData = {
      ...newTemplate,
      id: newTemplate.id || generateId(newTemplate.name)
    }
    createTemplate.mutate(templateData)
  }

  return (
    <div className="min-h-screen bg-midnight-950">
      {/* Header */}
      <header className="sticky top-0 z-50 glass border-b border-midnight-700/50">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link to="/" className="p-2 rounded-lg hover:bg-midnight-800 text-midnight-400 hover:text-white transition-colors">
                <ArrowLeft className="w-5 h-5" />
              </Link>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-scentcraft-500 to-scentcraft-700 flex items-center justify-center">
                  <Grid3X3 className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h1 className="font-display text-xl font-semibold text-white">Jig Templates</h1>
                  <p className="text-xs text-midnight-400">Manage print layouts</p>
                </div>
              </div>
            </div>

            <button
              onClick={() => setShowUploadModal(true)}
              className="btn-primary flex items-center gap-2"
            >
              <Plus className="w-4 h-4" />
              New Template
            </button>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {isLoading ? (
          <div className="flex items-center justify-center py-20">
            <div className="w-8 h-8 border-2 border-scentcraft-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : templates?.length === 0 ? (
          <div className="card text-center py-16">
            <div className="w-16 h-16 rounded-2xl bg-midnight-800 flex items-center justify-center mx-auto mb-4">
              <Grid3X3 className="w-8 h-8 text-midnight-400" />
            </div>
            <h2 className="text-xl font-semibold text-white mb-2">No Templates Yet</h2>
            <p className="text-midnight-400 max-w-md mx-auto mb-6">
              Upload your jig PDF to create a template. Define slot positions where labels will be placed.
            </p>
            <button
              onClick={() => setShowUploadModal(true)}
              className="btn-primary inline-flex items-center gap-2"
            >
              <Upload className="w-4 h-4" />
              Upload Jig PDF
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {templates?.map(template => (
              <motion.div
                key={template.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="card group hover:border-scentcraft-500/50 transition-all"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="w-12 h-12 rounded-xl bg-midnight-800 flex items-center justify-center">
                    {template.template_pdf_path ? (
                      <FileText className="w-6 h-6 text-scentcraft-400" />
                    ) : (
                      <Grid3X3 className="w-6 h-6 text-midnight-400" />
                    )}
                  </div>
                  <div className="flex gap-2">
                    <Link
                      to={`/template/${template.id}/edit`}
                      className="p-2 rounded-lg hover:bg-midnight-700 text-midnight-400 hover:text-white transition-colors"
                    >
                      <Edit className="w-4 h-4" />
                    </Link>
                  </div>
                </div>

                <h3 className="font-semibold text-lg text-white mb-1">{template.name}</h3>
                <p className="text-midnight-400 text-sm mb-4">
                  {template.description || 'No description'}
                </p>

                <div className="flex items-center gap-4 text-sm text-midnight-500">
                  <span>{template.bed_width} × {template.bed_height} mm</span>
                  <span>•</span>
                  <span>{new Date(template.created_at).toLocaleDateString()}</span>
                </div>

                <Link
                  to={`/template/${template.id}/edit`}
                  className="mt-4 block w-full btn-secondary text-center"
                >
                  Edit Slots
                </Link>
              </motion.div>
            ))}
          </div>
        )}
      </main>

      {/* Upload Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-midnight-900 border border-midnight-700 rounded-2xl p-6 w-full max-w-md"
          >
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold text-white">New Template</h2>
              <button
                onClick={() => { setShowUploadModal(false); resetForm() }}
                className="p-2 rounded-lg hover:bg-midnight-800 text-midnight-400"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-midnight-300 mb-2">
                  Template Name *
                </label>
                <input
                  type="text"
                  required
                  value={newTemplate.name}
                  onChange={(e) => setNewTemplate({ ...newTemplate, name: e.target.value })}
                  placeholder="e.g., 3x 50ml + 2x5ml + Caps"
                  className="w-full px-4 py-2 bg-midnight-800 border border-midnight-700 rounded-lg
                           text-white placeholder-midnight-500 focus:border-scentcraft-500 outline-none"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-midnight-300 mb-2">
                  Description
                </label>
                <textarea
                  value={newTemplate.description}
                  onChange={(e) => setNewTemplate({ ...newTemplate, description: e.target.value })}
                  placeholder="Optional description..."
                  rows={2}
                  className="w-full px-4 py-2 bg-midnight-800 border border-midnight-700 rounded-lg
                           text-white placeholder-midnight-500 focus:border-scentcraft-500 outline-none resize-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-midnight-300 mb-2">
                    Bed Width (mm)
                  </label>
                  <input
                    type="number"
                    value={newTemplate.bed_width}
                    onChange={(e) => setNewTemplate({ ...newTemplate, bed_width: parseInt(e.target.value) })}
                    className="w-full px-4 py-2 bg-midnight-800 border border-midnight-700 rounded-lg
                             text-white focus:border-scentcraft-500 outline-none"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-midnight-300 mb-2">
                    Bed Height (mm)
                  </label>
                  <input
                    type="number"
                    value={newTemplate.bed_height}
                    onChange={(e) => setNewTemplate({ ...newTemplate, bed_height: parseInt(e.target.value) })}
                    className="w-full px-4 py-2 bg-midnight-800 border border-midnight-700 rounded-lg
                             text-white focus:border-scentcraft-500 outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-midnight-300 mb-2">
                  Jig PDF (optional)
                </label>
                <div className="relative">
                  <input
                    type="file"
                    accept=".pdf"
                    onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                    className="hidden"
                    id="jig-pdf-upload"
                  />
                  <label
                    htmlFor="jig-pdf-upload"
                    className="flex items-center justify-center gap-2 w-full px-4 py-3 bg-midnight-800 border border-dashed border-midnight-600 rounded-lg
                             text-midnight-400 hover:border-scentcraft-500 hover:text-scentcraft-400 cursor-pointer transition-colors"
                  >
                    <Upload className="w-5 h-5" />
                    {uploadFile ? uploadFile.name : 'Click to upload PDF'}
                  </label>
                </div>
                <p className="text-xs text-midnight-500 mt-2">
                  Upload a 2D drawing of your jig to use as a background reference
                </p>
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => { setShowUploadModal(false); resetForm() }}
                  className="flex-1 btn-secondary"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createTemplate.isPending || uploadJigPdfMutation.isPending}
                  className="flex-1 btn-primary disabled:opacity-50"
                >
                  {createTemplate.isPending || uploadJigPdfMutation.isPending ? 'Creating...' : 'Create Template'}
                </button>
              </div>
            </form>
          </motion.div>
        </div>
      )}
    </div>
  )
}

