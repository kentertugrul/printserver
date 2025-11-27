import { useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { motion, AnimatePresence } from 'framer-motion'
import axios from 'axios'
import {
  ArrowLeft,
  Printer,
  Package,
  User,
  Droplets,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Loader2,
  Play,
  RotateCcw,
} from 'lucide-react'
import { Job, JobSlot } from '../types'

// Jig map visualization
function JigMap({ slots }: { slots: JobSlot[] }) {
  // Mock layout - in production this would come from the template
  const layout = {
    width: 329,
    height: 483,
    slots: [
      { id: 'bottle_main', x: 50, y: 50, width: 100, height: 150, label: 'A' },
      { id: 'mini_1', x: 200, y: 50, width: 50, height: 80, label: 'B' },
      { id: 'mini_2', x: 200, y: 150, width: 50, height: 80, label: 'C' },
      { id: 'box_top', x: 50, y: 250, width: 150, height: 100, label: 'D' },
    ]
  }

  return (
    <div className="relative bg-midnight-800 rounded-2xl p-4 overflow-hidden">
      {/* Grid pattern background */}
      <div 
        className="absolute inset-0 opacity-10"
        style={{
          backgroundImage: `
            linear-gradient(to right, rgb(100 116 139) 1px, transparent 1px),
            linear-gradient(to bottom, rgb(100 116 139) 1px, transparent 1px)
          `,
          backgroundSize: '20px 20px',
        }}
      />
      
      <svg 
        viewBox={`0 0 ${layout.width} ${layout.height}`}
        className="w-full h-auto relative z-10"
        style={{ maxHeight: '400px' }}
      >
        {/* Print bed outline */}
        <rect
          x="0"
          y="0"
          width={layout.width}
          height={layout.height}
          fill="none"
          stroke="rgb(71 85 105)"
          strokeWidth="2"
          strokeDasharray="8 4"
          rx="8"
        />
        
        {/* Slot positions */}
        {layout.slots.map((slotPos) => {
          const jobSlot = slots.find(s => s.template_slot_id === slotPos.id)
          const hasLabel = !!jobSlot?.label_asset_path
          
          return (
            <g key={slotPos.id}>
              {/* Slot rectangle */}
              <rect
                x={slotPos.x}
                y={slotPos.y}
                width={slotPos.width}
                height={slotPos.height}
                fill={hasLabel ? 'rgba(214, 125, 94, 0.2)' : 'rgba(100, 116, 139, 0.2)'}
                stroke={hasLabel ? 'rgb(214, 125, 94)' : 'rgb(100, 116, 139)'}
                strokeWidth="2"
                rx="4"
              />
              
              {/* Slot label */}
              <text
                x={slotPos.x + slotPos.width / 2}
                y={slotPos.y + 20}
                textAnchor="middle"
                fill="white"
                fontSize="16"
                fontWeight="bold"
              >
                {slotPos.label}
              </text>
              
              {/* Guest name */}
              {jobSlot?.guest_name && (
                <text
                  x={slotPos.x + slotPos.width / 2}
                  y={slotPos.y + slotPos.height / 2}
                  textAnchor="middle"
                  fill="rgb(214, 125, 94)"
                  fontSize="12"
                >
                  {jobSlot.guest_name}
                </text>
              )}
              
              {/* Product type */}
              {jobSlot?.product_type && (
                <text
                  x={slotPos.x + slotPos.width / 2}
                  y={slotPos.y + slotPos.height - 8}
                  textAnchor="middle"
                  fill="rgb(148, 163, 184)"
                  fontSize="10"
                >
                  {jobSlot.product_type.replace(/_/g, ' ')}
                </text>
              )}
            </g>
          )
        })}
      </svg>
    </div>
  )
}

// Slot list component
function SlotList({ slots }: { slots: JobSlot[] }) {
  return (
    <div className="space-y-3">
      {slots.map((slot, idx) => (
        <motion.div
          key={slot.id}
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: idx * 0.1 }}
          className="flex items-center gap-4 p-4 bg-midnight-800/50 rounded-xl border border-midnight-700/50"
        >
          {/* Position badge */}
          <div className="w-10 h-10 rounded-lg bg-scentcraft-500/20 flex items-center justify-center">
            <span className="font-bold text-scentcraft-400">{slot.slot_position || idx + 1}</span>
          </div>
          
          {/* Slot info */}
          <div className="flex-1 min-w-0">
            <p className="font-medium text-white truncate">
              {slot.slot_label || slot.template_slot_id}
            </p>
            <div className="flex items-center gap-3 mt-1 text-sm text-midnight-400">
              {slot.guest_name && (
                <span className="flex items-center gap-1">
                  <User className="w-3.5 h-3.5" />
                  {slot.guest_name}
                </span>
              )}
              {slot.fragrance_name && (
                <span className="flex items-center gap-1">
                  <Droplets className="w-3.5 h-3.5" />
                  {slot.fragrance_name}
                </span>
              )}
              {slot.product_type && (
                <span className="flex items-center gap-1">
                  <Package className="w-3.5 h-3.5" />
                  {slot.product_type.replace(/_/g, ' ')}
                </span>
              )}
            </div>
          </div>
          
          {/* Status indicator */}
          {slot.label_asset_path ? (
            <CheckCircle2 className="w-5 h-5 text-emerald-400" />
          ) : (
            <AlertTriangle className="w-5 h-5 text-amber-400" />
          )}
        </motion.div>
      ))}
    </div>
  )
}

