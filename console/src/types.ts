export type JobStatus = 
  | 'draft'
  | 'pending_review'
  | 'ready_for_print'
  | 'queued_local'
  | 'awaiting_operator'
  | 'sent_to_printer'
  | 'printed'
  | 'failed'

export interface JobSlot {
  id: number
  template_slot_id: string
  slot_position: string | null
  slot_label: string | null
  label_asset_path: string | null
  label_preview_path: string | null
  guest_name: string | null
  recipient: string | null
  fragrance_id: string | null
  fragrance_name: string | null
  product_type: string | null
  qr_uid: string | null
}

export interface Job {
  id: number
  printer_id: string
  template_id: string
  status: JobStatus
  queue_position: number | null
  local_queue_position: number | null
  priority: number
  job_name: string | null
  event_name: string | null
  event_date: string | null
  copies: number
  composed_pdf_path: string | null
  created_by: number | null
  reprint_of: number | null
  reprint_reason: string | null
  created_at: string
  updated_at: string
  submitted_at: string | null
  downloaded_at: string | null
  printed_at: string | null
  operator_notes: string | null
  designer_notes: string | null
  slots: JobSlot[]
}

export interface Template {
  id: string
  name: string
  description: string | null
  bed_width: number
  bed_height: number
  hot_folder_type: string
  preview_image_path: string | null
  is_active: boolean
  slots: TemplateSlot[]
}

export interface TemplateSlot {
  id: string
  name: string
  slot_position: string | null
  x: number
  y: number
  width: number
  height: number
  rotation: number
  product_type: string | null
  display_order: number
}

export interface Printer {
  id: string
  name: string
  location: string | null
  is_online: boolean
  last_seen: string | null
}



