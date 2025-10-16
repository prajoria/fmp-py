# FMP-PY Project Organization Rules

## Overview
This document defines the rules and structure for organizing the FMP-PY project properly. These rules are designed to be AI-readable and enforce a clean, maintainable codebase with minimal restructuring of existing functionality.

## Project Structure Principles

### 1. Source Code Organization
- **Core Library**: All library code must be in `src/fmp_py/`
- **Application Scripts**: All standalone scripts must be in appropriate subdirectories under `src/fmp_py/`
- **Tests**: All tests must be in `tests/` directory with mirror structure of `src/`
- **Documentation**: All docs in `docs/` directory
- **Examples**: All example code in `examples/` directory
- **Data**: Static data files in `data/` directory

### 2. Root Directory Rules
**ALLOWED in root:**
- Configuration files: `pyproject.toml`, `pytest.ini`, `.env`, `.gitignore`, etc.
- Documentation: `README.md`, `LICENSE`, `SECURITY.md`, etc.
- Package metadata: `poetry.lock`
- CI/CD files: `.github/`, `.pre-commit-config.yaml`
- IDE settings: `.vscode/`, `*.code-workspace`

**NOT ALLOWED in root:**
- Executable Python scripts (`.py` files except `setup.py` if needed)
- SQL files
- Data processing scripts
- Analysis scripts
- Utility scripts

### 3. Source Directory Structure (`src/fmp_py/`)

#### 3.1 Core API Modules (Current - Keep as is)
```
src/fmp_py/
├── __init__.py
├── fmp_base.py                    # Base API client
├── fmp_*.py                       # API endpoint modules
└── models/                        # Data models
    ├── __init__.py
    └── *.py                       # Model classes
```

#### 3.2 Stock Analysis Package (Current - Keep as is)
```
src/fmp_py/StockAnalysis/
├── __init__.py
├── api/                           # API integration
├── cache/                         # Caching functionality
├── client/                        # Client implementations
├── database/                      # Database operations
├── docs/                          # Package-specific docs
├── examples/                      # Package examples
├── notebooks/                     # Jupyter notebooks
└── utils/                         # Utility functions
```

#### 3.3 New Required Subdirectories

##### 3.3.1 Scripts Directory
```
src/fmp_py/scripts/
├── __init__.py
├── data_management/               # Data management scripts
│   ├── __init__.py
│   ├── sp500_gap_filler.py       # Move from root
│   ├── populate_sp500_companies.py # Move from root
│   └── monitor_progress.py       # Move from root
├── analysis/                      # Analysis scripts
│   ├── __init__.py
│   ├── apple_analytics.py        # Move from root
│   └── view_apple_cache.py       # Move from root
├── utilities/                     # Utility scripts
│   ├── __init__.py
│   ├── security_check.py         # Move from root
│   └── test_holidays.py          # Move from root
└── data_fetching/                 # Data fetching scripts
    ├── __init__.py
    └── fetch_apple_data.py        # Move from root
```

##### 3.3.2 SQL Directory
```
src/fmp_py/sql/
├── __init__.py
├── procedures/
│   ├── __init__.py
│   ├── watermark_procedures.sql      # Move from root
│   ├── watermark_procedures_fixed.sql # Move from root
│   └── watermark_procedures_simple.sql # Move from root
└── migrations/
    ├── __init__.py
    └── # Future migration files
```

### 4. File Movement Rules

#### 4.1 Root-level Python Files to Move
| Current Location | Target Location | Category |
|------------------|-----------------|----------|
| `sp500_gap_filler.py` | `src/fmp_py/scripts/data_management/` | Data Management |
| `apple_analytics.py` | `src/fmp_py/scripts/analysis/` | Analysis |
| `fetch_apple_data.py` | `src/fmp_py/scripts/data_fetching/` | Data Fetching |
| `monitor_progress.py` | `src/fmp_py/scripts/data_management/` | Data Management |
| `populate_sp500_companies.py` | `src/fmp_py/scripts/data_management/` | Data Management |
| `security_check.py` | `src/fmp_py/scripts/utilities/` | Utilities |
| `test_holidays.py` | `src/fmp_py/scripts/utilities/` | Utilities |
| `view_apple_cache.py` | `src/fmp_py/scripts/analysis/` | Analysis |

#### 4.2 Root-level SQL Files to Move
| Current Location | Target Location | Category |
|------------------|-----------------|----------|
| `watermark_procedures.sql` | `src/fmp_py/sql/procedures/` | SQL Procedures |
| `watermark_procedures_fixed.sql` | `src/fmp_py/sql/procedures/` | SQL Procedures |
| `watermark_procedures_simple.sql` | `src/fmp_py/sql/procedures/` | SQL Procedures |

### 5. Import Path Rules

#### 5.1 After Reorganization Import Updates
When files are moved, update imports to use proper relative imports:

**For scripts in `src/fmp_py/scripts/`:**
```python
# Instead of:
sys.path.append('/absolute/path/to/src')
from fmp_py.StockAnalysis.database.connection import get_connection

# Use:
from ...StockAnalysis.database.connection import get_connection
```

**For cross-package imports:**
```python
from fmp_py.StockAnalysis.client.fmp_client import FMPClient
from fmp_py.models.quote import Quote
```

#### 5.2 Entry Point Scripts
For scripts that need to be executable from command line:
- Keep shebang lines: `#!/usr/bin/env python3`
- Add entry points in `pyproject.toml` if needed
- Use `python -m fmp_py.scripts.category.script_name` pattern

