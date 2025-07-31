"""Main entry point for the Advanced MCP Task Manager.

This module provides the main entry point for running the task management server
with integrated graph (NetworkX) and table (DuckDB) storage backends.
"""

import asyncio
import logging
import sys
from pathlib import Path

from src.config import get_config, TaskManagerConfig
from src.server import main as server_main


def setup_logging(config: TaskManagerConfig) -> None:
    """Set up logging configuration."""
    log_level = getattr(logging, config.get_log_level())
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(
                Path(config.data_dir) / 'task_manager.log',
                mode='a'
            )
        ]
    )
    
    # Suppress noisy third-party loggers in non-debug mode
    if not config.is_debug_mode():
        logging.getLogger('mcp').setLevel(logging.WARNING)
        logging.getLogger('duckdb').setLevel(logging.WARNING)


async def initialize_system(config: TaskManagerConfig) -> None:
    """Initialize the task management system."""
    logger = logging.getLogger(__name__)
    
    # Ensure data directory exists
    data_dir = Path(config.data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Task Manager starting...")
    logger.info(f"Data directory: {data_dir.absolute()}")
    logger.info(f"Database path: {config.database.path}")
    logger.info(f"Debug mode: {config.is_debug_mode()}")
    
    # Check database file
    db_path = Path(config.database.path)
    if db_path.exists():
        logger.info(f"Using existing database: {db_path}")
    else:
        logger.info(f"Creating new database: {db_path}")


async def main() -> None:
    """Main entry point for the application."""
    try:
        # Load configuration
        config = get_config()
        
        # Setup logging
        setup_logging(config)
        
        # Initialize system
        await initialize_system(config)
        
        # Start the MCP server
        await server_main()
        
    except KeyboardInterrupt:
        logging.info("Shutting down gracefully...")
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())