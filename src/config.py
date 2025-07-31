"""Configuration management for the Advanced Task Manager."""

import os
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class DatabaseConfig(BaseModel):
    """Database configuration settings."""
    
    path: str = Field(default="tasks.db", description="Path to DuckDB database file")
    backup_enabled: bool = Field(default=True, description="Enable automatic backups")
    backup_interval_hours: int = Field(default=24, description="Backup interval in hours")
    optimize_on_startup: bool = Field(default=True, description="Optimize database on startup")


class ServerConfig(BaseModel):
    """MCP server configuration settings."""
    
    name: str = Field(default="advanced-task-manager", description="Server name")
    version: str = Field(default="1.0.0", description="Server version")
    log_level: str = Field(default="INFO", description="Logging level")
    max_tasks_per_query: int = Field(default=1000, description="Maximum tasks returned per query")


class StorageConfig(BaseModel):
    """Storage backend configuration."""
    
    enable_graph_cache: bool = Field(default=True, description="Enable graph storage caching")
    max_graph_nodes: int = Field(default=10000, description="Maximum nodes in graph")
    enable_table_indexes: bool = Field(default=True, description="Enable table indexes")
    bulk_insert_batch_size: int = Field(default=100, description="Batch size for bulk operations")


class UIConfig(BaseModel):
    """User interface configuration."""
    
    cli_colors: bool = Field(default=True, description="Enable CLI colors")
    progress_bars: bool = Field(default=True, description="Show progress bars")
    table_max_width: int = Field(default=120, description="Maximum table width in CLI")
    auto_wrap_text: bool = Field(default=True, description="Auto-wrap long text")


class TaskManagerConfig(BaseSettings):
    """Main configuration class for the Task Manager."""
    
    # Configuration sections
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    ui: UIConfig = Field(default_factory=UIConfig)
    
    # Global settings
    debug: bool = Field(default=False, description="Enable debug mode")
    data_dir: str = Field(default="./data", description="Data directory path")
    config_file: Optional[str] = Field(default=None, description="Path to config file")
    
    model_config = {
        "env_prefix": "TASK_MANAGER_",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore"
    }
    
    def __init__(self, **kwargs):
        """Initialize configuration with environment variables and defaults."""
        super().__init__(**kwargs)
        
        # Ensure data directory exists
        Path(self.data_dir).mkdir(parents=True, exist_ok=True)
        
        # Update database path if relative
        if not os.path.isabs(self.database.path):
            self.database.path = os.path.join(self.data_dir, self.database.path)
    
    @classmethod
    def from_file(cls, config_path: str) -> "TaskManagerConfig":
        """Load configuration from a TOML file."""
        import tomllib
        
        with open(config_path, 'rb') as f:
            config_data = tomllib.load(f)
        
        return cls(**config_data)
    
    def save_to_file(self, config_path: str) -> None:
        """Save current configuration to a TOML file."""
        import tomli_w
        
        config_dict = self.model_dump()
        
        with open(config_path, 'wb') as f:
            tomli_w.dump(config_dict, f)
    
    def get_database_url(self) -> str:
        """Get the database connection URL."""
        return self.database.path
    
    def get_log_level(self) -> str:
        """Get the configured log level."""
        return self.server.log_level.upper()
    
    def is_debug_mode(self) -> bool:
        """Check if debug mode is enabled."""
        return self.debug or self.server.log_level.upper() == "DEBUG"
    
    def get_backup_path(self) -> str:
        """Get the backup file path."""
        db_name = Path(self.database.path).stem
        return os.path.join(self.data_dir, f"{db_name}_backup.parquet")


# Global configuration instance
_config: Optional[TaskManagerConfig] = None


def get_config() -> TaskManagerConfig:
    """Get the global configuration instance."""
    global _config
    
    if _config is None:
        # Check for config file in environment
        config_file = os.getenv("TASK_MANAGER_CONFIG_FILE")
        
        if config_file and os.path.exists(config_file):
            _config = TaskManagerConfig.from_file(config_file)
        else:
            _config = TaskManagerConfig()
    
    return _config


def set_config(config: TaskManagerConfig) -> None:
    """Set the global configuration instance."""
    global _config
    _config = config


def reset_config() -> None:
    """Reset the global configuration to defaults."""
    global _config
    _config = None


# Environment variable mappings for common settings
ENVIRONMENT_MAPPINGS = {
    "TASK_DB_PATH": "database.path",
    "TASK_DEBUG": "debug",
    "TASK_LOG_LEVEL": "server.log_level",
    "TASK_DATA_DIR": "data_dir",
    "TASK_SERVER_NAME": "server.name",
    "TASK_MAX_TASKS": "server.max_tasks_per_query",
}


def get_config_from_env() -> TaskManagerConfig:
    """Create configuration from environment variables with legacy support."""
    config = TaskManagerConfig()
    
    # Apply legacy environment variable mappings
    for env_var, config_path in ENVIRONMENT_MAPPINGS.items():
        value = os.getenv(env_var)
        if value is not None:
            # Navigate to nested config attribute
            obj = config
            parts = config_path.split('.')
            
            for part in parts[:-1]:
                obj = getattr(obj, part)
            
            # Convert value to appropriate type
            field_info = obj.model_fields[parts[-1]]
            if field_info.annotation == bool:
                value = value.lower() in ('true', '1', 'yes', 'on')
            elif field_info.annotation == int:
                value = int(value)
            
            setattr(obj, parts[-1], value)
    
    return config