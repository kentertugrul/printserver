"""
ScentCraft Print Server - Main Application

A distributed print job management system for UV printing.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from api import api_router
from models import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - runs on startup and shutdown."""
    # Startup: Initialize database
    init_db()
    print("✓ Database initialized")
    yield
    # Shutdown: cleanup if needed
    print("Shutting down...")


app = FastAPI(
    title="ScentCraft Print Server",
    description="""
    A distributed print job management system for UV printing on custom perfume bottles, boxes, and labels.
    
    ## Overview
    
    This system manages the print workflow from designer to printed product:
    
    1. **Designers** create jobs remotely, upload label art, and submit for printing
    2. **Print Agent** running on the printer PC downloads jobs and manages the local queue
    3. **Operators** use the console to load jigs, trigger prints, and confirm completion
    
    ## Authentication
    
    - **Users** (designers, operators, admins): JWT token via `/api/auth/token`
    - **Print Agents**: API key via `X-API-Key` header
    """,
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware for the operator console
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React dev server
        "http://localhost:5173",  # Vite dev server
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint - basic health check."""
    return {
        "name": "ScentCraft Print Server",
        "status": "running",
        "version": "1.0.0",
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


