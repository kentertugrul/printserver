# ScentCraft Print Server

A distributed print job management system for UV printing on custom perfume bottles, boxes, and labels.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     CLOUD (Your Server)                              │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │              Print Job Manager API                           │    │
│  │  • Designer uploads label art                                │    │
│  │  • System composes final PDFs with jig layouts               │    │
│  │  • Jobs assigned to printers, enter queue                    │    │
│  └─────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              │ REST API / WebSocket
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  LOCAL (Printer PC)                                  │
│  ┌───────────────────┐    ┌────────────────────────────────────┐    │
│  │   Print Agent     │◄──►│      Operator Console              │    │
│  │  • Polls API      │    │  • Shows job queue                 │    │
│  │  • Downloads PDFs │    │  • Jig layout preview              │    │
│  │  • Copies to hot  │    │  • Load/Print/Done buttons         │    │
│  │    folder         │    │  • Slot mapping display            │    │
│  └───────────────────┘    └────────────────────────────────────┘    │
│           │                                                          │
│           ▼                                                          │
│  ┌───────────────────┐                                              │
│  │   Epson EdgePrint │                                              │
│  │   (Hot Folder)    │                                              │
│  └───────────────────┘                                              │
└─────────────────────────────────────────────────────────────────────┘
```

## Job Lifecycle

```
DRAFT → PENDING_REVIEW → READY_FOR_PRINT → QUEUED_LOCAL → AWAITING_OPERATOR → SENT_TO_PRINTER → PRINTED
                                                                    │                              │
                                                                    └──────────► FAILED ◄─────────┘
```

| Status | Description |
|--------|-------------|
| `DRAFT` | Designer is editing/uploading art |
| `PENDING_REVIEW` | Awaiting internal approval (optional) |
| `READY_FOR_PRINT` | Final PDF generated, waiting for pickup |
| `QUEUED_LOCAL` | Agent downloaded PDF, in operator's queue |
| `AWAITING_OPERATOR` | Operator selected job, loading jig |
| `SENT_TO_PRINTER` | PDF dropped into EdgePrint hot folder |
| `PRINTED` | Operator confirmed success |
| `FAILED` | Issue flagged, can be re-queued |

## Project Structure

```
├── backend/              # FastAPI server (Cloud)
│   ├── api/              # API route handlers
│   ├── models/           # SQLAlchemy database models
│   ├── schemas/          # Pydantic request/response schemas
│   ├── services/         # Business logic
│   └── main.py           # Application entry point
├── agent/                # Print Agent (Local)
│   └── agent.py          # Polling service
├── console/              # Operator Console (React)
│   └── src/
├── scripts/              # Utility scripts
└── docs/                 # Additional documentation
```

## Quick Start

### Backend (Cloud Server)

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Operator Console

```bash
cd console
npm install
npm run dev
```

### Print Agent (Local Printer PC)

```bash
cd agent
pip install -r requirements.txt
python agent.py --printer-id b1070uv-brooklyn --api-url http://your-server:8000
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection string | `sqlite:///./scentcraft.db` |
| `API_SECRET_KEY` | JWT signing key | (required) |
| `AGENT_API_KEY` | API key for print agents | (required) |

### Printer Hot Folders

Configure in `backend/config.py` or via API:

```python
PRINTERS = {
    "b1070uv-brooklyn": {
        "name": "Epson B1070UV - Brooklyn",
        "hot_folders": {
            "bottle_jig_v1": "C:\\EdgePrint\\hotfolders\\bottle_jig_v1\\",
            "cards_jig_v1": "C:\\EdgePrint\\hotfolders\\cards_jig_v1\\"
        }
    }
}
```

## Template Editor

The visual template editor lets you define slot positions by uploading your jig PDF:

1. Navigate to `/template/{template_id}/edit`
2. Upload your jig PDF (the layout your printer uses)
3. Draw rectangles on the PDF to define where labels go
4. Save - coordinates are stored in mm based on bed dimensions

```
┌─────────────────────────────────────────────────────────────────┐
│                    Your Jig Template PDF                         │
│                                                                  │
│    ┌───────────┐         ┌─────┐                                │
│    │  Slot A   │         │  B  │   ← Draw slots visually         │
│    │  (drag)   │         └─────┘                                │
│    └───────────┘         ┌─────┐                                │
│                          │  C  │                                │
│    ┌─────────────────────┴─────┘                                │
│    │       Slot D                                               │
│    └─────────────────────────────                               │
└─────────────────────────────────────────────────────────────────┘
```

## API Overview

### Template Editor Endpoints
- `POST /api/templates/{id}/upload-pdf` - Upload jig template PDF
- `GET /api/templates/{id}/preview` - Get PDF preview image
- `GET /api/templates/{id}/slots/visual` - Get slots as percentages
- `POST /api/templates/{id}/slots/visual` - Save slots from visual editor

### Designer Endpoints
- `POST /api/jobs` - Create new print job
- `POST /api/jobs/{id}/labels` - Upload label assets
- `PUT /api/jobs/{id}` - Update job details
- `POST /api/jobs/{id}/submit` - Submit for printing (generates composed PDF)

### Agent Endpoints
- `GET /api/printers/{id}/jobs?status=READY_FOR_PRINT` - Fetch queue
- `GET /api/jobs/{id}/download` - Download composed PDF
- `PUT /api/jobs/{id}/status` - Update job status

### Operator Endpoints
- `GET /api/operator/queue` - Get local queue
- `PUT /api/operator/jobs/{id}/reorder` - Reorder queue
- `POST /api/operator/jobs/{id}/jig-loaded` - Mark jig loaded
- `POST /api/operator/jobs/{id}/print` - Trigger print
- `POST /api/operator/jobs/{id}/complete` - Mark complete
- `POST /api/operator/jobs/{id}/fail` - Mark failed

## License

Proprietary - ScentCraft

