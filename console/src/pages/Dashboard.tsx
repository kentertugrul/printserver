import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { motion, AnimatePresence } from 'framer-motion'
import { Link } from 'react-router-dom'
import api from '../lib/api'
import { 
  Printer, 
  Clock, 
  LogOut,
  RefreshCw,
  ChevronRight,
  Sparkles,
  Layers,
  Play,
  Pause,
  Grid3X3
} from 'lucide-react'
// Auth disabled for testing
// import { useAuth } from '../contexts/AuthContext'
import { Job, JobStatus } from '../types'
import clsx from 'clsx'

// Status badge component
function StatusBadge({ status }: { status: JobStatus }) {
  const config = {
    draft: { bg: 'bg-midnight-600', text: 'text-midnight-200', label: 'Draft' },
    pending_review: { bg: 'bg-amber-500/20', text: 'text-amber-400', label: 'Review' },
    ready_for_print: { bg: 'bg-blue-500/20', text: 'text-blue-400', label: 'Ready' },
    queued_local: { bg: 'bg-purple-500/20', text: 'text-purple-400', label: 'Queued' },
    awaiting_operator: { bg: 'bg-scentcraft-500/20', text: 'text-scentcraft-400', label: 'Loading' },
    sent_to_printer: { bg: 'bg-cyan-500/20', text: 'text-cyan-400', label: 'Printing' },
    printed: { bg: 'bg-emerald-500/20', text: 'text-emerald-400', label: 'Done' },
    failed: { bg: 'bg-red-500/20', text: 'text-red-400', label: 'Failed' },
  }[status]

  return (
    <span className={clsx('status-badge', config.bg, config.text)}>
      {config.label}
    </span>
  )
}

// Job card component
function JobCard({ job }: { job: Job }) {
  const isActive = job.status === 'awaiting_operator' || job.status === 'sent_to_printer'
  
  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className={clsx(
        'card group hover:border-scentcraft-500/50 transition-all cursor-pointer',
        isActive && 'ring-2 ring-scentcraft-500/50'
      )}
    >
      <Link to={`/job/${job.id}`} className="block">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h3 className="font-semibold text-lg text-white group-hover:text-scentcraft-400 transition-colors">
              {job.job_name || `Job #${job.id}`}
            </h3>
            <p className="text-midnight-400 text-sm mt-1">
              {job.event_name || 'No event'}
            </p>
          </div>
          <StatusBadge status={job.status} />
        </div>

        <div className="flex items-center gap-4 text-sm text-midnight-400">
          <div className="flex items-center gap-1.5">
            <Layers className="w-4 h-4" />
            <span>{job.slots?.length || 0} slots</span>
          </div>
          <div className="flex items-center gap-1.5">
            <Clock className="w-4 h-4" />
            <span>{new Date(job.created_at).toLocaleTimeString()}</span>
          </div>
        </div>

        <div className="flex items-center justify-end mt-4 pt-4 border-t border-midnight-700/50">
          <ChevronRight className="w-5 h-5 text-midnight-500 group-hover:text-scentcraft-400 transition-colors" />
        </div>
      </Link>
    </motion.div>
  )
}

// Queue section component
function QueueSection({ 
  title, 
  icon: Icon, 
  jobs, 
  emptyText 
}: { 
  title: string
  icon: React.ElementType
  jobs: Job[]
  emptyText: string 
}) {
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 text-midnight-300">
        <Icon className="w-5 h-5" />
        <h2 className="font-semibold">{title}</h2>
        <span className="text-midnight-500">({jobs.length})</span>
      </div>
      
      {jobs.length === 0 ? (
        <div className="card text-center py-12">
          <p className="text-midnight-500">{emptyText}</p>
        </div>
      ) : (
        <div className="space-y-3">
          <AnimatePresence>
            {jobs.map(job => (
              <JobCard key={job.id} job={job} />
            ))}
          </AnimatePresence>
        </div>
      )}
    </div>
  )
}

