import { useState, useRef, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import axios from 'axios'
import clsx from 'clsx'
import {
  ArrowLeft,
  Upload,
  Plus,
  Trash2,
  Save,
  Square,
  RotateCcw,
  Loader2,
  CheckCircle2,
  Grid3X3,
} from 'lucide-react'

interface SlotData {
  id: string
  name: string
  slot_position: string
  x_percent: number
  y_percent: number
  width_percent: number
  height_percent: number
  rotation: number
  product_type: string
}

interface TemplateData {
  template_id: string
  bed_width_mm: number
  bed_height_mm: number
  has_pdf: boolean
  slots: SlotData[]
}

// Draggable/Resizable Slot Component
function SlotBox({
  slot,
  isSelected,
  onSelect,
  onChange,
  containerRef,
}: {
  slot: SlotData
  isSelected: boolean
  onSelect: () => void
  onChange: (updates: Partial<SlotData>) => void
  containerRef: React.RefObject<HTMLDivElement>
}) {
  const [isDragging, setIsDragging] = useState(false)
  const [isResizing, setIsResizing] = useState(false)
  const [dragStart, setDragStart] = useState({ x: 0, y: 0, slotX: 0, slotY: 0 })
  const [resizeStart, setResizeStart] = useState({ x: 0, y: 0, width: 0, height: 0 })

  const handleMouseDown = (e: React.MouseEvent, action: 'drag' | 'resize') => {
    e.preventDefault()
    e.stopPropagation()
    onSelect()

    if (action === 'drag') {
      setIsDragging(true)
      setDragStart({
        x: e.clientX,
        y: e.clientY,
        slotX: slot.x_percent,
        slotY: slot.y_percent,
      })
    } else {
      setIsResizing(true)
      setResizeStart({
        x: e.clientX,
        y: e.clientY,
        width: slot.width_percent,
        height: slot.height_percent,
      })
    }
  }

  useEffect(() => {
    if (!isDragging && !isResizing) return

    const handleMouseMove = (e: MouseEvent) => {
      if (!containerRef.current) return

      const rect = containerRef.current.getBoundingClientRect()
      const deltaXPercent = ((e.clientX - (isDragging ? dragStart.x : resizeStart.x)) / rect.width) * 100
      const deltaYPercent = ((e.clientY - (isDragging ? dragStart.y : resizeStart.y)) / rect.height) * 100

      if (isDragging) {
        onChange({
          x_percent: Math.max(0, Math.min(100 - slot.width_percent, dragStart.slotX + deltaXPercent)),
          y_percent: Math.max(0, Math.min(100 - slot.height_percent, dragStart.slotY + deltaYPercent)),
        })
      } else if (isResizing) {
        onChange({
          width_percent: Math.max(5, Math.min(100 - slot.x_percent, resizeStart.width + deltaXPercent)),
          height_percent: Math.max(5, Math.min(100 - slot.y_percent, resizeStart.height + deltaYPercent)),
        })
      }
    }

    const handleMouseUp = () => {
      setIsDragging(false)
      setIsResizing(false)
    }

    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', handleMouseUp)

    return () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
    }
  }, [isDragging, isResizing, dragStart, resizeStart, slot, onChange, containerRef])

  return (
    <div
      className={clsx(
        'absolute border-2 rounded cursor-move transition-colors',
        isSelected
          ? 'border-scentcraft-500 bg-scentcraft-500/20 z-10'
          : 'border-scentcraft-400/50 bg-scentcraft-400/10 hover:border-scentcraft-400'
      )}
      style={{
        left: `${slot.x_percent}%`,
        top: `${slot.y_percent}%`,
        width: `${slot.width_percent}%`,
        height: `${slot.height_percent}%`,
        transform: slot.rotation ? `rotate(${slot.rotation}deg)` : undefined,
      }}
      onMouseDown={(e) => handleMouseDown(e, 'drag')}
    >
      {/* Slot label */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
        <div className="bg-midnight-900/90 px-2 py-1 rounded text-xs font-bold text-scentcraft-400">
          {slot.slot_position}
        </div>
      </div>

      {/* Slot name */}
      <div className="absolute -top-6 left-0 text-xs text-midnight-300 whitespace-nowrap">
        {slot.name}
      </div>

      {/* Resize handle */}
      {isSelected && (
        <div
          className="absolute -bottom-1 -right-1 w-4 h-4 bg-scentcraft-500 rounded-full cursor-se-resize
                     flex items-center justify-center hover:bg-scentcraft-400 transition-colors"
          onMouseDown={(e) => handleMouseDown(e, 'resize')}
        >
          <div className="w-2 h-2 border-r-2 border-b-2 border-white" />
        </div>
      )}
    </div>
  )
}

// Slot Properties Panel
function SlotProperties({
  slot,
  onChange,
  onDelete,
}: {
  slot: SlotData
  onChange: (updates: Partial<SlotData>) => void
  onDelete: () => void
}) {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs text-midnight-400 mb-1">Slot ID</label>
          <input
            type="text"
            value={slot.id}
            onChange={(e) => onChange({ id: e.target.value })}
            className="w-full px-3 py-2 rounded-lg bg-midnight-800 border border-midnight-700 
                     text-white text-sm focus:border-scentcraft-500 outline-none"
          />
        </div>
        <div>
          <label className="block text-xs text-midnight-400 mb-1">Position Label</label>
          <input
            type="text"
            value={slot.slot_position}
            onChange={(e) => onChange({ slot_position: e.target.value })}
            className="w-full px-3 py-2 rounded-lg bg-midnight-800 border border-midnight-700 
                     text-white text-sm focus:border-scentcraft-500 outline-none"
            maxLength={2}
          />
        </div>
      </div>

      <div>
        <label className="block text-xs text-midnight-400 mb-1">Name</label>
        <input
          type="text"
          value={slot.name}
          onChange={(e) => onChange({ name: e.target.value })}
          className="w-full px-3 py-2 rounded-lg bg-midnight-800 border border-midnight-700 
                   text-white text-sm focus:border-scentcraft-500 outline-none"
          placeholder="e.g., 30ml Bottle"
        />
      </div>

      <div>
        <label className="block text-xs text-midnight-400 mb-1">Product Type</label>
        <select
          value={slot.product_type}
          onChange={(e) => onChange({ product_type: e.target.value })}
          className="w-full px-3 py-2 rounded-lg bg-midnight-800 border border-midnight-700 
                   text-white text-sm focus:border-scentcraft-500 outline-none"
        >
          <option value="">Select type...</option>
          <option value="30ml_bottle">30ml Bottle</option>
          <option value="5ml_mini">5ml Mini</option>
          <option value="box_top">Box Top</option>
          <option value="card">Card</option>
          <option value="tag">Tag</option>
          <option value="custom">Custom</option>
        </select>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs text-midnight-400 mb-1">X Position (%)</label>
          <input
            type="number"
            value={slot.x_percent.toFixed(1)}
            onChange={(e) => onChange({ x_percent: parseFloat(e.target.value) || 0 })}
            className="w-full px-3 py-2 rounded-lg bg-midnight-800 border border-midnight-700 
                     text-white text-sm focus:border-scentcraft-500 outline-none"
            step="0.1"
            min="0"
            max="100"
          />
        </div>
        <div>
          <label className="block text-xs text-midnight-400 mb-1">Y Position (%)</label>
          <input
            type="number"
            value={slot.y_percent.toFixed(1)}
            onChange={(e) => onChange({ y_percent: parseFloat(e.target.value) || 0 })}
            className="w-full px-3 py-2 rounded-lg bg-midnight-800 border border-midnight-700 
                     text-white text-sm focus:border-scentcraft-500 outline-none"
            step="0.1"
            min="0"
            max="100"
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs text-midnight-400 mb-1">Width (%)</label>
          <input
            type="number"
            value={slot.width_percent.toFixed(1)}
            onChange={(e) => onChange({ width_percent: parseFloat(e.target.value) || 5 })}
            className="w-full px-3 py-2 rounded-lg bg-midnight-800 border border-midnight-700 
                     text-white text-sm focus:border-scentcraft-500 outline-none"
            step="0.1"
            min="1"
            max="100"
          />
        </div>
        <div>
          <label className="block text-xs text-midnight-400 mb-1">Height (%)</label>
          <input
            type="number"
            value={slot.height_percent.toFixed(1)}
            onChange={(e) => onChange({ height_percent: parseFloat(e.target.value) || 5 })}
            className="w-full px-3 py-2 rounded-lg bg-midnight-800 border border-midnight-700 
                     text-white text-sm focus:border-scentcraft-500 outline-none"
            step="0.1"
            min="1"
            max="100"
          />
        </div>
      </div>

      <div>
        <label className="block text-xs text-midnight-400 mb-1">Rotation (°)</label>
        <input
          type="number"
          value={slot.rotation}
          onChange={(e) => onChange({ rotation: parseFloat(e.target.value) || 0 })}
          className="w-full px-3 py-2 rounded-lg bg-midnight-800 border border-midnight-700 
                   text-white text-sm focus:border-scentcraft-500 outline-none"
          step="1"
          min="-180"
          max="180"
        />
      </div>

      <button
        onClick={onDelete}
        className="w-full btn-danger flex items-center justify-center gap-2 text-sm py-2"
      >
        <Trash2 className="w-4 h-4" />
        Delete Slot
      </button>
    </div>
  )
}

