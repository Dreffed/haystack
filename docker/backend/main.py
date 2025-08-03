#!/usr/bin/env python3
"""
Haystack Backend API Service
FastAPI-based REST API for the Haystack Web Collector Suite
"""

import os
import sys
import asyncio
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

# Add parent directories to path to import haystack modules
sys.path.insert(0, '/app')
sys.path.insert(0, '/app/db')
sys.path.insert(0, '/app/engines')

from db.PeregrinDB import PeregrinDB
from engines.peregrinbase import PeregrinBase

# Initialize FastAPI app
app = FastAPI(
    title="Haystack Web Collector API",
    description="REST API for managing web scraping and data collection",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for web UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for API
class EngineInfo(BaseModel):
    engine_id: int
    name: str
    version: str
    description: str
    disabled: bool = False
    created: datetime

class ItemInfo(BaseModel):
    item_id: int
    uri: str
    engine_id: int
    created: datetime

class ItemData(BaseModel):
    item_id: int
    data_type: str
    value: str
    sequence: int = 0

class StatusMessage(BaseModel):
    engine_id: int
    action_id: int
    message: str
    timestamp: datetime

class ScrapingJob(BaseModel):
    engine_name: str
    action_name: str
    parameters: Dict[str, Any] = {}

class SystemHealth(BaseModel):
    status: str
    database_connected: bool
    active_engines: int
    pending_jobs: int
    last_activity: Optional[datetime]

# Database dependency
async def get_database():
    """Get database connection"""
    try:
        db = PeregrinDB()
        # Use environment variables for database connection
        import configparser
        config = configparser.RawConfigParser()
        
        # Create config from environment variables
        config.add_section('Database')
        config.set('Database', 'Server', os.getenv('DB_HOST', 'database'))
        config.set('Database', 'User', os.getenv('DB_USER', 'peregrin'))
        config.set('Database', 'Password', os.getenv('DB_PASSWORD', 'peregrin_pass_2023'))
        config.set('Database', 'Schema', os.getenv('DB_NAME', 'Peregrin'))
        
        db.connect_db(config)
        return db
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

# Health check endpoint
@app.get("/health", response_model=SystemHealth)
async def health_check(db: PeregrinDB = Depends(get_database)):
    """System health check"""
    try:
        # Test database connectivity
        status = db.getStatus()
        
        return SystemHealth(
            status="healthy",
            database_connected=True,
            active_engines=len(status),
            pending_jobs=0,  # Would need to implement job queue
            last_activity=datetime.now()
        )
    except Exception as e:
        return SystemHealth(
            status="unhealthy",
            database_connected=False,
            active_engines=0,
            pending_jobs=0,
            last_activity=None
        )

# Engine management endpoints
@app.get("/api/engines", response_model=List[EngineInfo])
async def list_engines(db: PeregrinDB = Depends(get_database)):
    """List all registered engines"""
    try:
        # This would need to be implemented in PeregrinDB
        engines = []  # db.getEngines()
        return engines
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/engines/{engine_name}/start")
async def start_engine(
    engine_name: str, 
    background_tasks: BackgroundTasks,
    db: PeregrinDB = Depends(get_database)
):
    """Start a scraping engine"""
    try:
        # Load and start the engine
        background_tasks.add_task(run_engine, engine_name, db)
        return {"message": f"Engine {engine_name} started", "status": "starting"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/engines/{engine_name}/stop")
async def stop_engine(engine_name: str):
    """Stop a scraping engine"""
    # This would require implementing engine management
    return {"message": f"Engine {engine_name} stopped", "status": "stopped"}

# Item management endpoints
@app.get("/api/items", response_model=List[ItemInfo])
async def list_items(
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    engine_id: Optional[int] = None,
    db: PeregrinDB = Depends(get_database)
):
    """List items with pagination"""
    try:
        # This would need proper implementation in PeregrinDB
        items = []
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/items/{item_id}")
async def get_item(item_id: int, db: PeregrinDB = Depends(get_database)):
    """Get specific item details"""
    try:
        uri = db.getItemURI(item_id)
        if not uri:
            raise HTTPException(status_code=404, detail="Item not found")
        
        # Get item data
        item_data = db.getItemDataAll(item_id)
        
        return {
            "item_id": item_id,
            "uri": uri,
            "data": [{"type": row[0], "value": row[1]} for row in item_data]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Status and monitoring endpoints
@app.get("/api/status", response_model=List[StatusMessage])
async def get_system_status(
    limit: int = Query(50, le=200),
    db: PeregrinDB = Depends(get_database)
):
    """Get recent system status messages"""
    try:
        status_list = db.getStatus()
        return [
            StatusMessage(
                engine_id=row.get('EngineId', 0),
                action_id=row.get('ActionId', 0),
                message=row.get('StatusMessage', ''),
                timestamp=row.get('StatusDate', datetime.now())
            ) for row in status_list[:limit]
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/config")
async def get_config(db: PeregrinDB = Depends(get_database)):
    """Get system configuration"""
    try:
        config = {}
        config['RunQueue'] = db.getConfig('RunQueue')
        config['MaxConcurrentJobs'] = db.getConfig('MaxConcurrentJobs')
        config['DefaultDelay'] = db.getConfig('DefaultDelay')
        return config
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/config/{config_name}")
async def update_config(
    config_name: str, 
    value: str, 
    db: PeregrinDB = Depends(get_database)
):
    """Update configuration value"""
    try:
        engine_id = db.get_id()  # Get system engine ID
        db.addConfig(engine_id, config_name, value)
        return {"message": f"Configuration {config_name} updated", "value": value}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Job management endpoints
@app.post("/api/jobs/scrape")
async def create_scraping_job(
    job: ScrapingJob,
    background_tasks: BackgroundTasks,
    db: PeregrinDB = Depends(get_database)
):
    """Create a new scraping job"""
    try:
        # Add job to background tasks
        background_tasks.add_task(run_scraping_job, job, db)
        return {"message": "Scraping job created", "job": job.dict()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Background task functions
async def run_engine(engine_name: str, db: PeregrinDB):
    """Run a scraping engine in the background"""
    try:
        # Dynamically load the engine module
        engine_module = f"engines.{engine_name}"
        module = __import__(engine_module, fromlist=[engine_name])
        
        # Get the engine class (assumes class name matches file name)
        engine_classes = [getattr(module, name) for name in dir(module) 
                         if isinstance(getattr(module, name), type) 
                         and issubclass(getattr(module, name), PeregrinBase)]
        
        if not engine_classes:
            raise Exception(f"No engine class found in {engine_name}")
        
        # Instantiate and run the engine
        engine = engine_classes[0]()
        engine.set_db(db)
        
        # Create basic config
        import configparser
        config = configparser.RawConfigParser()
        config.add_section('Paths')
        config.set('Paths', 'Downloads', '/app/data/downloads')
        config.set('Paths', 'Haystack', '/app/data/haystack')
        
        engine.set_config(config)
        engine.start()
        
    except Exception as e:
        print(f"Error running engine {engine_name}: {e}")

async def run_scraping_job(job: ScrapingJob, db: PeregrinDB):
    """Execute a scraping job"""
    try:
        await run_engine(job.engine_name, db)
    except Exception as e:
        print(f"Error in scraping job: {e}")

# Worker mode for dedicated scraper containers
def run_worker():
    """Run in worker mode for scraping tasks"""
    if os.getenv('WORKER_MODE') == 'true':
        worker_type = os.getenv('WORKER_TYPE', 'scraper')
        print(f"Starting in worker mode: {worker_type}")
        
        # Implement worker logic here
        # This would be a continuous loop checking for jobs
        asyncio.create_task(worker_loop())

async def worker_loop():
    """Main worker loop for processing scraping tasks"""
    while True:
        try:
            # Check for pending jobs and process them
            await asyncio.sleep(30)  # Check every 30 seconds
        except Exception as e:
            print(f"Worker error: {e}")
            await asyncio.sleep(60)  # Wait longer on error

if __name__ == "__main__":
    # Check if running in worker mode
    if os.getenv('WORKER_MODE') == 'true':
        asyncio.run(worker_loop())
    else:
        # Run API server
        host = os.getenv('API_HOST', '0.0.0.0')
        port = int(os.getenv('API_PORT', 8000))
        
        uvicorn.run(
            "main:app",
            host=host,
            port=port,
            reload=False,
            log_level="info"
        )