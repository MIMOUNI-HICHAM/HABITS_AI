from .budget_db import init_db as init_budget_db, seed_data as seed_budget_data
from .sleeping_db import init_db as init_sleeping_db, seed_data as seed_sleeping_data
from .sports_db import init_db as init_sports_db, seed_data as seed_sports_data
from .studying_db import init_db as init_studying_db, seed_data as seed_studying_data

def init_all_dbs():
    """Initialize all databases and seed data."""
    # Initialize databases
    init_budget_db()
    init_sleeping_db()
    init_sports_db()
    init_studying_db()
    
    # Seed data with current dates
    seed_budget_data()
    seed_sleeping_data()
    seed_sports_data()
    seed_studying_data()

def seed_all_data():
    """Seed all databases with sample data."""
    seed_budget_data()
    seed_sleeping_data()
    seed_sports_data()
    seed_studying_data() 