export default function Dashboard() {
  const [selectedPrinter, setSelectedPrinter] = useState<string>('b1070uv-brooklyn')
  
  // Mock user for testing (auth disabled)
  const user = { full_name: 'Operator', email: 'operator@scentcraft.com', role: 'operator' }
  const logout = () => { window.location.href = '/login' }

  // Fetch queue
  const { data: queue, isLoading, error: queueError, refetch } = useQuery({
    queryKey: ['queue', selectedPrinter],
    queryFn: async () => {
      const response = await api.get(`/api/operator/queue?printer_id=${selectedPrinter}`)
      return response.data as Job[]
    },
    retry: false,
  })

  // Fetch printers
  const { data: printers } = useQuery({
    queryKey: ['printers'],
    queryFn: async () => {
      const response = await api.get('/api/printers/')
      return response.data
    },
    retry: false,
  })

  // Show error state if backend unavailable
  const backendUnavailable = queueError !== null

  // Separate jobs by status
  const nowPrinting = queue?.filter(j => j.status === 'sent_to_printer') || []
  const awaitingOperator = queue?.filter(j => j.status === 'awaiting_operator') || []
  const upNext = queue?.filter(j => j.status === 'queued_local') || []

  return (
    <div className="min-h-screen bg-midnight-950">
      {/* Header */}
      <header className="sticky top-0 z-50 glass border-b border-midnight-700/50">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-scentcraft-500 to-scentcraft-700 flex items-center justify-center">
                  <Sparkles className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h1 className="font-display text-xl font-semibold text-white">ScentCraft</h1>
                  <p className="text-xs text-midnight-400">Operator Console</p>
                </div>
              </div>
              
              {/* Printer selector */}
              <div className="ml-8 flex items-center gap-2">
                <Printer className="w-4 h-4 text-midnight-400" />
                <select
                  value={selectedPrinter}
                  onChange={(e) => setSelectedPrinter(e.target.value)}
                  className="bg-midnight-800 border border-midnight-700 rounded-lg px-3 py-1.5 text-sm
                           text-white focus:border-scentcraft-500 outline-none"
                >
                  {printers?.map((p: any) => (
                    <option key={p.id} value={p.id}>{p.name}</option>
                  ))}
                  {!printers?.length && (
                    <option value="b1070uv-brooklyn">Epson B1070UV - Brooklyn</option>
                  )}
                </select>
              </div>
            </div>

            <div className="flex items-center gap-4">
              <Link 
                to="/templates"
                className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-midnight-800 text-midnight-400 hover:text-white transition-colors"
              >
                <Grid3X3 className="w-4 h-4" />
                <span className="text-sm">Templates</span>
              </Link>
              <button 
                onClick={() => refetch()}
                className="p-2 rounded-lg hover:bg-midnight-800 text-midnight-400 hover:text-white transition-colors"
              >
                <RefreshCw className="w-5 h-5" />
              </button>
              
              <div className="flex items-center gap-3 pl-4 border-l border-midnight-700">
                <div className="text-right">
                  <p className="text-sm font-medium text-white">{user?.full_name || user?.email}</p>
                  <p className="text-xs text-midnight-500 capitalize">{user?.role}</p>
                </div>
                <button
                  onClick={logout}
                  className="p-2 rounded-lg hover:bg-midnight-800 text-midnight-400 hover:text-white transition-colors"
                >
                  <LogOut className="w-5 h-5" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {backendUnavailable ? (
          <div className="card text-center py-16">
            <div className="w-16 h-16 rounded-2xl bg-amber-500/20 flex items-center justify-center mx-auto mb-4">
              <Sparkles className="w-8 h-8 text-amber-400" />
            </div>
            <h2 className="text-xl font-semibold text-white mb-2">Backend Not Connected</h2>
            <p className="text-midnight-400 max-w-md mx-auto">
              The print server API is not available. Deploy the backend to Railway or Render to enable full functionality.
            </p>
            <div className="mt-6 p-4 bg-midnight-800 rounded-xl text-left max-w-lg mx-auto">
              <p className="text-sm text-midnight-300 font-mono">
                API URL: {import.meta.env.VITE_API_URL || '/api (not configured)'}
              </p>
            </div>
          </div>
        ) : isLoading ? (
          <div className="flex items-center justify-center py-20">
            <div className="w-8 h-8 border-2 border-scentcraft-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Now Printing */}
            <QueueSection
              title="Now Printing"
              icon={Play}
              jobs={nowPrinting}
              emptyText="No jobs printing"
            />

            {/* Awaiting Operator */}
            <QueueSection
              title="Loading Jig"
              icon={Pause}
              jobs={awaitingOperator}
              emptyText="No jobs waiting"
            />

            {/* Up Next */}
            <QueueSection
              title="Up Next"
              icon={Clock}
              jobs={upNext}
              emptyText="Queue is empty"
            />
          </div>
        )}

        {/* Stats bar */}
        <div className="mt-12 grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: 'In Queue', value: upNext.length, color: 'text-purple-400' },
            { label: 'Loading', value: awaitingOperator.length, color: 'text-scentcraft-400' },
            { label: 'Printing', value: nowPrinting.length, color: 'text-cyan-400' },
            { label: 'Total Today', value: (queue?.length || 0), color: 'text-emerald-400' },
          ].map(stat => (
            <div key={stat.label} className="card text-center">
              <p className={clsx('text-3xl font-display font-semibold', stat.color)}>
                {stat.value}
              </p>
              <p className="text-midnight-400 text-sm mt-1">{stat.label}</p>
            </div>
          ))}
        </div>
      </main>
    </div>
  )
}


