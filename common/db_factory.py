import sqlite3
import os
from .logging_config import setup_logger

logger = setup_logger('db_factory', '.jules_state/db_factory.log')

class DBFactory:
    def __init__(self, db_path):
        self.db_path = db_path
        self._ensure_db_dir()

    def _ensure_db_dir(self):
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            try:
                os.makedirs(db_dir)
                logger.info(f"Created database directory: {db_dir}")
            except OSError as e:
                logger.error(f"Failed to create database directory {db_dir}: {e}")
                raise

    def get_connection(self):
        try:
            conn = sqlite3.connect(self.db_path)
            logger.info(f"Connected to database: {self.db_path}")
            return conn
        except sqlite3.Error as e:
            logger.error(f"Failed to connect to database {self.db_path}: {e}")
            raise
