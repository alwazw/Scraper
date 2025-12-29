import json
import os
import sqlite3
from .logging_config import setup_logger

logger = setup_logger('db_utils', '.jules_state/db_utils.log')

def load_schema(schema_name):
    """Loads the schema definition for a given module from the registry."""
    registry_path = os.path.join(os.path.dirname(__file__), 'schema_registry.json')
    try:
        with open(registry_path, 'r') as f:
            registry = json.load(f)
        return registry.get(schema_name)
    except Exception as e:
        logger.error(f"Failed to load schema registry: {e}")
        raise

def init_db(connection, schema_name):
    """Initializes the database table based on the schema name."""
    schema = load_schema(schema_name)
    if not schema:
        logger.error(f"Schema '{schema_name}' not found in registry.")
        raise ValueError(f"Schema '{schema_name}' not found.")

    table_name = schema_name # using schema key as table name for simplicity, or we could add table_name to schema
    # Actually schema_registry keys seem to be logical names. Let's assume table name matches key or we derive it.
    # Looking at schema_registry.json: "lead_harvest", "enrichment", "master_leads".
    # I'll use these as table names.

    columns_def = []
    for col in schema['columns']:
        columns_def.append(f"{col['name']} {col['type']}")

    create_statement = f"CREATE TABLE IF NOT EXISTS {schema_name} ({', '.join(columns_def)});"

    try:
        cursor = connection.cursor()
        cursor.execute(create_statement)
        connection.commit()
        logger.info(f"Initialized table '{schema_name}' successfully.")
    except sqlite3.Error as e:
        logger.error(f"Failed to initialize table '{schema_name}': {e}")
        raise