export default function TemplateEditor() {
  const { templateId } = useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const canvasRef = useRef<HTMLDivElement>(null)

  const [slots, setSlots] = useState<SlotData[]>([])
  const [selectedSlotId, setSelectedSlotId] = useState<string | null>(null)
  const [showGrid, setShowGrid] = useState(true)
  const [isUploading, setIsUploading] = useState(false)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)

  // Fetch template data
  const { data: templateData, isLoading } = useQuery({
    queryKey: ['template-visual', templateId],
    queryFn: async () => {
      const response = await axios.get(`/api/templates/${templateId}/slots/visual`)
      return response.data as TemplateData
    },
    enabled: !!templateId,
  })

  // Load slots when data arrives
  useEffect(() => {
    if (templateData?.slots) {
      setSlots(templateData.slots)
    }
  }, [templateData])

  // Load preview image
  useEffect(() => {
    if (templateData?.has_pdf) {
      setPreviewUrl(`/api/templates/${templateId}/preview?t=${Date.now()}`)
    }
  }, [templateData, templateId])

  // Save mutation
  const saveMutation = useMutation({
    mutationFn: async () => {
      const formData = new FormData()
      formData.append('slots_json', JSON.stringify(slots))
      await axios.post(`/api/templates/${templateId}/slots/visual`, formData)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['template-visual', templateId] })
    },
  })

  // Upload PDF mutation
  const uploadPdfMutation = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData()
      formData.append('file', file)
      await axios.post(`/api/templates/${templateId}/upload-pdf`, formData)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['template-visual', templateId] })
      setPreviewUrl(`/api/templates/${templateId}/preview?t=${Date.now()}`)
    },
  })

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    setIsUploading(true)
    try {
      await uploadPdfMutation.mutateAsync(file)
    } finally {
      setIsUploading(false)
    }
  }

  const addSlot = () => {
    const newSlot: SlotData = {
      id: `slot_${slots.length + 1}`,
      name: `Slot ${slots.length + 1}`,
      slot_position: String.fromCharCode(65 + slots.length), // A, B, C...
      x_percent: 10,
      y_percent: 10,
      width_percent: 20,
      height_percent: 25,
      rotation: 0,
      product_type: '',
    }
    setSlots([...slots, newSlot])
    setSelectedSlotId(newSlot.id)
  }

  const updateSlot = (id: string, updates: Partial<SlotData>) => {
    setSlots(slots.map(s => s.id === id ? { ...s, ...updates } : s))
  }

  const deleteSlot = (id: string) => {
    setSlots(slots.filter(s => s.id !== id))
    if (selectedSlotId === id) {
      setSelectedSlotId(null)
    }
  }

  const selectedSlot = slots.find(s => s.id === selectedSlotId)

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-scentcraft-500 animate-spin" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-midnight-950">
      {/* Header */}
      <header className="sticky top-0 z-50 glass border-b border-midnight-700/50">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link
                to="/"
                className="p-2 rounded-lg hover:bg-midnight-800 text-midnight-400 hover:text-white transition-colors"
              >
                <ArrowLeft className="w-5 h-5" />
              </Link>
              <div>
                <h1 className="font-semibold text-white">Template Editor</h1>
                <p className="text-sm text-midnight-400">{templateId}</p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={() => setShowGrid(!showGrid)}
                className={clsx(
                  'p-2 rounded-lg transition-colors',
                  showGrid
                    ? 'bg-scentcraft-500/20 text-scentcraft-400'
                    : 'text-midnight-400 hover:text-white hover:bg-midnight-800'
                )}
                title="Toggle grid"
              >
                <Grid3X3 className="w-5 h-5" />
              </button>

              <button
                onClick={() => saveMutation.mutate()}
                disabled={saveMutation.isPending}
                className="btn-primary flex items-center gap-2"
              >
                {saveMutation.isPending ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : saveMutation.isSuccess ? (
                  <CheckCircle2 className="w-4 h-4" />
                ) : (
                  <Save className="w-4 h-4" />
                )}
                Save Template
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Canvas area */}
          <div className="lg:col-span-3">
            <div className="card">
              {/* Upload area if no PDF */}
              {!templateData?.has_pdf && (
                <div className="mb-6">
                  <label className="block">
                    <div className="border-2 border-dashed border-midnight-600 rounded-xl p-8 text-center
                                  hover:border-scentcraft-500 transition-colors cursor-pointer">
                      <input
                        type="file"
                        accept=".pdf"
                        onChange={handleFileUpload}
                        className="hidden"
                      />
                      {isUploading ? (
                        <Loader2 className="w-8 h-8 text-scentcraft-500 animate-spin mx-auto" />
                      ) : (
                        <>
                          <Upload className="w-8 h-8 text-midnight-500 mx-auto mb-3" />
                          <p className="text-midnight-300 font-medium">Upload Jig Template PDF</p>
                          <p className="text-midnight-500 text-sm mt-1">
                            Your jig layout will be used as the background for positioning slots
                          </p>
                        </>
                      )}
                    </div>
                  </label>
                </div>
              )}

              {/* Canvas */}
              <div
                ref={canvasRef}
                className="relative bg-midnight-800 rounded-xl overflow-hidden"
                style={{ aspectRatio: templateData ? `${templateData.bed_width_mm} / ${templateData.bed_height_mm}` : '329 / 483' }}
                onClick={() => setSelectedSlotId(null)}
              >
                {/* Grid overlay */}
                {showGrid && (
                  <div
                    className="absolute inset-0 opacity-20 pointer-events-none"
                    style={{
                      backgroundImage: `
                        linear-gradient(to right, rgb(100 116 139) 1px, transparent 1px),
                        linear-gradient(to bottom, rgb(100 116 139) 1px, transparent 1px)
                      `,
                      backgroundSize: '10% 10%',
                    }}
                  />
                )}

                {/* Template PDF preview */}
                {previewUrl && (
                  <img
                    src={previewUrl}
                    alt="Template preview"
                    className="absolute inset-0 w-full h-full object-contain opacity-50"
                    onError={() => setPreviewUrl(null)}
                  />
                )}

                {/* Slots */}
                {slots.map((slot) => (
                  <SlotBox
                    key={slot.id}
                    slot={slot}
                    isSelected={selectedSlotId === slot.id}
                    onSelect={() => setSelectedSlotId(slot.id)}
                    onChange={(updates) => updateSlot(slot.id, updates)}
                    containerRef={canvasRef}
                  />
                ))}

                {/* Empty state */}
                {slots.length === 0 && !previewUrl && (
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="text-center">
                      <Square className="w-12 h-12 text-midnight-600 mx-auto mb-3" />
                      <p className="text-midnight-500">No slots defined</p>
                      <p className="text-midnight-600 text-sm">Upload a PDF or add slots manually</p>
                    </div>
                  </div>
                )}
              </div>

              {/* Canvas info */}
              <div className="flex items-center justify-between mt-4 text-sm text-midnight-400">
                <span>
                  Bed size: {templateData?.bed_width_mm || 329}mm × {templateData?.bed_height_mm || 483}mm
                </span>
                <span>{slots.length} slot{slots.length !== 1 ? 's' : ''}</span>
              </div>
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Add slot button */}
            <button
              onClick={addSlot}
              className="btn-secondary w-full flex items-center justify-center gap-2"
            >
              <Plus className="w-4 h-4" />
              Add Slot
            </button>

            {/* Slot list */}
            <div className="card">
              <h3 className="font-semibold text-white mb-4">Slots</h3>
              {slots.length === 0 ? (
                <p className="text-midnight-500 text-sm">No slots yet</p>
              ) : (
                <div className="space-y-2">
                  {slots.map((slot) => (
                    <button
                      key={slot.id}
                      onClick={() => setSelectedSlotId(slot.id)}
                      className={clsx(
                        'w-full text-left px-3 py-2 rounded-lg transition-colors',
                        selectedSlotId === slot.id
                          ? 'bg-scentcraft-500/20 text-scentcraft-400'
                          : 'hover:bg-midnight-800 text-midnight-300'
                      )}
                    >
                      <span className="font-bold mr-2">{slot.slot_position}</span>
                      {slot.name}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Slot properties */}
            {selectedSlot && (
              <div className="card">
                <h3 className="font-semibold text-white mb-4">Slot Properties</h3>
                <SlotProperties
                  slot={selectedSlot}
                  onChange={(updates) => updateSlot(selectedSlot.id, updates)}
                  onDelete={() => deleteSlot(selectedSlot.id)}
                />
              </div>
            )}

            {/* Re-upload PDF */}
            {templateData?.has_pdf && (
              <div className="card">
                <h3 className="font-semibold text-white mb-4">Template PDF</h3>
                <label className="block">
                  <div className="border border-midnight-700 rounded-lg p-3 text-center
                                hover:border-scentcraft-500 transition-colors cursor-pointer">
                    <input
                      type="file"
                      accept=".pdf"
                      onChange={handleFileUpload}
                      className="hidden"
                    />
                    {isUploading ? (
                      <Loader2 className="w-5 h-5 text-scentcraft-500 animate-spin mx-auto" />
                    ) : (
                      <span className="text-midnight-400 text-sm flex items-center justify-center gap-2">
                        <RotateCcw className="w-4 h-4" />
                        Replace PDF
                      </span>
                    )}
                  </div>
                </label>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}



