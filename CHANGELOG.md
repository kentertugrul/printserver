# Changelog

All notable changes to this project will be documented in this file.

## [1.1.0] - 2024-11-27

### Added

#### PDF Composition System
- **Jig Template Upload**: Upload your actual jig PDF as the base template
- **Visual Slot Editor**: Draw slots directly on your uploaded jig PDF
- **PDF Composer Service**: Automatically overlays label artwork onto jig templates
- **Dual Mode Support**: 
  - Option A: Upload PDF + manually define coordinates
  - Option B: Visual editor to draw slot regions on PDF
- **Preview Generation**: Auto-generates PNG preview from uploaded PDFs

#### Template Editor UI
- Interactive canvas with PDF background
- Drag-and-drop slot positioning
- Resize handles for slot dimensions
- Slot properties panel (position, size, rotation, product type)
- Grid overlay toggle for alignment
- Real-time save to server

---

## [1.0.0] - 2024-11-27

### Added

#### Backend API (FastAPI)
- **User Authentication**: JWT-based auth with roles (admin, designer, operator, viewer)
- **Printer Management**: Register printers, manage hot folder mappings, API key generation
- **Template System**: Define jig layouts with slot positions for UV printing
- **Job Lifecycle**: Full state machine from DRAFT → PRINTED/FAILED
- **Designer Endpoints**: Create jobs, upload label assets, submit for printing
- **Agent Endpoints**: Fetch queue, download PDFs, update status (authenticated via API key)
- **Operator Endpoints**: Manage local queue, mark jig loaded, trigger print, confirm completion

#### Print Agent
- Background service for local printer PC
- Polls cloud API for READY_FOR_PRINT jobs
- Downloads PDFs to local queue folder
- Watches for SENT_TO_PRINTER status and copies to EdgePrint hot folder
- Heartbeat system to indicate online status

#### Operator Console (React)
- Modern, dark-themed UI with warm ScentCraft brand colors
- Real-time queue display with auto-refresh
- Job detail view with jig map visualization
- Slot-by-slot loading instructions
- Action buttons: Jig Loaded → Print → Complete/Failed
- Login authentication

#### Database Models
- `User` - Auth and role management
- `Printer` - Physical printer registry with hot folder mappings
- `Template` - Jig layout definitions
- `TemplateSlot` - Individual slot positions within templates
- `Job` - Print jobs with full lifecycle tracking
- `JobSlot` - Per-slot label assignments for each job

### Technical Details
- Backend: Python 3.11+, FastAPI, SQLAlchemy, SQLite (dev) / PostgreSQL (prod)
- Frontend: React 18, TypeScript, TailwindCSS, Framer Motion, TanStack Query
- Agent: Python asyncio with httpx for API communication

