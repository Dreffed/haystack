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
import uuid

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

# Add parent directories to path to import haystack modules
sys.path.insert(0, '/app')
sys.path.insert(0, '/app/db')
sys.path.insert(0, '/app/engines')
sys.path.insert(0, '/app/utils')

from db.PeregrinDB_v2 import PeregrinDB, PeregrinDBError
from engines.peregrinbase import PeregrinBase
from utils.logging_config import get_logger, setup_logging, logging_context, set_correlation_id
from utils.retry_utils import robust_database_operation, robust_network_operation

# Set up logging
setup_logging(
    log_level=os.getenv('LOG_LEVEL', 'INFO'),
    log_dir='/app/logs',
    enable_json_logging=True,
    enable_console_logging=True
)

logger = get_logger('api.main')

# Initialize FastAPI app
app = FastAPI(
    title="Haystack Web Collector API",
    description="REST API for managing web scraping and data collection",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Add correlation ID and logging context to all requests"""
    correlation_id = str(uuid.uuid4())
    set_correlation_id(correlation_id)
    
    with logging_context(
        correlation_id=correlation_id,
        operation=f"{request.method} {request.url.path}",
        user_id="api_user",
        request_id=correlation_id
    ):
        start_time = datetime.now()
        logger.info(f"Request started: {request.method} {request.url.path}")
        
        response = await call_next(request)
        
        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"Request completed: {request.method} {request.url.path} - {response.status_code} - {duration:.4f}s")
        
        # Add correlation ID to response headers
        response.headers["X-Correlation-ID"] = correlation_id
        
        return response

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
@robust_database_operation
async def get_database() -> PeregrinDB:
    """Get database connection with connection pooling"""
    try:
        db = PeregrinDB()
        
        # Create config from environment variables
        config = {
            'host': os.getenv('DB_HOST', 'database'),
            'port': int(os.getenv('DB_PORT', 3306)),
            'user': os.getenv('DB_USER', 'peregrin'),
            'password': os.getenv('DB_PASSWORD', 'peregrin_pass_2023'),
            'database': os.getenv('DB_NAME', 'Peregrin'),
            'charset': 'utf8mb4',
            'pool_size': int(os.getenv('DB_POOL_SIZE', 10)),
            'max_overflow': int(os.getenv('DB_MAX_OVERFLOW', 20))
        }
        
        db.connect_db(config)
        logger.debug("Database connection established")
        return db
        
    except PeregrinDBError as e:
        logger.error(f"Database connection failed: {e}")
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected database error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# Health check endpoint
@app.get("/health", response_model=SystemHealth)
async def health_check():
    """System health check"""
    with logging_context(operation="health_check"):
        try:
            db = await get_database()
            
            # Test database connectivity
            status = db.getStatus(limit=10)
            pool_status = db.get_pool_status()
            
            logger.info(f"Health check completed - Database pool status: {pool_status}")
            
            return SystemHealth(
                status="healthy",
                database_connected=True,
                active_engines=pool_status.get('checked_out', 0),
                pending_jobs=0,  # Would need to implement job queue
                last_activity=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Health check failed: {e}", exc_info=True)
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

# Database Admin API endpoints
@app.get("/api/admin/tables")
async def list_tables(db: PeregrinDB = Depends(get_database)):
    """List all database tables"""
    try:
        tables = [
            {"name": "Engines", "description": "Scraping engines", "primary_key": "EngineId"},
            {"name": "Items", "description": "Scraped items", "primary_key": "itemId"},
            {"name": "ItemData", "description": "Item data fields", "primary_key": "ItemDataId"},
            {"name": "Actions", "description": "Engine actions", "primary_key": "actionId"},
            {"name": "EngineActions", "description": "Engine-action mapping", "primary_key": "engineActionId"},
            {"name": "ItemEvents", "description": "Item processing events", "primary_key": "ItemEventId"},
            {"name": "ItemLinks", "description": "Item relationships", "primary_key": "itemLinkId"},
            {"name": "LinkTypes", "description": "Link type definitions", "primary_key": "LinkTypeId"},
            {"name": "Status", "description": "System status messages", "primary_key": "statusId"},
            {"name": "Config", "description": "System configuration", "primary_key": "configId"}
        ]
        return {"tables": tables}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/tables/{table_name}/schema")
async def get_table_schema(table_name: str, db: PeregrinDB = Depends(get_database)):
    """Get table schema information"""
    try:
        schemas = {
            "Engines": [
                {"name": "EngineId", "type": "int", "primary": True, "auto_increment": True},
                {"name": "EngineName", "type": "varchar(100)", "required": True},
                {"name": "EngineVersion", "type": "varchar(20)", "required": True},
                {"name": "EngineDesc", "type": "text", "required": False},
                {"name": "EngineDisabled", "type": "tinyint(1)", "default": 0},
                {"name": "EngineCreated", "type": "timestamp", "default": "CURRENT_TIMESTAMP"}
            ],
            "Items": [
                {"name": "itemId", "type": "int", "primary": True, "auto_increment": True},
                {"name": "ItemURI", "type": "text", "required": True},
                {"name": "EngineId", "type": "int", "required": True, "foreign_key": "Engines.EngineId"},
                {"name": "ItemDTS", "type": "timestamp", "required": True},
                {"name": "itemCreated", "type": "timestamp", "default": "CURRENT_TIMESTAMP"}
            ],
            "ItemData": [
                {"name": "ItemDataId", "type": "int", "primary": True, "auto_increment": True},
                {"name": "itemId", "type": "int", "required": True, "foreign_key": "Items.itemId"},
                {"name": "itemData", "type": "varchar(100)", "required": True},
                {"name": "itemDataValue", "type": "text", "required": False},
                {"name": "itemDataSeq", "type": "int", "default": 0},
                {"name": "itemDataAdded", "type": "timestamp", "default": "CURRENT_TIMESTAMP"}
            ],
            "Actions": [
                {"name": "actionId", "type": "int", "primary": True, "auto_increment": True},
                {"name": "actionName", "type": "varchar(100)", "required": True},
                {"name": "actionDesc", "type": "text", "required": False},
                {"name": "actionCreated", "type": "timestamp", "default": "CURRENT_TIMESTAMP"}
            ],
            "Config": [
                {"name": "configId", "type": "int", "primary": True, "auto_increment": True},
                {"name": "configName", "type": "varchar(100)", "required": True},
                {"name": "configValue", "type": "text", "required": False},
                {"name": "configUpdated", "type": "timestamp", "default": "CURRENT_TIMESTAMP"}
            ]
        }
        
        if table_name not in schemas:
            raise HTTPException(status_code=404, detail=f"Table {table_name} not found")
        
        return {"table": table_name, "columns": schemas[table_name]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/tables/{table_name}/data")
async def get_table_data(
    table_name: str,
    limit: int = Query(50, le=1000),
    offset: int = Query(0, ge=0),
    search: Optional[str] = None,
    db: PeregrinDB = Depends(get_database)
):
    """Get table data with pagination and search"""
    try:
        # Use existing database methods where available
        if table_name == "Engines":
            data = db.getEngines(limit=limit, offset=offset)
        elif table_name == "Items":
            data = db.getItems(limit=limit, offset=offset)
        elif table_name == "ItemData":
            data = db.getItemDataPaginated(limit=limit, offset=offset)
        elif table_name == "Actions":
            data = db.getActions(limit=limit, offset=offset)
        elif table_name == "Config":
            data = db.getAllConfig(limit=limit, offset=offset)
        elif table_name == "Status":
            data = db.getStatus(limit=limit)
        else:
            raise HTTPException(status_code=404, detail=f"Table {table_name} not supported")
        
        # Get total count for pagination
        try:
            total_count = db.getTableCount(table_name)
        except:
            total_count = len(data) if data else 0
        
        # Apply search if provided
        if search and data:
            try:
                data = db.searchTable(table_name, search, limit=limit, offset=offset)
                total_count = len(data)  # Search results count
            except:
                # Fallback to basic filtering
                data = [record for record in data if search.lower() in str(record).lower()]
        
        return {
            "table": table_name,
            "data": data or [],
            "pagination": {
                "limit": limit,
                "offset": offset,
                "total": total_count,
                "has_next": (offset + limit) < total_count,
                "has_prev": offset > 0
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/tables/{table_name}/records/{record_id}")
async def get_record(table_name: str, record_id: int, db: PeregrinDB = Depends(get_database)):
    """Get a specific record by ID"""
    try:
        # Route to appropriate method based on table
        if table_name == "Items":
            uri = db.getItemURI(record_id)
            if not uri:
                raise HTTPException(status_code=404, detail="Record not found")
            
            item_data = db.getItemDataAll(record_id)
            return {
                "itemId": record_id,
                "ItemURI": uri,
                "data": [{"type": row[0], "value": row[1]} for row in item_data]
            }
        else:
            # Would need to implement generic record retrieval
            return {"message": f"Record retrieval for {table_name} not yet implemented"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/admin/tables/{table_name}/records/{record_id}")
async def update_record(
    table_name: str, 
    record_id: int, 
    record_data: Dict[str, Any], 
    db: PeregrinDB = Depends(get_database)
):
    """Update a specific record"""
    try:
        # Update record based on table type
        if table_name == "Engines":
            result = db.updateEngine(
                record_id,
                name=record_data.get("EngineName"),
                version=record_data.get("EngineVersion"), 
                description=record_data.get("EngineDesc"),
                disabled=record_data.get("EngineDisabled")
            )
        elif table_name == "ItemData":
            result = db.updateItemData(
                record_id,
                data_type=record_data.get("itemData"),
                value=record_data.get("itemDataValue"),
                sequence=record_data.get("itemDataSeq")
            )
        elif table_name == "Config":
            if "configValue" in record_data:
                db.addConfig(db.get_id(), record_data.get("configName", ""), record_data["configValue"])
                result = True
            else:
                result = False
        else:
            raise HTTPException(status_code=400, detail=f"Update not supported for table {table_name}")
        
        if result:
            return {"message": "Record updated successfully"}
        else:
            raise HTTPException(status_code=400, detail="No changes made to record")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/admin/tables/{table_name}/records")
async def create_record(
    table_name: str, 
    record_data: Dict[str, Any], 
    db: PeregrinDB = Depends(get_database)
):
    """Create a new record"""
    try:
        # Create record based on table type
        if table_name == "Items":
            item_id = db.addItem(
                record_data["EngineId"],
                record_data["ItemURI"], 
                datetime.now()
            )
            return {"message": "Record created", "id": item_id}
        elif table_name == "ItemData":
            db.addItemData(
                record_data["itemId"],
                record_data["itemData"],
                record_data.get("itemDataValue", ""),
                record_data.get("itemDataSeq", 0)
            )
            return {"message": "ItemData record created"}
        
        return {"message": f"Create for {table_name} not yet implemented"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/admin/tables/{table_name}/records/{record_id}")
async def delete_record(table_name: str, record_id: int, db: PeregrinDB = Depends(get_database)):
    """Delete a specific record"""
    try:
        result = db.deleteRecord(table_name, record_id)
        if result:
            return {"message": "Record deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Record not found or could not be deleted")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Engine-specific form configuration endpoints
@app.get("/api/admin/engines/forms")
async def get_engine_forms(db: PeregrinDB = Depends(get_database)):
    """Get form configurations for all engines"""
    try:
        forms = {
            "craigslist": {
                "title": "Craigslist Job Scraper",
                "description": "Scrapes job listings from Craigslist",
                "fields": {
                    "uri": {"type": "url", "label": "Base URI", "required": True, "default": "craigslist.ca"},
                    "keywords": {
                        "type": "array",
                        "label": "Search Keywords", 
                        "required": True,
                        "item_schema": {
                            "uriPrefix": {"type": "text", "label": "City", "default": "vancouver"},
                            "urlLang": {"type": "text", "label": "Language", "default": "en"},
                            "urlCountry": {"type": "text", "label": "Country", "default": "ca"},
                            "path": {"type": "text", "label": "Path", "default": "/search/"},
                            "query": {"type": "text", "label": "Search Query", "required": True},
                            "category": {"type": "text", "label": "Category", "default": "jjj"}
                        }
                    }
                },
                "actions": ["getItems", "getJobs"]
            },
            "webScraper": {
                "title": "Generic Web Scraper",
                "description": "Generic web page scraper",
                "fields": {
                    "uri": {"type": "url", "label": "Target URL", "required": True},
                    "selectors": {
                        "type": "array",
                        "label": "CSS Selectors",
                        "item_schema": {
                            "name": {"type": "text", "label": "Field Name", "required": True},
                            "selector": {"type": "text", "label": "CSS Selector", "required": True},
                            "attribute": {"type": "text", "label": "Attribute", "default": "text"}
                        }
                    }
                },
                "actions": ["scrape", "extract"]
            }
        }
        return {"forms": forms}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/engines/{engine_name}/form")
async def get_engine_form(engine_name: str, db: PeregrinDB = Depends(get_database)):
    """Get form configuration for specific engine"""
    try:
        forms = await get_engine_forms(db)
        if engine_name not in forms["forms"]:
            raise HTTPException(status_code=404, detail=f"Engine {engine_name} not found")
        
        return {"engine": engine_name, "form": forms["forms"][engine_name]}
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