# Print Agent Setup - Windows PC

## Quick Start

### 1. Install dependencies
```bash
pip install httpx click python-dateutil
```

### 2. Get your API key
Open this URL in a browser:
```
https://printserver-production.up.railway.app/api/dev/printer-api-key/b1070uv-brooklyn
```
Copy the `api_key` value.

### 3. Run the agent
```bash
cd C:\ScentCraft\PrintAgent\printserver-main\agent
python agent.py --api-url https://printserver-production.up.railway.app --api-key YOUR_API_KEY_HERE --queue-dir "C:\ScentCraftQueue"
```

Replace `YOUR_API_KEY_HERE` with the key from step 2.

---

## What the Agent Does

1. **Polls** the cloud server for new print jobs
2. **Downloads** PDFs to `C:\ScentCraftQueue\job_X\`
3. **Watches** for operator "Print" commands
4. **Copies** PDFs to EdgePrint hot folder when triggered

---

## URLs

| Service | URL |
|---------|-----|
| Console (Frontend) | https://scentcraft-printserver.vercel.app |
| API (Backend) | https://printserver-production.up.railway.app |
| Health Check | https://printserver-production.up.railway.app/health |

---

## Troubleshooting

### "No module named httpx"
```bash
pip install httpx
```

### "No module named click"
```bash
pip install click
```

### Agent can't connect
- Check internet connection
- Verify API key is correct
- Check if backend is running: visit https://printserver-production.up.railway.app/health

### Agent connected but no jobs
- Jobs need to be in `READY_FOR_PRINT` status
- Check console at https://scentcraft-printserver.vercel.app

---

## Hot Folder Setup (EdgePrint)

The agent will copy PDFs to the hot folder specified by the server.
Make sure this folder exists:
```
C:\EdgePrint\hotfolders\bottle_jig_v1\
```

Configure EdgePrint to watch this folder.

