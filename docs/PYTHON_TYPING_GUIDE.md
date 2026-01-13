# Python Typing Module Guide

## Overview
The `typing` module provides type hints for Python functions and variables, improving code readability and enabling static type checking.

```python
from typing import Dict, List, Any, Tuple, Union, Optional
```

## 1. Dict - Dictionary Type Hints

**Purpose**: Specify dictionary key and value types

### Basic Usage
```python
# Dict[key_type, value_type]
def get_user_scores() -> Dict[str, int]:
    return {"alice": 95, "bob": 87, "charlie": 92}

# Function parameter
def process_config(config: Dict[str, str]) -> None:
    for key, value in config.items():
        print(f"{key}: {value}")
```

### Real Examples
```python
# String keys, integer values
user_ages: Dict[str, int] = {"john": 25, "jane": 30}

# String keys, any value type
settings: Dict[str, Any] = {
    "debug": True,
    "port": 8080,
    "host": "localhost"
}

# Nested dictionaries
nested_data: Dict[str, Dict[str, int]] = {
    "team_a": {"wins": 10, "losses": 5},
    "team_b": {"wins": 8, "losses": 7}
}
```

## 2. List - List Type Hints

**Purpose**: Specify list element types

### Basic Usage
```python
# List[element_type]
def get_names() -> List[str]:
    return ["alice", "bob", "charlie"]

# Function parameter
def calculate_average(numbers: List[float]) -> float:
    return sum(numbers) / len(numbers)
```

### Real Examples
```python
# List of strings
usernames: List[str] = ["admin", "user1", "guest"]

# List of integers
scores: List[int] = [95, 87, 92, 78]

# List of dictionaries
users: List[Dict[str, str]] = [
    {"name": "Alice", "role": "admin"},
    {"name": "Bob", "role": "user"}
]

# Nested lists
matrix: List[List[int]] = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
```

## 3. Any - Accept Any Type

**Purpose**: Allow any type (use sparingly)

### Basic Usage
```python
def process_data(data: Any) -> str:
    return str(data)  # Convert anything to string

def flexible_function(value: Any) -> Any:
    if isinstance(value, str):
        return value.upper()
    elif isinstance(value, int):
        return value * 2
    else:
        return value
```

### Real Examples
```python
# Configuration that can hold any type
config_value: Any = "debug_mode"  # Could be str, bool, int, etc.

# API response that varies
api_response: Dict[str, Any] = {
    "status": "success",
    "data": [1, 2, 3],  # Could be list, dict, str, etc.
    "timestamp": 1234567890
}

# Generic container
container: List[Any] = ["text", 42, True, {"key": "value"}]
```

## 4. Tuple - Tuple Type Hints

**Purpose**: Specify tuple element types and length

### Basic Usage
```python
# Fixed length tuple
def get_coordinates() -> Tuple[float, float]:
    return (10.5, 20.3)

# Variable length tuple (all same type)
def get_scores() -> Tuple[int, ...]:
    return (95, 87, 92, 78)
```

### Real Examples
```python
# Fixed tuple - coordinates
point: Tuple[float, float] = (10.5, 20.3)

# Mixed types - name and age
person: Tuple[str, int] = ("Alice", 25)

# Three elements - RGB color
color: Tuple[int, int, int] = (255, 128, 0)

# Variable length - all integers
numbers: Tuple[int, ...] = (1, 2, 3, 4, 5)

# Function returning multiple values
def parse_name(full_name: str) -> Tuple[str, str]:
    parts = full_name.split()
    return parts[0], parts[-1]  # first_name, last_name
```

## 5. Union - Multiple Possible Types

**Purpose**: Allow multiple specific types

### Basic Usage
```python
# Can be string OR integer
def process_id(user_id: Union[str, int]) -> str:
    return str(user_id)

# Return string OR None
def find_user(name: str) -> Union[str, None]:
    users = ["alice", "bob"]
    return name if name in users else None
```

### Real Examples
```python
# ID can be string or integer
user_id: Union[str, int] = "user123"  # or 12345

# Response can be data or error message
response: Union[Dict[str, Any], str] = {"data": "success"}  # or "Error occurred"

# Number can be int or float
number: Union[int, float] = 42  # or 42.5

# Function that accepts multiple input types
def format_value(value: Union[str, int, float]) -> str:
    if isinstance(value, str):
        return f"'{value}'"
    else:
        return str(value)
```

