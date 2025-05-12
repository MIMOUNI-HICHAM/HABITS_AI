# Code Organization Guide

This guide explains how to organize a Flask application by separating concerns into different modules. The example shown here demonstrates how to split a monolithic Flask application into a more maintainable structure.

## Current Structure

```
studying/
├── app.py          # Flask application and routes
├── logic.py        # Business logic and database operations
├── studying.db     # SQLite database
└── templates/      # HTML templates
    └── index.html
```

## Code Organization Process

### 1. Identify Components

First, identify the different components in your monolithic application:

- **Routes/API Endpoints**: Flask route handlers and API endpoints
- **Business Logic**: Data processing, calculations, and business rules
- **Database Operations**: Database queries and data manipulation
- **Helper Functions**: Utility functions and common operations

### 2. Create Separate Files

#### app.py
- Contains only Flask-specific code
- Handles routing and request/response logic
- Imports functions from other modules
- Keeps the application configuration

Example:
```python
from flask import Flask, jsonify
from logic import get_study_data, add_study_session

app = Flask(__name__)

@app.route('/api/study-data')
def get_study_data_route():
    data = get_study_data()
    return jsonify(data)
```

#### logic.py
- Contains all business logic
- Handles database operations
- Contains helper functions
- Keeps constants and configuration

Example:
```python
import sqlite3
from datetime import datetime

DATABASE = 'studying.db'

def get_study_data():
    # Database operations and data processing
    pass

def add_study_session(data):
    # Database operations
    pass
```

### 3. Moving Code

1. **Identify Dependencies**:
   - Look for functions that depend on Flask (keep in app.py)
   - Look for functions that handle data processing (move to logic.py)

2. **Move Functions**:
   - Move database operations to logic.py
   - Move calculations and data processing to logic.py
   - Keep route handlers in app.py

3. **Update Imports**:
   - Add necessary imports in both files
   - Update function calls to use the new structure

### 4. Testing

After moving code:
1. Test each route to ensure it works
2. Verify database operations
3. Check that all functionality remains the same

## How to Apply to Other Projects

1. **Start with a Single File**:
   - Begin with your monolithic application
   - Identify the different types of code

2. **Create New Files**:
   - Create separate files for different concerns
   - Name files according to their purpose

3. **Move Code**:
   - Move related functions together
   - Keep dependencies in mind
   - Update imports and function calls

4. **Common Patterns**:
   - Keep routes in app.py
   - Move database operations to a separate file
   - Move business logic to a separate file
   - Keep configuration in appropriate files

## Benefits

- **Maintainability**: Easier to find and fix issues
- **Reusability**: Functions can be reused across different parts of the application
- **Testing**: Easier to write unit tests for isolated components
- **Scalability**: Easier to add new features or modify existing ones

## Next Steps

After this basic separation, you can further organize your code by:
1. Creating a proper package structure
2. Implementing blueprints for different features
3. Adding configuration files
4. Creating separate modules for different features

## Example of Further Organization

```
studying/
├── app/
│   ├── __init__.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   └── api.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── study.py
│   └── utils/
│       ├── __init__.py
│       └── helpers.py
├── config.py
├── run.py
└── requirements.txt
```

This structure allows for better organization as your application grows. 