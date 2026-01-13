# Python Code Quality Tools Guide

## Overview

This guide covers the essential tools for maintaining high-quality Python code: Black, Flake8, and MyPy.

## Tool Installation

```bash
pip3 install black flake8 mypy
```

**Note**: On macOS, use `pip3` to avoid conflicts with system commands. Consider using a virtual environment:

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate
pip install black flake8 mypy
```

## 1. Black - Code Formatter

**Purpose**: Automatically formats code to consistent style
**Why use it**: Eliminates formatting debates, ensures consistency

### Usage
```bash
# Format single file
black your_file.py

# Format entire directory
black .

# Check what would be changed (dry run)
black --check .
```

### Configuration
Create `pyproject.toml`:
```toml
[tool.black]
line-length = 88
target-version = ['py38']
```

## 2. Flake8 - Style & Error Checker

**Purpose**: Catches style violations, unused imports, complexity issues
**Why use it**: More practical than pylint, fewer false positives

### Usage
```bash
# Check single file
flake8 your_file.py

# Check entire directory
flake8 .

# Show statistics
flake8 --statistics .
```

### Configuration
Create `.flake8` or add to `pyproject.toml`:
```ini
[flake8]
max-line-length = 88
ignore = E203, W503
exclude = .git,__pycache__,venv
```

### Common Error Codes
- `E501`: Line too long
- `F401`: Unused import
- `F841`: Unused variable
- `E302`: Expected 2 blank lines

## 3. MyPy - Type Checker

**Purpose**: Validates type hints and catches type-related errors
**Why use it**: Prevents runtime type errors, improves code reliability

### Usage
```bash
# Check single file
mypy your_file.py

# Check entire directory
mypy .

# Ignore missing imports
mypy --ignore-missing-imports .
```

### Configuration
Create `mypy.ini`:
```ini
[mypy]
python_version = 3.8
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
```

## Complete Workflow

### 1. Project Setup
Create `pyproject.toml`:
```toml
[tool.black]
line-length = 88

[tool.mypy]
python_version = "3.8"
warn_return_any = true
warn_unused_configs = true
```

Create `.flake8`:
```ini
[flake8]
max-line-length = 88
ignore = E203, W503
exclude = .git,__pycache__,venv
```

### 2. Pre-commit Script
Create `check_code.sh`:
```bash
#!/bin/bash
echo "Running Black..."
black .

echo "Running Flake8..."
flake8 .

echo "Running MyPy..."
mypy .

echo "Code quality checks complete!"
```

### 3. Single Command
```bash
black . && flake8 . && mypy .
```

## IDE Integration

### VS Code
Install extensions:
- Python (Microsoft)
- Black Formatter
- Flake8
- Pylance (includes MyPy)

Add to `settings.json`:
```json
{
    "python.formatting.provider": "black",
    "python.linting.flake8Enabled": true,
    "python.linting.mypyEnabled": true,
    "editor.formatOnSave": true
}
```

## Why This Combination?

### Black
- ✅ Zero configuration needed
- ✅ Eliminates style debates
- ✅ Works with any codebase
- ✅ Fast and reliable

### Flake8 vs Pylint
- ✅ Flake8: Faster, fewer false positives
- ✅ Flake8: Better Black compatibility
- ❌ Pylint: Slower, more verbose warnings

### MyPy
- ✅ Catches type errors before runtime
- ✅ Improves code documentation
- ✅ Better IDE support with type hints

## Common Issues & Solutions

### Black vs Flake8 Conflicts
Use these Flake8 ignores:
```ini
ignore = E203, W503
```

### MyPy Import Errors
For third-party libraries without types:
```bash
mypy --ignore-missing-imports .
```

Install type stubs for better type checking:
```bash
pip install pandas-stubs types-requests
# Or install all missing stubs automatically
mypy --install-types
```

### Large Codebases
Run tools on changed files only:
```bash
git diff --name-only | grep "\.py$" | xargs black
```

## Automation

### GitHub Actions
```yaml
name: Code Quality
on: [push, pull_request]
jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - uses: actions/setup-python@v2
    - run: pip install black flake8 mypy
    - run: black --check .
    - run: flake8 .
    - run: mypy .
```

### Pre-commit Hooks
```bash
pip install pre-commit
```

Create `.pre-commit-config.yaml`:
```yaml
repos:
- repo: https://github.com/psf/black
  rev: 22.3.0
  hooks:
  - id: black
- repo: https://github.com/pycqa/flake8
  rev: 4.0.1
  hooks:
  - id: flake8
```

## Summary

This three-tool combination provides:
- **Consistent formatting** (Black)
- **Style compliance** (Flake8) 
- **Type safety** (MyPy)

Run `black . && flake8 . && mypy .` before every commit for clean, reliable Python code.