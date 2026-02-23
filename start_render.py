#!/usr/bin/env python3
"""
Render deployment startup script with automatic database migrations.
This script handles database migrations before starting the Flask application.
"""

import os
import sys
import logging
from alembic.config import Config
from alembic import command
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_database_connection():
    """Check if database is accessible."""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        logger.error("DATABASE_URL environment variable not set")
        return False
    
    try:
        engine = create_engine(database_url)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connection successful")
        return True
    except OperationalError as e:
        logger.error(f"Database connection failed: {e}")
        return False

def run_migrations():
    """Run Alembic database migrations."""
    try:
        # Get the database URL
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            logger.error("DATABASE_URL not set for migrations")
            return False
        
        # Configure Alembic
        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", database_url)
        
        # Run migrations
        logger.info("Running database migrations...")
        command.upgrade(alembic_cfg, "head")
        logger.info("Database migrations completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_initial_data():
    """Create initial data if needed."""
    try:
        from app import create_app, db
        from app.models.user import User
        from app.models.lawyer_profile import LawyerProfile
        
        app = create_app()
        with app.app_context():
            # Check if any users exist
            if User.query.first() is None:
                logger.info("No users found, creating initial data...")
                # You can add initial data creation here if needed
                logger.info("Initial data creation completed")
            else:
                logger.info("Users already exist, skipping initial data creation")
        
        return True
    except Exception as e:
        logger.error(f"Initial data creation failed: {e}")
        return False

def start_application():
    """Start the Flask application with Gunicorn."""
    try:
        import subprocess
        import sys
        
        logger.info("Starting Flask application with Gunicorn...")
        
        # Get port from environment or use default
        port = os.getenv('PORT', 5000)
        logger.info(f"Using port: {port}")
        logger.info(f"PORT environment variable: {os.getenv('PORT')}")
        
        # Gunicorn command
        cmd = [
            'gunicorn',
            '--workers', '1',
            '--bind', f'0.0.0.0:{port}',
            '--timeout', '120',
            '--max-requests', '1000',
            '--max-requests-jitter', '100',
            '--log-level', 'info',
            'run:app'
        ]
        
        # Start Gunicorn
        logger.info(f"Running command: {' '.join(cmd)}")
        logger.info(f"Binding to 0.0.0.0:{port}")
        subprocess.run(cmd, check=True)
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        sys.exit(1)

def main():
    """Main startup function."""
    logger.info("Starting Legalize backend application...")
    
    # Check environment variables
    required_env_vars = ['DATABASE_URL', 'JWT_SECRET_KEY']
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        sys.exit(1)
    
    # Step 1: Check database connection
    if not check_database_connection():
        logger.error("Database connection failed, exiting")
        sys.exit(1)
    
    # Step 2: Run migrations
    if not run_migrations():
        logger.error("Migration failed, exiting")
        sys.exit(1)
    
    # Step 3: Create initial data (optional)
    create_initial_data()
    
    # Step 4: Start the application
    start_application()

if __name__ == "__main__":
    main()