export default function JobDetail() {
  const { jobId } = useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [failReason, setFailReason] = useState('')
  const [showFailModal, setShowFailModal] = useState(false)

  // Fetch job
  const { data: job, isLoading, error } = useQuery({
    queryKey: ['job', jobId],
    queryFn: async () => {
      const response = await axios.get(`/api/jobs/${jobId}`)
      return response.data as Job
    },
  })

  // Mutations
  const jigLoadedMutation = useMutation({
    mutationFn: () => axios.post(`/api/operator/jobs/${jobId}/jig-loaded`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['job', jobId] })
      queryClient.invalidateQueries({ queryKey: ['queue'] })
    },
  })

  const printMutation = useMutation({
    mutationFn: () => axios.post(`/api/operator/jobs/${jobId}/print`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['job', jobId] })
      queryClient.invalidateQueries({ queryKey: ['queue'] })
    },
  })

  const completeMutation = useMutation({
    mutationFn: () => axios.post(`/api/operator/jobs/${jobId}/complete`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['job', jobId] })
      queryClient.invalidateQueries({ queryKey: ['queue'] })
      navigate('/')
    },
  })

  const failMutation = useMutation({
    mutationFn: (reason: string) => axios.post(`/api/operator/jobs/${jobId}/fail?reason=${encodeURIComponent(reason)}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['job', jobId] })
      queryClient.invalidateQueries({ queryKey: ['queue'] })
      setShowFailModal(false)
      navigate('/')
    },
  })

  const returnToQueueMutation = useMutation({
    mutationFn: () => axios.post(`/api/operator/jobs/${jobId}/return-to-queue`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['job', jobId] })
      queryClient.invalidateQueries({ queryKey: ['queue'] })
    },
  })

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-scentcraft-500 animate-spin" />
      </div>
    )
  }

  if (error || !job) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <XCircle className="w-12 h-12 text-red-400 mx-auto mb-4" />
          <p className="text-midnight-400">Job not found</p>
          <Link to="/" className="btn-secondary mt-4 inline-block">
            Back to Dashboard
          </Link>
        </div>
      </div>
    )
  }

  // Determine which actions are available
  const canMarkJigLoaded = job.status === 'queued_local'
  const canPrint = job.status === 'awaiting_operator'
  const canComplete = job.status === 'sent_to_printer'

  return (
    <div className="min-h-screen bg-midnight-950">
      {/* Header */}
      <header className="sticky top-0 z-50 glass border-b border-midnight-700/50">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center gap-4">
            <Link 
              to="/"
              className="p-2 rounded-lg hover:bg-midnight-800 text-midnight-400 hover:text-white transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
            </Link>
            <div>
              <h1 className="font-semibold text-white">
                {job.job_name || `Job #${job.id}`}
              </h1>
              <p className="text-sm text-midnight-400">
                {job.event_name || 'No event'} • {job.copies} {job.copies === 1 ? 'copy' : 'copies'}
              </p>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Left column - Jig Map */}
          <div className="space-y-6">
            <div className="card">
              <h2 className="font-semibold text-white mb-4 flex items-center gap-2">
                <Printer className="w-5 h-5 text-scentcraft-400" />
                Jig Layout
              </h2>
              <JigMap slots={job.slots} />
              
              <div className="mt-4 p-4 bg-scentcraft-500/10 rounded-xl border border-scentcraft-500/20">
                <p className="text-scentcraft-300 text-sm">
                  <strong>Instructions:</strong> Load items into the jig according to the positions shown above. 
                  Match each letter (A, B, C, D) to the corresponding physical slot on your jig.
                </p>
              </div>
            </div>
          </div>

          {/* Right column - Slots & Actions */}
          <div className="space-y-6">
            {/* Slot list */}
            <div className="card">
              <h2 className="font-semibold text-white mb-4 flex items-center gap-2">
                <Package className="w-5 h-5 text-scentcraft-400" />
                Slot Details
              </h2>
              <SlotList slots={job.slots} />
            </div>

            {/* Action buttons */}
            <div className="card">
              <h2 className="font-semibold text-white mb-4">Actions</h2>
              
              <div className="space-y-3">
                {canMarkJigLoaded && (
                  <button
                    onClick={() => jigLoadedMutation.mutate()}
                    disabled={jigLoadedMutation.isPending}
                    className="btn-primary w-full flex items-center justify-center gap-2"
                  >
                    {jigLoadedMutation.isPending ? (
                      <Loader2 className="w-5 h-5 animate-spin" />
                    ) : (
                      <>
                        <CheckCircle2 className="w-5 h-5" />
                        Jig Loaded - Ready to Print
                      </>
                    )}
                  </button>
                )}

                {canPrint && (
                  <>
                    <button
                      onClick={() => printMutation.mutate()}
                      disabled={printMutation.isPending}
                      className="btn-success w-full flex items-center justify-center gap-2"
                    >
                      {printMutation.isPending ? (
                        <Loader2 className="w-5 h-5 animate-spin" />
                      ) : (
                        <>
                          <Play className="w-5 h-5" />
                          Print Now
                        </>
                      )}
                    </button>
                    
                    <button
                      onClick={() => returnToQueueMutation.mutate()}
                      disabled={returnToQueueMutation.isPending}
                      className="btn-secondary w-full flex items-center justify-center gap-2"
                    >
                      <RotateCcw className="w-5 h-5" />
                      Return to Queue
                    </button>
                  </>
                )}

                {canComplete && (
                  <>
                    <button
                      onClick={() => completeMutation.mutate()}
                      disabled={completeMutation.isPending}
                      className="btn-success w-full flex items-center justify-center gap-2"
                    >
                      {completeMutation.isPending ? (
                        <Loader2 className="w-5 h-5 animate-spin" />
                      ) : (
                        <>
                          <CheckCircle2 className="w-5 h-5" />
                          Mark as Printed
                        </>
                      )}
                    </button>
                    
                    <button
                      onClick={() => setShowFailModal(true)}
                      className="btn-danger w-full flex items-center justify-center gap-2"
                    >
                      <XCircle className="w-5 h-5" />
                      Mark as Failed
                    </button>
                  </>
                )}

                {!canMarkJigLoaded && !canPrint && !canComplete && (
                  <p className="text-center text-midnight-500 py-4">
                    No actions available for this job status
                  </p>
                )}
              </div>
            </div>

            {/* Notes */}
            {(job.designer_notes || job.operator_notes) && (
              <div className="card">
                <h2 className="font-semibold text-white mb-4">Notes</h2>
                {job.designer_notes && (
                  <div className="mb-3">
                    <p className="text-xs text-midnight-500 uppercase tracking-wider mb-1">Designer</p>
                    <p className="text-midnight-300 text-sm">{job.designer_notes}</p>
                  </div>
                )}
                {job.operator_notes && (
                  <div>
                    <p className="text-xs text-midnight-500 uppercase tracking-wider mb-1">Operator</p>
                    <p className="text-midnight-300 text-sm whitespace-pre-wrap">{job.operator_notes}</p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Fail modal */}
      <AnimatePresence>
        {showFailModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
            onClick={() => setShowFailModal(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="card max-w-md w-full"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="font-semibold text-white text-lg mb-4">Mark Job as Failed</h3>
              <textarea
                value={failReason}
                onChange={(e) => setFailReason(e.target.value)}
                placeholder="Reason for failure..."
                className="w-full px-4 py-3 rounded-xl bg-midnight-800 border border-midnight-700 
                         text-white placeholder-midnight-500 focus:border-red-500 
                         focus:ring-1 focus:ring-red-500 transition-colors outline-none resize-none"
                rows={3}
              />
              <div className="flex gap-3 mt-4">
                <button
                  onClick={() => setShowFailModal(false)}
                  className="btn-secondary flex-1"
                >
                  Cancel
                </button>
                <button
                  onClick={() => failMutation.mutate(failReason)}
                  disabled={!failReason.trim() || failMutation.isPending}
                  className="btn-danger flex-1 flex items-center justify-center gap-2"
                >
                  {failMutation.isPending ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : (
                    'Confirm Failure'
                  )}
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}



