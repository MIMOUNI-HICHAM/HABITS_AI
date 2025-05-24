from .init_db import init_database, init_tables

def init_all_dbs():
    """Initialize all databases."""
    init_database()
    init_tables() 