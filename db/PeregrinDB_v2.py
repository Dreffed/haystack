#!/usr/bin/env python3
"""
Enhanced PeregrinDB with Connection Pooling and Proper Error Handling
This is the new version that replaces the original PeregrinDB.py
"""

import sys
import os
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple, Union
import configparser
from contextlib import contextmanager

# Add utils to path for logging
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.logging_config import get_logger, logging_context, log_performance
from db.database_pool import (
    DatabasePool, DatabasePoolManager, DatabaseConfig, 
    create_database_config, DatabaseError, ConnectionError, QueryError
)

logger = get_logger('database.peregrin')

class PeregrinDBError(Exception):
    """Base exception for PeregrinDB operations"""
    pass

class PeregrinDB:
    """
    Enhanced Peregrin Database interface with connection pooling
    Maintains backward compatibility with original PeregrinDB interface
    """
    
    def __init__(self):
        """Initialize the database interface"""
        self._pool: Optional[DatabasePool] = None
        self._title = 'PeregrinDB'
        self._version = '2.0'
        self._descr = 'Enhanced Peregrin Database Engine with Connection Pooling'
        self._engine_id = -1
        
        logger.debug("PeregrinDB v2 initialized")
    
    def __del__(self):
        """Cleanup database connections"""
        self.close_db()
    
    def info(self) -> Tuple[str, str, str]:
        """Returns the database interface information"""
        return (self._title, self._version, self._descr)
    
    def get_id(self) -> int:
        """Returns the engine id"""
        return self._engine_id
    
    def set_id(self, engine_id: int):
        """Sets the engine id"""
        self._engine_id = engine_id
    
    @log_performance("database_connect")
    def connect_db(self, config: Union[configparser.ConfigParser, Dict[str, Any]]):
        """
        Connect to the database using connection pooling
        
        Args:
            config: Configuration object or dictionary with database settings
        """
        try:
            with logging_context(operation="database_connect"):
                logger.info("Connecting to database with connection pooling")
                
                # Create database configuration
                db_config = create_database_config(config)
                
                # Get or create connection pool
                self._pool = DatabasePoolManager.get_pool(db_config, "peregrin")
                
                # Test connection
                if not self._pool.health_check():
                    raise ConnectionError("Database health check failed")
                
                # Initialize engine entry
                self._engine_id = self.addEngine(self._title, self._version, self._descr)
                
                logger.info(f"Database connected successfully - Engine ID: {self._engine_id}")
                
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise PeregrinDBError(f"Failed to connect to database: {e}")
    
    def commit_db(self):
        """Commit database transactions (handled automatically by connection pool)"""
        # Connection pool handles commits automatically, but keep for compatibility
        logger.debug("Database commit requested (handled by connection pool)")
    
    def close_db(self):
        """Close database connections"""
        if self._pool:
            try:
                # Don't actually close the pool as it may be shared
                # Pool cleanup is handled by DatabasePoolManager
                logger.info("Database connection closed")
            except Exception as e:
                logger.error(f"Error closing database connection: {e}")
            finally:
                self._pool = None
    
    def _ensure_connected(self):
        """Ensure database is connected"""
        if not self._pool:
            raise PeregrinDBError("Database not connected. Call connect_db() first.")
    
    @log_performance("add_status")
    def addStatus(self, engine_id: int, action_id: int, message: str):
        """Add a status message to the system"""
        self._ensure_connected()
        
        try:
            with logging_context(operation="add_status", engine_id=engine_id):
                query = """
                    INSERT INTO Status (engineId, actionId, StatusMessage, StatusDate) 
                    VALUES (:engine_id, :action_id, :message, :status_date)
                """
                params = {
                    'engine_id': engine_id,
                    'action_id': action_id,
                    'message': message,
                    'status_date': datetime.now()
                }
                
                self._pool.execute_insert(query, params)
                logger.debug(f"Status added for engine {engine_id}: {message}")
                
        except Exception as e:
            logger.error(f"Failed to add status: {e}")
            raise PeregrinDBError(f"Failed to add status: {e}")
    
    @log_performance("get_status")
    def getStatus(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """Returns recent status messages"""
        self._ensure_connected()
        
        try:
            with logging_context(operation="get_status"):
                query = """
                    SELECT statusId, EngineId, ActionId, StatusMessage, StatusDate 
                    FROM Status 
                    ORDER BY StatusDate DESC 
                    LIMIT :limit
                """
                
                result = self._pool.execute_query(query, {'limit': limit})
                logger.debug(f"Retrieved {len(result)} status messages")
                return result
                
        except Exception as e:
            logger.error(f"Failed to get status: {e}")
            raise PeregrinDBError(f"Failed to get status: {e}")
    
    @log_performance("add_config")
    def addConfig(self, engine_id: int, config_name: str, config_value: str):
        """Add or update a configuration value"""
        self._ensure_connected()
        
        try:
            with logging_context(operation="add_config", engine_id=engine_id):
                # Check if config exists
                check_query = "SELECT configValue FROM Config WHERE configName = :config_name"
                existing = self._pool.execute_query(check_query, {'config_name': config_name})
                
                action_id = self.addAction('config')
                
                if not existing:
                    # Insert new config
                    self.addStatus(engine_id, action_id, f'CONFIG NEW: {config_name} = {config_value}')
                    insert_query = "INSERT INTO Config (configName, configValue) VALUES (:name, :value)"
                    self._pool.execute_insert(insert_query, {'name': config_name, 'value': config_value})
                    logger.info(f"New configuration added: {config_name} = {config_value}")
                    
                else:
                    old_value = existing[0]['configValue']
                    if old_value != config_value:
                        # Update existing config
                        self.addStatus(engine_id, action_id, f'CONFIG CHANGE: {config_name}: {old_value} -> {config_value}')
                        update_query = "UPDATE Config SET configValue = :value WHERE configName = :name"
                        self._pool.execute_update(update_query, {'value': config_value, 'name': config_name})
                        logger.info(f"Configuration updated: {config_name} = {config_value}")
                        
        except Exception as e:
            logger.error(f"Failed to add/update config {config_name}: {e}")
            raise PeregrinDBError(f"Failed to add/update config: {e}")
    
    @log_performance("get_config")
    def getConfig(self, config_name: str) -> str:
        """Get a configuration value"""
        self._ensure_connected()
        
        try:
            with logging_context(operation="get_config"):
                query = "SELECT configValue FROM Config WHERE configName = :config_name"
                result = self._pool.execute_query(query, {'config_name': config_name})
                
                if result:
                    value = result[0]['configValue']
                    logger.debug(f"Configuration retrieved: {config_name} = {value}")
                    return value
                else:
                    logger.debug(f"Configuration not found: {config_name}")
                    return 'n/a'
                    
        except Exception as e:
            logger.error(f"Failed to get config {config_name}: {e}")
            raise PeregrinDBError(f"Failed to get config: {e}")
    
    @log_performance("add_engine")
    def addEngine(self, engine_title: str, engine_version: str, engine_descr: str) -> int:
        """Add or get an engine entry"""
        self._ensure_connected()
        
        try:
            with logging_context(operation="add_engine", engine_name=engine_title):
                # Check if engine exists
                check_query = """
                    SELECT EngineId FROM Engines 
                    WHERE EngineName = :name AND EngineVersion = :version
                """
                existing = self._pool.execute_query(check_query, {
                    'name': engine_title, 
                    'version': engine_version
                })
                
                if existing:
                    engine_id = existing[0]['EngineId']
                    logger.debug(f"Existing engine found: {engine_title} v{engine_version} (ID: {engine_id})")
                    return engine_id
                else:
                    # Insert new engine
                    insert_query = """
                        INSERT INTO Engines (EngineName, EngineVersion, EngineDesc) 
                        VALUES (:name, :version, :description)
                    """
                    engine_id = self._pool.execute_insert(insert_query, {
                        'name': engine_title,
                        'version': engine_version,
                        'description': engine_descr
                    })
                    logger.info(f"New engine added: {engine_title} v{engine_version} (ID: {engine_id})")
                    return engine_id
                    
        except Exception as e:
            logger.error(f"Failed to add engine {engine_title}: {e}")
            raise PeregrinDBError(f"Failed to add engine: {e}")
    
    @log_performance("add_action")
    def addAction(self, action_name: str) -> int:
        """Add or get an action entry"""
        self._ensure_connected()
        
        try:
            with logging_context(operation="add_action"):
                # Check if action exists
                check_query = "SELECT actionId FROM Actions WHERE actionName = :action_name"
                existing = self._pool.execute_query(check_query, {'action_name': action_name})
                
                if existing:
                    action_id = existing[0]['actionId']
                    logger.debug(f"Existing action found: {action_name} (ID: {action_id})")
                    return action_id
                else:
                    # Insert new action
                    insert_query = "INSERT INTO Actions (actionName) VALUES (:action_name)"
                    action_id = self._pool.execute_insert(insert_query, {'action_name': action_name})
                    logger.debug(f"New action added: {action_name} (ID: {action_id})")
                    return action_id
                    
        except Exception as e:
            logger.error(f"Failed to add action {action_name}: {e}")
            raise PeregrinDBError(f"Failed to add action: {e}")
    
    @log_performance("add_item")
    def addItem(self, engine_id: int, item_uri: str, item_date: datetime, *args) -> int:
        """Add an item to the database"""
        self._ensure_connected()
        
        try:
            with logging_context(operation="add_item", engine_id=engine_id):
                # Check if item exists
                check_query = "SELECT itemId FROM Items WHERE ItemURI = :item_uri"
                existing = self._pool.execute_query(check_query, {'item_uri': item_uri})
                
                if existing:
                    item_id = existing[0]['itemId']
                    logger.debug(f"Existing item found: {item_uri} (ID: {item_id})")
                else:
                    # Insert new item
                    insert_query = """
                        INSERT INTO Items (ItemURI, EngineId, ItemDTS) 
                        VALUES (:item_uri, :engine_id, :item_date)
                    """
                    item_id = self._pool.execute_insert(insert_query, {
                        'item_uri': item_uri,
                        'engine_id': engine_id,
                        'item_date': item_date
                    })
                    logger.debug(f"New item added: {item_uri} (ID: {item_id})")
                
                # Add actions for the item
                for action_list in args:
                    for action_name in action_list:
                        action_id = self.addAction(action_name)
                        self.addItemEvent(engine_id, action_id, item_id)
                
                return item_id
                
        except Exception as e:
            logger.error(f"Failed to add item {item_uri}: {e}")
            raise PeregrinDBError(f"Failed to add item: {e}")
    
    @log_performance("get_item_uri")
    def getItemURI(self, item_id: int) -> str:
        """Get item URI by ID"""
        self._ensure_connected()
        
        try:
            with logging_context(operation="get_item_uri", item_id=item_id):
                query = "SELECT itemURI FROM Items WHERE ItemId = :item_id"
                result = self._pool.execute_query(query, {'item_id': item_id})
                
                if result:
                    uri = result[0]['itemURI']
                    logger.debug(f"Item URI retrieved for ID {item_id}: {uri}")
                    return uri
                else:
                    logger.warning(f"Item not found: {item_id}")
                    return ''
                    
        except Exception as e:
            logger.error(f"Failed to get item URI for ID {item_id}: {e}")
            raise PeregrinDBError(f"Failed to get item URI: {e}")
    
    @log_performance("add_item_data")
    def addItemData(self, item_id: int, item_data: str, item_data_value: str, item_data_seq: int):
        """Add data for an item"""
        self._ensure_connected()
        
        try:
            with logging_context(operation="add_item_data", item_id=item_id):
                # Check if item data exists
                check_query = """
                    SELECT ItemDataId FROM ItemData 
                    WHERE ItemId = :item_id AND ItemData = :item_data AND ItemDataSeq = :item_data_seq
                """
                existing = self._pool.execute_query(check_query, {
                    'item_id': item_id,
                    'item_data': item_data,
                    'item_data_seq': item_data_seq
                })
                
                if existing:
                    data_id = existing[0]['ItemDataId']
                    logger.debug(f"Existing item data found: {item_data} (ID: {data_id})")
                    return data_id
                else:
                    # Insert new item data
                    insert_query = """
                        INSERT INTO ItemData (itemId, itemData, itemDataValue, itemDataSeq, itemDataAdded) 
                        VALUES (:item_id, :item_data, :item_data_value, :item_data_seq, :item_data_added)
                    """
                    data_id = self._pool.execute_insert(insert_query, {
                        'item_id': item_id,
                        'item_data': item_data,
                        'item_data_value': item_data_value,
                        'item_data_seq': item_data_seq,
                        'item_data_added': datetime.now()
                    })
                    logger.debug(f"New item data added: {item_data} = {item_data_value} (ID: {data_id})")
                    return data_id
                    
        except Exception as e:
            logger.error(f"Failed to add item data for item {item_id}: {e}")
            raise PeregrinDBError(f"Failed to add item data: {e}")
    
    @log_performance("get_item_data_all")
    def getItemDataAll(self, item_id: int) -> List[Tuple[str, str]]:
        """Get all data for an item"""
        self._ensure_connected()
        
        try:
            with logging_context(operation="get_item_data_all", item_id=item_id):
                query = """
                    SELECT itemData, itemDataValue 
                    FROM ItemData 
                    WHERE ItemId = :item_id 
                    ORDER BY itemDataAdded
                """
                result = self._pool.execute_query(query, {'item_id': item_id})
                
                # Convert to list of tuples for backward compatibility
                data_list = [(row['itemData'], row['itemDataValue']) for row in result]
                logger.debug(f"Retrieved {len(data_list)} data items for item {item_id}")
                return data_list
                
        except Exception as e:
            logger.error(f"Failed to get item data for item {item_id}: {e}")
            raise PeregrinDBError(f"Failed to get item data: {e}")
    
    @log_performance("add_item_event")
    def addItemEvent(self, engine_id: int, action_id: int, item_id: int) -> int:
        """Add an item event"""
        self._ensure_connected()
        
        try:
            with logging_context(operation="add_item_event", engine_id=engine_id, item_id=item_id):
                # Check if event exists
                check_query = """
                    SELECT ItemEventId FROM ItemEvents 
                    WHERE engineId = :engine_id AND actionId = :action_id AND ItemId = :item_id
                """
                existing = self._pool.execute_query(check_query, {
                    'engine_id': engine_id,
                    'action_id': action_id,
                    'item_id': item_id
                })
                
                if existing:
                    event_id = existing[0]['ItemEventId']
                    logger.debug(f"Existing item event found (ID: {event_id})")
                    return event_id
                else:
                    # Insert new item event
                    insert_query = """
                        INSERT INTO ItemEvents (engineId, actionId, itemId, itemEventAddedDate) 
                        VALUES (:engine_id, :action_id, :item_id, :item_event_added_date)
                    """
                    event_id = self._pool.execute_insert(insert_query, {
                        'engine_id': engine_id,
                        'action_id': action_id,
                        'item_id': item_id,
                        'item_event_added_date': datetime.now()
                    })
                    logger.debug(f"New item event added (ID: {event_id})")
                    return event_id
                    
        except Exception as e:
            logger.error(f"Failed to add item event: {e}")
            raise PeregrinDBError(f"Failed to add item event: {e}")
    
    @log_performance("update_item")
    def updateItem(self, engine_id: int, item_id: int, action_id: int, item_event_date: datetime) -> bool:
        """Update an item event with completion date"""
        self._ensure_connected()
        
        try:
            with logging_context(operation="update_item", engine_id=engine_id, item_id=item_id):
                # Check if event exists
                check_query = """
                    SELECT ItemEventId FROM ItemEvents 
                    WHERE engineId = :engine_id AND actionId = :action_id AND ItemId = :item_id
                """
                existing = self._pool.execute_query(check_query, {
                    'engine_id': engine_id,
                    'action_id': action_id,
                    'item_id': item_id
                })
                
                if not existing:
                    # Create new event
                    insert_query = """
                        INSERT INTO ItemEvents (itemEventDate, engineId, itemId, actionId, ItemEventAddedDate) 
                        VALUES (:item_event_date, :engine_id, :item_id, :action_id, :item_event_added_date)
                    """
                    self._pool.execute_insert(insert_query, {
                        'item_event_date': item_event_date,
                        'engine_id': engine_id,
                        'item_id': item_id,
                        'action_id': action_id,
                        'item_event_added_date': datetime.now()
                    })
                    logger.debug(f"New item event created and updated for item {item_id}")
                else:
                    # Update existing event
                    update_query = """
                        UPDATE ItemEvents 
                        SET itemEventDate = :item_event_date 
                        WHERE engineId = :engine_id AND itemId = :item_id AND actionId = :action_id
                    """
                    self._pool.execute_update(update_query, {
                        'item_event_date': item_event_date,
                        'engine_id': engine_id,
                        'item_id': item_id,
                        'action_id': action_id
                    })
                    logger.debug(f"Item event updated for item {item_id}")
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to update item {item_id}: {e}")
            return False
    
    @log_performance("get_item_list")
    def getItemList(self, engine_id: int, action_name: str, find_others: bool = False, time_span: int = -3) -> List[Tuple[int, str]]:
        """Get list of items for processing"""
        self._ensure_connected()
        
        try:
            with logging_context(operation="get_item_list", engine_id=engine_id):
                action_id = self.addAction(action_name)
                
                if find_others:
                    query = """
                        SELECT i.ItemID AS ItemID, ItemURI
                        FROM Items i 
                        INNER JOIN ItemEvents e ON i.itemId = e.itemId AND e.actionId = :action_id
                        WHERE i.ItemId NOT IN (
                            SELECT ItemId FROM ItemEvents ie
                            WHERE ie.ItemEventDate IS NOT NULL
                            AND ie.actionId = :action_id
                            AND ie.engineId = :engine_id
                        )
                        AND e.ItemEventAddedDate >= DATE_ADD(NOW(), INTERVAL :time_span MONTH)
                        GROUP BY i.ItemID, ItemURI
                    """
                else:
                    query = """
                        SELECT i.ItemID AS ItemID, ItemURI
                        FROM Items i 
                        INNER JOIN ItemEvents e ON i.itemId = e.itemId 
                            AND e.actionId = :action_id AND e.engineId = :engine_id
                        WHERE e.ItemEventAddedDate >= DATE_ADD(NOW(), INTERVAL :time_span MONTH)
                        AND e.ItemEventDate IS NULL
                    """
                
                result = self._pool.execute_query(query, {
                    'action_id': action_id,
                    'engine_id': engine_id,
                    'time_span': time_span
                })
                
                items = [(row['ItemID'], row['ItemURI']) for row in result]
                logger.debug(f"Retrieved {len(items)} items for processing")
                return items
                
        except Exception as e:
            logger.error(f"Failed to get item list: {e}")
            raise PeregrinDBError(f"Failed to get item list: {e}")
    
    def get_pool_status(self) -> Dict[str, Any]:
        """Get database pool status for monitoring"""
        if self._pool:
            return self._pool.get_pool_status()
        else:
            return {"status": "not_connected"}

    # Admin interface methods
    def getEngines(self, limit=100, offset=0):
        """Get all engines with pagination"""
        try:
            with self.get_session() as session:
                result = session.execute(
                    text("""
                        SELECT EngineId, EngineName, EngineVersion, EngineDesc, 
                               EngineDisabled, EngineCreated
                        FROM Engines
                        ORDER BY EngineCreated DESC
                        LIMIT :limit OFFSET :offset
                    """),
                    {"limit": limit, "offset": offset}
                )
                
                return [dict(row._mapping) for row in result]
                
        except Exception as e:
            logger.error(f"Error getting engines: {e}")
            raise PeregrinDBError(f"Failed to get engines: {e}")

    def getItems(self, limit=100, offset=0, engine_id=None):
        """Get items with pagination and optional engine filter"""
        try:
            with self.get_session() as session:
                where_clause = ""
                params = {"limit": limit, "offset": offset}
                
                if engine_id:
                    where_clause = "WHERE i.EngineId = :engine_id"
                    params["engine_id"] = engine_id
                
                result = session.execute(
                    text(f"""
                        SELECT i.itemId, i.ItemURI, i.EngineId, i.ItemDTS, i.itemCreated,
                               e.EngineName
                        FROM Items i
                        LEFT JOIN Engines e ON i.EngineId = e.EngineId
                        {where_clause}
                        ORDER BY i.itemCreated DESC
                        LIMIT :limit OFFSET :offset
                    """),
                    params
                )
                
                return [dict(row._mapping) for row in result]
                
        except Exception as e:
            logger.error(f"Error getting items: {e}")
            raise PeregrinDBError(f"Failed to get items: {e}")

    def getItemDataPaginated(self, limit=100, offset=0, item_id=None):
        """Get item data with pagination and optional item filter"""
        try:
            with self.get_session() as session:
                where_clause = ""
                params = {"limit": limit, "offset": offset}
                
                if item_id:
                    where_clause = "WHERE id.itemId = :item_id"
                    params["item_id"] = item_id
                
                result = session.execute(
                    text(f"""
                        SELECT id.ItemDataId, id.itemId, id.itemData, id.itemDataValue, 
                               id.itemDataSeq, id.itemDataAdded, i.ItemURI
                        FROM ItemData id
                        LEFT JOIN Items i ON id.itemId = i.itemId
                        {where_clause}
                        ORDER BY id.itemDataAdded DESC
                        LIMIT :limit OFFSET :offset
                    """),
                    params
                )
                
                return [dict(row._mapping) for row in result]
                
        except Exception as e:
            logger.error(f"Error getting item data: {e}")
            raise PeregrinDBError(f"Failed to get item data: {e}")

    def getActions(self, limit=100, offset=0):
        """Get all actions with pagination"""
        try:
            with self.get_session() as session:
                result = session.execute(
                    text("""
                        SELECT actionId, actionName, actionDesc, actionCreated
                        FROM Actions
                        ORDER BY actionCreated DESC
                        LIMIT :limit OFFSET :offset
                    """),
                    {"limit": limit, "offset": offset}
                )
                
                return [dict(row._mapping) for row in result]
                
        except Exception as e:
            logger.error(f"Error getting actions: {e}")
            raise PeregrinDBError(f"Failed to get actions: {e}")

    def getAllConfig(self, limit=100, offset=0):
        """Get all configuration values with pagination"""
        try:
            with self.get_session() as session:
                result = session.execute(
                    text("""
                        SELECT configId, configName, configValue, configUpdated
                        FROM Config
                        ORDER BY configUpdated DESC
                        LIMIT :limit OFFSET :offset
                    """),
                    {"limit": limit, "offset": offset}
                )
                
                return [dict(row._mapping) for row in result]
                
        except Exception as e:
            logger.error(f"Error getting config: {e}")
            raise PeregrinDBError(f"Failed to get config: {e}")

    def getTableCount(self, table_name):
        """Get total count of records in a table"""
        try:
            with self.get_session() as session:
                result = session.execute(
                    text(f"SELECT COUNT(*) as count FROM {table_name}")
                )
                
                return result.fetchone()[0]
                
        except Exception as e:
            logger.error(f"Error getting table count for {table_name}: {e}")
            raise PeregrinDBError(f"Failed to get table count: {e}")

    def searchTable(self, table_name, search_term, limit=100, offset=0):
        """Search within a table for matching records"""
        try:
            with self.get_session() as session:
                # Define searchable columns for each table
                search_columns = {
                    "Engines": ["EngineName", "EngineDesc"],
                    "Items": ["ItemURI"],
                    "ItemData": ["itemData", "itemDataValue"],
                    "Actions": ["actionName", "actionDesc"],
                    "Config": ["configName", "configValue"],
                    "Status": ["StatusMessage"]
                }
                
                if table_name not in search_columns:
                    raise PeregrinDBError(f"Search not supported for table {table_name}")
                
                columns = search_columns[table_name]
                search_conditions = " OR ".join([f"{col} LIKE :search" for col in columns])
                
                result = session.execute(
                    text(f"""
                        SELECT * FROM {table_name}
                        WHERE {search_conditions}
                        LIMIT :limit OFFSET :offset
                    """),
                    {"search": f"%{search_term}%", "limit": limit, "offset": offset}
                )
                
                return [dict(row._mapping) for row in result]
                
        except Exception as e:
            logger.error(f"Error searching table {table_name}: {e}")
            raise PeregrinDBError(f"Failed to search table: {e}")

    def updateEngine(self, engine_id, name=None, version=None, description=None, disabled=None):
        """Update an engine record"""
        try:
            with self.get_session() as session:
                updates = []
                params = {"engine_id": engine_id}
                
                if name is not None:
                    updates.append("EngineName = :name")
                    params["name"] = name
                if version is not None:
                    updates.append("EngineVersion = :version")
                    params["version"] = version
                if description is not None:
                    updates.append("EngineDesc = :description")
                    params["description"] = description
                if disabled is not None:
                    updates.append("EngineDisabled = :disabled")
                    params["disabled"] = disabled
                
                if not updates:
                    return False
                
                session.execute(
                    text(f"""
                        UPDATE Engines 
                        SET {', '.join(updates)}
                        WHERE EngineId = :engine_id
                    """),
                    params
                )
                
                return True
                
        except Exception as e:
            logger.error(f"Error updating engine: {e}")
            raise PeregrinDBError(f"Failed to update engine: {e}")

    def updateItemData(self, item_data_id, data_type=None, value=None, sequence=None):
        """Update an item data record"""
        try:
            with self.get_session() as session:
                updates = []
                params = {"item_data_id": item_data_id}
                
                if data_type is not None:
                    updates.append("itemData = :data_type")
                    params["data_type"] = data_type
                if value is not None:
                    updates.append("itemDataValue = :value")
                    params["value"] = value
                if sequence is not None:
                    updates.append("itemDataSeq = :sequence")
                    params["sequence"] = sequence
                
                if not updates:
                    return False
                
                session.execute(
                    text(f"""
                        UPDATE ItemData 
                        SET {', '.join(updates)}
                        WHERE ItemDataId = :item_data_id
                    """),
                    params
                )
                
                return True
                
        except Exception as e:
            logger.error(f"Error updating item data: {e}")
            raise PeregrinDBError(f"Failed to update item data: {e}")

    def deleteRecord(self, table_name, record_id, id_column=None):
        """Delete a record from a table"""
        try:
            with self.get_session() as session:
                # Map tables to their primary key columns
                primary_keys = {
                    "Engines": "EngineId",
                    "Items": "itemId",
                    "ItemData": "ItemDataId",
                    "Actions": "actionId",
                    "Config": "configId",
                    "Status": "statusId"
                }
                
                pk_column = id_column or primary_keys.get(table_name)
                if not pk_column:
                    raise PeregrinDBError(f"Unknown primary key for table {table_name}")
                
                result = session.execute(
                    text(f"DELETE FROM {table_name} WHERE {pk_column} = :record_id"),
                    {"record_id": record_id}
                )
                
                return result.rowcount > 0
                
        except Exception as e:
            logger.error(f"Error deleting record from {table_name}: {e}")
            raise PeregrinDBError(f"Failed to delete record: {e}")


# Backward compatibility - create alias
PeregrinDatabase = PeregrinDB

def main():
    """Test the enhanced PeregrinDB"""
    import tempfile
    
    # Set up logging
    from utils.logging_config import setup_logging
    setup_logging(log_level="DEBUG")
    
    # Create test database configuration
    config = configparser.RawConfigParser()
    config.add_section('Database')
    config.set('Database', 'Server', os.getenv('DB_HOST', 'localhost'))
    config.set('Database', 'User', os.getenv('DB_USER', 'peregrin'))
    config.set('Database', 'Password', os.getenv('DB_PASSWORD', 'peregrin_pass_2023'))
    config.set('Database', 'Schema', os.getenv('DB_NAME', 'Peregrin'))
    
    try:
        # Test the database
        db = PeregrinDB()
        db.connect_db(config)
        
        print(f"Database Info: {db.info()}")
        print(f"Engine ID: {db.get_id()}")
        print(f"Pool Status: {db.get_pool_status()}")
        
        # Test basic operations
        action_id = db.addAction('test_action')
        db.addStatus(db.get_id(), action_id, 'Test message from enhanced PeregrinDB')
        
        status_messages = db.getStatus(limit=5)
        print(f"Recent status messages: {status_messages}")
        
        print("✅ Enhanced PeregrinDB test completed successfully")
        
    except Exception as e:
        print(f"❌ Enhanced PeregrinDB test failed: {e}")
        return 1
    
    return 0



if __name__ == '__main__':
    sys.exit(main())