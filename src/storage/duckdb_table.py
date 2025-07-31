"""DuckDB-based table storage implementation."""

import json
from typing import Any, Dict, List, Optional, Type
from uuid import UUID

import duckdb
from pydantic import BaseModel

from .abstractions import AbstractTableStorage


class DuckDBTableStorage(AbstractTableStorage):
    """DuckDB-based implementation of table storage."""
    
    def __init__(
        self, 
        model_class: Type[BaseModel], 
        database_path: str = ":memory:",
        table_name: Optional[str] = None
    ) -> None:
        """Initialize DuckDB table storage.
        
        Args:
            model_class: The Pydantic model class
            database_path: Path to DuckDB database file (":memory:" for in-memory)
            table_name: Custom table name (defaults to model class name)
        """
        super().__init__(model_class)
        self._database_path = database_path
        self._table_name = table_name or model_class.__name__.lower()
        self._connection = duckdb.connect(database_path)
        
        # Create table schema based on Pydantic model
        self._create_table_if_not_exists()
    
    def _create_table_if_not_exists(self) -> None:
        """Create table schema based on Pydantic model."""
        # For simplicity, store as JSON in a single column with ID index
        # Production implementation would map Pydantic fields to columns
        create_sql = f"""
            CREATE TABLE IF NOT EXISTS {self._table_name} (
                id UUID PRIMARY KEY,
                data JSON NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        self._connection.execute(create_sql)
        
        # Create index on commonly queried fields (extracted from JSON)
        index_sqls = [
            f"CREATE INDEX IF NOT EXISTS idx_{self._table_name}_status ON {self._table_name} ((data ->> 'status'))",
            f"CREATE INDEX IF NOT EXISTS idx_{self._table_name}_priority ON {self._table_name} ((data ->> 'priority'))",
            f"CREATE INDEX IF NOT EXISTS idx_{self._table_name}_category ON {self._table_name} ((data ->> 'category'))"
        ]
        
        for sql in index_sqls:
            try:
                self._connection.execute(sql)
            except Exception:
                # Index might already exist or field might not be applicable
                pass
    
    async def create(self, item: BaseModel) -> BaseModel:
        """Create new item in DuckDB table."""
        # Check if item already exists
        if await self.exists(item.id):
            raise ValueError(f"Item with ID {item.id} already exists")
        
        # Insert item
        item_json = item.model_dump_json()
        insert_sql = f"""
            INSERT INTO {self._table_name} (id, data)
            VALUES (?, ?)
        """
        
        self._connection.execute(insert_sql, [str(item.id), item_json])
        return item
    
    async def get_by_id(self, item_id: UUID) -> Optional[BaseModel]:
        """Retrieve item by ID."""
        select_sql = f"""
            SELECT data FROM {self._table_name}
            WHERE id = ?
        """
        
        result = self._connection.execute(select_sql, [str(item_id)]).fetchone()
        if not result:
            return None
        
        # Deserialize JSON back to Pydantic model
        item_data = json.loads(result[0])
        return self.model_class.model_validate(item_data)
    
    async def list_all(self) -> List[BaseModel]:
        """Get all items."""
        select_sql = f"SELECT data FROM {self._table_name} ORDER BY created_at"
        
        results = self._connection.execute(select_sql).fetchall()
        items = []
        
        for result in results:
            item_data = json.loads(result[0])
            items.append(self.model_class.model_validate(item_data))
        
        return items
    
    async def update(self, item: BaseModel) -> BaseModel:
        """Update existing item."""
        # Check if item exists
        if not await self.exists(item.id):
            raise ValueError(f"Item with ID {item.id} doesn't exist")
        
        # Update item
        item_json = item.model_dump_json()
        update_sql = f"""
            UPDATE {self._table_name} 
            SET data = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """
        
        self._connection.execute(update_sql, [item_json, str(item.id)])
        return item
    
    async def delete(self, item_id: UUID) -> bool:
        """Delete item by ID."""
        # First check if item exists
        if not await self.exists(item_id):
            return False
        
        delete_sql = f"DELETE FROM {self._table_name} WHERE id = ?"
        self._connection.execute(delete_sql, [str(item_id)])
        return True
    
    async def query(self, filters: Dict[str, Any]) -> List[BaseModel]:
        """Query items with filters using JSON path expressions."""
        if not filters:
            return await self.list_all()
        
        # Build WHERE clause using JSON path expressions
        where_conditions = []
        params = []
        
        for field, value in filters.items():
            # Use CAST to ensure string comparison for JSON fields
            where_conditions.append(f"CAST(data ->> '{field}' AS VARCHAR) = ?")
            
            if hasattr(value, 'value'):
                # Handle enum values
                params.append(str(value.value))
            else:
                # Convert all other values to string
                params.append(str(value) if value is not None else None)
        
        where_clause = " AND ".join(where_conditions)
        select_sql = f"""
            SELECT data FROM {self._table_name}
            WHERE {where_clause}
            ORDER BY created_at
        """
        
        results = self._connection.execute(select_sql, params).fetchall()
        items = []
        
        for result in results:
            item_data = json.loads(result[0])
            items.append(self.model_class.model_validate(item_data))
        
        return items
    
    async def count(self) -> int:
        """Get total count of items."""
        count_sql = f"SELECT COUNT(*) FROM {self._table_name}"
        result = self._connection.execute(count_sql).fetchone()
        return result[0] if result else 0
    
    async def exists(self, item_id: UUID) -> bool:
        """Check if item exists."""
        exists_sql = f"SELECT 1 FROM {self._table_name} WHERE id = ? LIMIT 1"
        result = self._connection.execute(exists_sql, [str(item_id)]).fetchone()
        return result is not None
    
    async def clear(self) -> None:
        """Remove all items from storage."""
        clear_sql = f"DELETE FROM {self._table_name}"
        self._connection.execute(clear_sql)
    
    # Additional DuckDB-specific methods
    
    async def query_sql(self, sql: str, params: Optional[List] = None) -> List[Dict]:
        """Execute raw SQL query and return results as dictionaries."""
        if params is None:
            params = []
        
        # Add table name validation to prevent SQL injection
        if self._table_name not in sql.lower():
            raise ValueError("SQL query must reference the correct table")
        
        results = self._connection.execute(sql, params).fetchall()
        columns = [desc[0] for desc in self._connection.description]
        
        return [dict(zip(columns, row)) for row in results]
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get table statistics."""
        stats_sql = f"""
            SELECT 
                COUNT(*) as total_count,
                MIN(created_at) as earliest_created,
                MAX(created_at) as latest_created,
                MAX(updated_at) as latest_updated
            FROM {self._table_name}
        """
        
        result = self._connection.execute(stats_sql).fetchone()
        if not result:
            return {
                "total_count": 0,
                "earliest_created": None,
                "latest_created": None,
                "latest_updated": None
            }
        
        return {
            "total_count": result[0],
            "earliest_created": result[1],
            "latest_created": result[2], 
            "latest_updated": result[3]
        }
    
    async def bulk_insert(self, items: List[BaseModel]) -> List[BaseModel]:
        """Bulk insert multiple items for better performance."""
        if not items:
            return []
        
        # Prepare bulk insert data
        insert_data = []
        for item in items:
            if await self.exists(item.id):
                raise ValueError(f"Item with ID {item.id} already exists")
            insert_data.append([str(item.id), item.model_dump_json()])
        
        # Execute bulk insert
        insert_sql = f"""
            INSERT INTO {self._table_name} (id, data)
            VALUES (?, ?)
        """
        
        self._connection.executemany(insert_sql, insert_data)
        return items
    
    async def create_backup(self, backup_path: str) -> None:
        """Create backup of the table."""
        backup_sql = f"""
            COPY {self._table_name} TO '{backup_path}' (FORMAT PARQUET)
        """
        self._connection.execute(backup_sql)
    
    async def optimize_table(self) -> None:
        """Optimize table performance."""
        # Analyze table for better query planning
        analyze_sql = f"ANALYZE {self._table_name}"
        self._connection.execute(analyze_sql)
        
        # Vacuum if needed (not applicable to DuckDB, but could checkpoint)
        checkpoint_sql = "CHECKPOINT"
        self._connection.execute(checkpoint_sql)
    
    def close(self) -> None:
        """Close database connection."""
        if self._connection:
            self._connection.close()
    
    def __del__(self) -> None:
        """Cleanup on object destruction."""
        self.close()