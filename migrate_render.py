#!/usr/bin/env python3
"""
Standalone migration script for Render deployment.
This script runs migrations without requiring Flask app context.
"""

import os
import sys
import logging
from alembic.config import Config
from alembic import command
from alembic.script import ScriptDirectory
from alembic.runtime.migration import MigrationContext
from sqlalchemy import create_engine, text

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_migrations_standalone():
    """Run migrations using Alembic directly without Flask context."""
    try:
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            logger.error("DATABASE_URL not set")
            return False
        
        # Create engine and connect
        engine = create_engine(database_url)
        
        # Configure Alembic
        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", database_url)
        
        # Check if migrations are needed
        with engine.connect() as connection:
            # Create alembic_version table if it doesn't exist
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS alembic_version (
                    version_num VARCHAR(32) NOT NULL,
                    PRIMARY KEY (version_num)
                )
            """))
            
            # Get current version
            result = connection.execute(text("SELECT version_num FROM alembic_version"))
            current_version = result.scalar() if result.rowcount > 0 else None
            
            # Get available migrations
            script_dir = ScriptDirectory.from_config(alembic_cfg)
            head_revision = script_dir.get_current_head()
            
            logger.info(f"Current version: {current_version}")
            logger.info(f"Head version: {head_revision}")
            
            if current_version == head_revision:
                logger.info("Database is already up to date")
                return True
            
            # Run migrations
            logger.info("Running migrations...")
            with connection.begin():
                context = MigrationContext.configure(connection)
                context.configure(alembic_cfg)
                
                # Run upgrade to head
                command.upgrade(alembic_cfg, "head")
            
        logger.info("Migrations completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_migrations_standalone()
    sys.exit(0 if success else 1)
