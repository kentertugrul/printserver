#!/usr/bin/env python3
"""
ScentCraft Print Agent

This service runs on the local printer PC and:
1. Polls the cloud API for new jobs (READY_FOR_PRINT status)
2. Downloads PDFs to a local queue folder
3. Updates job status to QUEUED_LOCAL
4. Watches for SENT_TO_PRINTER status and copies files to EdgePrint hot folder
5. Sends heartbeats to indicate online status

Usage:
    python agent.py --api-url http://your-server:8000 --api-key YOUR_KEY --queue-dir C:\\ScentCraftQueue
"""

import asyncio
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import click
import httpx


class PrintAgent:
    """Print Agent service that bridges cloud jobs to local EdgePrint."""
    
    def __init__(
        self,
        api_url: str,
        api_key: str,
        queue_dir: str,
        poll_interval: int = 10,
    ):
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key
        self.queue_dir = Path(queue_dir)
        self.poll_interval = poll_interval
        
        # Create queue directory
        self.queue_dir.mkdir(parents=True, exist_ok=True)
        
        # HTTP client with auth header
        self.client = httpx.AsyncClient(
            base_url=self.api_url,
            headers={"X-API-Key": api_key},
            timeout=30.0,
        )
        
        self._running = False
        self._printer_id: Optional[str] = None
    
    async def start(self):
        """Start the agent service."""
        self._running = True
        print(f"🖨️  ScentCraft Print Agent starting...")
        print(f"   API: {self.api_url}")
        print(f"   Queue: {self.queue_dir}")
        print()
        
        # Verify API connection with first heartbeat
        try:
            result = await self.send_heartbeat()
            self._printer_id = result.get("printer_id")
            print(f"✓ Connected as printer: {self._printer_id}")
        except Exception as e:
            print(f"✗ Failed to connect: {e}")
            return
        
        print()
        print("Agent running. Press Ctrl+C to stop.")
        print("=" * 50)
        
        # Run main loops
        await asyncio.gather(
            self.heartbeat_loop(),
            self.poll_new_jobs_loop(),
            self.watch_print_triggers_loop(),
        )
    
    async def stop(self):
        """Stop the agent service."""
        self._running = False
        await self.client.aclose()
    
    async def send_heartbeat(self) -> dict:
        """Send heartbeat to server."""
        response = await self.client.post(
            "/api/agent/heartbeat",
            json={"printer_id": self._printer_id or "unknown"}
        )
        response.raise_for_status()
        return response.json()
    
    async def heartbeat_loop(self):
        """Periodically send heartbeats."""
        while self._running:
            try:
                await self.send_heartbeat()
            except Exception as e:
                print(f"⚠ Heartbeat failed: {e}")
            await asyncio.sleep(30)  # Heartbeat every 30 seconds
    
    async def poll_new_jobs_loop(self):
        """Poll for new jobs and download them."""
        while self._running:
            try:
                await self.check_for_new_jobs()
            except Exception as e:
                print(f"⚠ Job poll failed: {e}")
            await asyncio.sleep(self.poll_interval)
    
    async def check_for_new_jobs(self):
        """Check for jobs ready for download."""
        response = await self.client.get("/api/agent/jobs")
        response.raise_for_status()
        jobs = response.json()
        
        for job in jobs:
            job_id = job["id"]
            job_name = job.get("job_name") or f"Job {job_id}"
            
            # Check if already downloaded
            job_dir = self.queue_dir / f"job_{job_id}"
            if job_dir.exists():
                continue
            
            print(f"📥 Downloading: {job_name}")
            await self.download_job(job)
    
    async def download_job(self, job: dict):
        """Download a job's PDF and mark as downloaded."""
        job_id = job["id"]
        job_name = job.get("job_name") or f"Job {job_id}"
        event_name = job.get("event_name") or "print"
        
        # Create job directory
        job_dir = self.queue_dir / f"job_{job_id}"
        job_dir.mkdir(exist_ok=True)
        
        # Download PDF
        pdf_path = job_dir / f"JOB-{job_id}_{event_name}.pdf"
        
        try:
            response = await self.client.get(f"/api/agent/jobs/{job_id}/download")
            response.raise_for_status()
            
            with open(pdf_path, "wb") as f:
                f.write(response.content)
            
            print(f"   ✓ Saved to: {pdf_path}")
            
            # Save job metadata
            import json
            meta_path = job_dir / "job.json"
            with open(meta_path, "w") as f:
                json.dump(job, f, indent=2, default=str)
            
            # Mark as downloaded
            response = await self.client.post(f"/api/agent/jobs/{job_id}/mark-downloaded")
            response.raise_for_status()
            print(f"   ✓ Marked as QUEUED_LOCAL")
            
        except Exception as e:
            print(f"   ✗ Download failed: {e}")
            # Clean up failed download
            if job_dir.exists():
                shutil.rmtree(job_dir)
    
    async def watch_print_triggers_loop(self):
        """Watch for jobs that need to be sent to EdgePrint."""
        while self._running:
            try:
                await self.check_for_print_triggers()
            except Exception as e:
                print(f"⚠ Print trigger check failed: {e}")
            await asyncio.sleep(2)  # Check frequently for print triggers
    
    async def check_for_print_triggers(self):
        """Check for jobs in SENT_TO_PRINTER status and copy to hot folder."""
        # Get queue status to find jobs needing print
        response = await self.client.get("/api/agent/queue-status")
        response.raise_for_status()
        status = response.json()
        
        sent_count = status.get("status_counts", {}).get("sent_to_printer", 0)
        if sent_count == 0:
            return
        
        # Get jobs that need to be sent to EdgePrint
        # We need to check local jobs in SENT_TO_PRINTER status
        for job_dir in self.queue_dir.iterdir():
            if not job_dir.is_dir() or not job_dir.name.startswith("job_"):
                continue
            
            job_id = int(job_dir.name.split("_")[1])
            
            # Check if already sent (marker file)
            sent_marker = job_dir / ".sent_to_edgeprint"
            if sent_marker.exists():
                continue
            
            # Get print info from server
            try:
                response = await self.client.get(f"/api/agent/jobs/{job_id}/print-info")
                if response.status_code == 400:
                    # Job not in SENT_TO_PRINTER status, skip
                    continue
                response.raise_for_status()
                print_info = response.json()
                
                await self.send_to_edgeprint(job_dir, print_info)
                
            except httpx.HTTPStatusError as e:
                if e.response.status_code != 400:
                    print(f"⚠ Error checking job {job_id}: {e}")
    
    async def send_to_edgeprint(self, job_dir: Path, print_info: dict):
        """Copy PDF to EdgePrint hot folder."""
        job_id = print_info["job_id"]
        hot_folder = Path(print_info["hot_folder_path"])
        filename = print_info["filename"]
        
        # Find the PDF in the job directory
        pdf_files = list(job_dir.glob("*.pdf"))
        if not pdf_files:
            print(f"⚠ No PDF found for job {job_id}")
            return
        
        source_pdf = pdf_files[0]
        dest_pdf = hot_folder / filename
        
        print(f"🖨️  Sending to EdgePrint: Job {job_id}")
        print(f"   From: {source_pdf}")
        print(f"   To:   {dest_pdf}")
        
        try:
            # Ensure hot folder exists
            hot_folder.mkdir(parents=True, exist_ok=True)
            
            # Copy file
            shutil.copy2(source_pdf, dest_pdf)
            
            # Mark as sent
            sent_marker = job_dir / ".sent_to_edgeprint"
            sent_marker.write_text(datetime.utcnow().isoformat())
            
            # Confirm to server
            await self.client.post(f"/api/agent/jobs/{job_id}/confirm-sent")
            
            print(f"   ✓ File copied to hot folder")
            
        except Exception as e:
            print(f"   ✗ Failed: {e}")


@click.command()
@click.option(
    "--api-url",
    required=True,
    help="URL of the print server API (e.g., http://your-server:8000)"
)
@click.option(
    "--api-key",
    required=True,
    help="API key for this printer agent"
)
@click.option(
    "--queue-dir",
    default="./queue",
    help="Local directory to store downloaded jobs"
)
@click.option(
    "--poll-interval",
    default=10,
    help="Seconds between job polls (default: 10)"
)
def main(api_url: str, api_key: str, queue_dir: str, poll_interval: int):
    """ScentCraft Print Agent - bridges cloud jobs to local EdgePrint."""
    agent = PrintAgent(
        api_url=api_url,
        api_key=api_key,
        queue_dir=queue_dir,
        poll_interval=poll_interval,
    )
    
    try:
        asyncio.run(agent.start())
    except KeyboardInterrupt:
        print("\nShutting down...")
        asyncio.run(agent.stop())


if __name__ == "__main__":
    main()



