# Database Module Documentation

## Overview
This database module is a core component of the HABITS_AI application, managing data storage and retrieval for various habit-tracking features. The module uses SQLite as the database engine and is organized into separate database files for different types of habits.

## Structure
The database module consists of the following components:

### Main Files
- `__init__.py`: Entry point that provides initialization and seeding functions for all databases
- `budget_db.py`: Manages financial tracking and budget-related data
- `sleeping_db.py`: Handles sleep tracking and analysis data
- `sports_db.py`: Manages sports and physical activity tracking
- `studying_db.py`: Handles study session tracking and analysis

### Database Features
Each database file follows a similar pattern and includes:
- Database initialization function (`init_db()`)
- Data seeding function (`seed_data()`)
- Realistic data generation for testing and development
- SQLite database tables with appropriate schemas

## Database Schemas

### Study Sessions Database
```sql
CREATE TABLE study_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    time TEXT,
    hours REAL,
    topic TEXT,
    location TEXT
)
```

### Sports Database
Similar structure to study sessions, tracking physical activities.

### Sleeping Database
Tracks sleep patterns and quality metrics.

### Budget Database
Manages financial transactions and budget tracking.

## Usage

### Initialization
To initialize all databases:
```python
from database import init_all_dbs
init_all_dbs()
```

### Seeding Data
To populate databases with sample data:
```python
from database import seed_all_data
seed_all_data()
```

## Data Generation
The module includes sophisticated data generation capabilities:
- Generates realistic patterns for different types of habits
- Accounts for seasonal variations (e.g., summer breaks for studying)
- Creates natural variations in activity frequency
- Maintains data consistency across different time periods

## Best Practices
1. Always initialize databases before use
2. Use the provided functions from `__init__.py` for database operations
3. Each database file is self-contained and can be used independently
4. Database files are stored in their respective feature directories

## Technical Details
- Uses SQLite for lightweight, file-based storage
- Implements proper connection handling with context managers
- Includes data validation and error handling
- Supports concurrent access through SQLite's built-in mechanisms

## Maintenance
- Regular database backups are recommended
- Monitor database size and performance
- Consider implementing data archiving for long-term storage
- Keep database schemas in sync with application updates 