## 6. Optional - Value or None

**Purpose**: Shorthand for `Union[Type, None]`

### Basic Usage
```python
# Optional[str] is same as Union[str, None]
def get_username(user_id: int) -> Optional[str]:
    users = {1: "alice", 2: "bob"}
    return users.get(user_id)  # Returns str or None

# Optional parameter with default None
def create_user(name: str, email: Optional[str] = None) -> Dict[str, Any]:
    user = {"name": name}
    if email:
        user["email"] = email
    return user
```

### Real Examples
```python
# Database query might return None
def find_user_by_id(user_id: int) -> Optional[Dict[str, str]]:
    # Simulate database lookup
    if user_id == 1:
        return {"name": "Alice", "email": "alice@example.com"}
    return None

# Optional configuration
debug_mode: Optional[bool] = None  # Not set yet

# Function with optional parameters
def connect_database(
    host: str,
    port: int = 5432,
    username: Optional[str] = None,
    password: Optional[str] = None
) -> bool:
    # Connection logic here
    return True

# Processing optional data
def process_user_data(data: Optional[Dict[str, Any]]) -> str:
    if data is None:
        return "No data provided"
    return f"Processing user: {data.get('name', 'Unknown')}"
```

## Complex Combinations

### Real-World Examples
```python
# API endpoint configuration
EndpointConfig = Dict[str, Union[str, int, bool, List[str]]]

api_config: EndpointConfig = {
    "url": "https://api.example.com",
    "port": 443,
    "ssl": True,
    "headers": ["Content-Type", "Authorization"]
}

# Database query result
QueryResult = Optional[List[Dict[str, Any]]]

def execute_query(sql: str) -> QueryResult:
    # Returns list of rows or None if no results
    return [{"id": 1, "name": "Alice"}] if sql else None

# Validation function
ValidationErrors = Dict[str, List[str]]

def validate_user(data: Dict[str, Any]) -> Tuple[bool, ValidationErrors]:
    errors: ValidationErrors = {}
    
    if not data.get("name"):
        errors["name"] = ["Name is required"]
    
    if not data.get("email"):
        errors["email"] = ["Email is required"]
    
    is_valid = len(errors) == 0
    return is_valid, errors
```

## Best Practices

### 1. Use Specific Types When Possible
```python
# Good
def calculate_tax(price: float, rate: float) -> float:
    return price * rate

# Avoid (too generic)
def calculate_tax(price: Any, rate: Any) -> Any:
    return price * rate
```

### 2. Use Optional for Nullable Values
```python
# Good
def find_user(name: str) -> Optional[Dict[str, str]]:
    return {"name": name} if name else None

# Less clear
def find_user(name: str) -> Union[Dict[str, str], None]:
    return {"name": name} if name else None
```

### 3. Type Aliases for Complex Types
```python
# Create aliases for readability
UserData = Dict[str, Union[str, int, bool]]
ValidationResult = Tuple[bool, List[str]]

def validate_user(data: UserData) -> ValidationResult:
    # Implementation here
    return True, []
```

## Common Patterns in Data Engineering

```python
# Configuration management
Config = Dict[str, Union[str, int, float, bool, List[str]]]

# Data validation results
ValidationSummary = Dict[str, Union[int, float, List[str], bool]]

# Database connection parameters
ConnectionParams = Dict[str, Optional[Union[str, int]]]

# Data processing pipeline
ProcessingResult = Tuple[bool, Optional[str], Dict[str, Any]]

def process_data(
    data: List[Dict[str, Any]], 
    config: Config
) -> ProcessingResult:
    try:
        # Process data
        return True, None, {"rows_processed": len(data)}
    except Exception as e:
        return False, str(e), {}
```

## Summary

- **Dict[K, V]**: Dictionary with specific key/value types
- **List[T]**: List with specific element type
- **Any**: Accept any type (use sparingly)
- **Tuple[T1, T2, ...]**: Fixed-length tuple with specific types
- **Union[T1, T2, ...]**: One of several possible types
- **Optional[T]**: Value of type T or None

Type hints improve code clarity, enable better IDE support, and catch errors early with static type checkers like MyPy.