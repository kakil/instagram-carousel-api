#!/usr/bin/env python3
"""
Cleanup script for temporary carousel files

This script can be run as a cron job to ensure temporary files are cleaned up
even if the application isn't restarted frequently.

Usage:
    python cleanup_temp_files.py
"""

import os
import sys
import logging
import shutil
from datetime import datetime, timedelta

# Add the parent directory to path so we can import the app modules
sys.path.insert(0,
                os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the storage service module
from app.services import storage_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('cleanup.log')
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Run the cleanup operation"""
    logger.info("Starting temporary file cleanup")

    try:
        # Call the cleanup function from the storage service
        storage_service.cleanup_old_files()
        logger.info("Cleanup completed successfully")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())