### 6. Configuration and Environment Rules

#### 6.1 Environment Files
- `.env` and `.env.example` stay in root
- Scripts should use relative paths to find `.env`:
```python
from pathlib import Path
import os
from dotenv import load_dotenv

# Find .env in project root
project_root = Path(__file__).parent.parent.parent.parent
load_dotenv(project_root / '.env')
```

#### 6.2 Path Management
- No hardcoded absolute paths in code
- Use `pathlib.Path` for path operations
- Use relative imports where possible
- Use `__file__` to determine script location for relative paths

### 7. Testing Rules

#### 7.1 Test Structure
Mirror the source structure in tests:
```
tests/
├── __init__.py
├── test_fmp_*.py                  # Core API tests
├── StockAnalysis/                 # Mirror StockAnalysis structure
│   ├── __init__.py
│   ├── test_api/
│   ├── test_cache/
│   └── test_database/
└── scripts/                       # Tests for scripts
    ├── __init__.py
    ├── test_data_management/
    ├── test_analysis/
    ├── test_utilities/
    └── test_data_fetching/
```

#### 7.2 Test Naming
- Test files: `test_*.py`
- Test classes: `Test*`
- Test methods: `test_*`

### 8. Documentation Rules

#### 8.1 Documentation Structure
```
docs/
├── source/
│   ├── index.md                   # Main documentation
│   ├── api/                       # API documentation
│   ├── scripts/                   # Scripts documentation
│   └── examples/                  # Usage examples
└── # Build files
```

#### 8.2 Code Documentation
- All modules must have docstrings
- All public functions must have docstrings
- Use Google-style docstrings
- Include examples in docstrings where helpful

### 9. Naming Conventions

#### 9.1 Files and Directories
- Directories: `snake_case`
- Python files: `snake_case.py`
- Classes: `PascalCase`
- Functions/methods: `snake_case`
- Constants: `UPPER_SNAKE_CASE`

#### 9.2 Package and Module Names
- Package names: lowercase, no underscores if possible
- Module names: lowercase with underscores
- Avoid name conflicts with Python stdlib

### 10. Entry Points and CLI

#### 10.1 Command Line Interface
Define entry points in `pyproject.toml`:
```toml
[tool.poetry.scripts]
fmp-gap-filler = "fmp_py.scripts.data_management.sp500_gap_filler:main"
fmp-monitor = "fmp_py.scripts.data_management.monitor_progress:main"
fmp-security-check = "fmp_py.scripts.utilities.security_check:main"
```

#### 10.2 Module Execution
Support `python -m` execution for scripts:
```python
if __name__ == "__main__":
    main()
```

### 11. Dependencies and Imports

#### 11.1 Import Order (following PEP 8)
1. Standard library imports
2. Related third-party imports
3. Local application/library imports

#### 11.2 Dependency Management
- All dependencies in `pyproject.toml`
- Use version constraints appropriately
- Separate dev, test, and doc dependencies

### 12. Data and Configuration

#### 12.1 Static Data
- CSV files, JSON configs in `data/` directory
- Version control static reference data
- Large datasets should be downloaded, not stored

#### 12.2 Runtime Data
- Generated data in appropriate subdirectories
- Cache data should be configurable location
- Log files in designated log directory

### 13. Security Rules

#### 13.1 Secrets Management
- Never commit API keys or passwords
- Use environment variables for secrets
- Provide `.env.example` with dummy values
- Use `python-dotenv` for local development

#### 13.2 Code Security
- Validate all inputs
- Use parameterized queries for SQL
- Sanitize file paths
- Regular security audits with tools

### 14. Quality and Standards

#### 14.1 Code Quality Tools
- Use `ruff` for linting and formatting (already configured)
- Use `pytest` for testing
- Use `pre-commit` hooks
- Type hints where beneficial

#### 14.2 Git Practices
- Meaningful commit messages
- Feature branch workflow
- No generated files in git (except necessary ones)
- Use `.gitignore` properly

### 15. Backwards Compatibility

#### 15.1 During Reorganization
- Maintain existing functionality
- Provide deprecation warnings for moved modules
- Create import aliases for smooth transition
- Update all internal imports

#### 15.2 API Stability
- Follow semantic versioning
- Deprecate before removing
- Document breaking changes
- Provide migration guides

## Implementation Priority

### Phase 1: Immediate (No Breaking Changes)
1. Create new directory structure under `src/fmp_py/`
2. Create `PROJECT_ORGANIZATION_RULES.md` (this file)
3. Update `.gitignore` for new structure

### Phase 2: File Movement
1. Move scripts to appropriate subdirectories
2. Move SQL files to `sql/` directory
3. Update all import statements
4. Update relative path references

### Phase 3: Integration
1. Add entry points to `pyproject.toml`
2. Update documentation
3. Add tests for moved scripts
4. Verify all functionality works

### Phase 4: Cleanup
1. Remove old file locations
2. Update CI/CD configurations
3. Update README and documentation
4. Final testing and validation

## AI Tool Instructions

When organizing this project:
1. **Always preserve functionality** - ensure moved files work correctly
2. **Update imports systematically** - fix all relative and absolute imports
3. **Maintain entry points** - ensure scripts remain executable
4. **Follow the structure** - use the exact directory structure defined here
5. **Test after changes** - verify functionality after each move
6. **Update documentation** - keep docs in sync with structure changes

This structure provides a clean, maintainable, and scalable organization while preserving all existing functionality and following Python packaging best practices.