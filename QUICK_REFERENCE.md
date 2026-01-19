# Quick Reference Guide

## Publishing a New Release

```bash
# 1. Update version in 3 files:
#    - pyproject.toml (line 3)
#    - src/lightodm/__init__.py (__version__)
#    - docs/conf.py (release and version)

# 2. Update CHANGELOG.md with changes

# 3. Run tests
cd /Users/vykhand/DEV/lightodm
uv run pytest --cov=lightodm --cov-report=term-missing
uv run black --check src tests
uv run ruff check src tests

# 4. Commit version bump
git add pyproject.toml src/lightodm/__init__.py docs/conf.py CHANGELOG.md
git commit -m "Bump version to X.Y.Z"
git push origin main

# 5. Create and push tag (this triggers automatic publishing)
git tag vX.Y.Z
git push origin vX.Y.Z

# Done! GitHub Actions will:
# - Build package
# - Publish to PyPI
# - Create GitHub release
# - ReadTheDocs will rebuild docs automatically
```

---

## Verify Release

```bash
# Check GitHub Actions
open https://github.com/Aprova-GmbH/lightodm/actions

# Check PyPI
open https://pypi.org/project/lightodm/

# Check Docs
open https://lightodm.readthedocs.io

# Test installation
pip install --upgrade lightodm
python -c "from lightodm import MongoBaseModel; print('OK')"
```

---

## Common Commands

```bash
# Run tests
uv run pytest -v

# Run tests with coverage
uv run pytest --cov=lightodm --cov-report=term-missing

# Run specific test file
uv run pytest tests/test_model.py -v

# Run specific test
uv run pytest tests/test_model.py::test_model_creation -v

# Format code
uv run black src tests

# Lint code
uv run ruff check src tests

# Fix linting issues
uv run ruff check --fix src tests

# Build package locally
uv run python -m build

# Check package metadata
uv run twine check dist/*

# Build documentation locally
cd docs
uv run sphinx-build -b html . _build/html
open _build/html/index.html

# Install package in editable mode
uv pip install -e .

# Install with dev dependencies
uv pip install -e ".[dev]"
```

---

## Development Setup

```bash
# Install uv (recommended package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies with development tools
uv pip install -e ".[dev]"

# Or using pip
pip install -e ".[dev]"
```

---

## Project Structure

```
lightodm/
├── src/lightodm/           # Source code
│   ├── __init__.py        # Public API exports
│   ├── connection.py      # MongoConnection singleton
│   └── model.py           # MongoBaseModel base class
├── tests/                 # Test suite
│   ├── conftest.py       # Pytest fixtures
│   ├── test_model.py     # Sync model tests
│   ├── test_async.py     # Async model tests
│   └── test_connection.py # Connection tests
├── docs/                  # Sphinx documentation
├── pyproject.toml        # Project configuration
└── CLAUDE.md             # Development guide
```

---

## Core Architecture

**Connection Management** (`src/lightodm/connection.py`)
- `MongoConnection`: Thread-safe singleton
- Sync client (PyMongo) initialized eagerly
- Async client (Motor) created lazily
- Environment variables: `MONGO_URL`, `MONGO_USER`, `MONGO_PASSWORD`, `MONGO_DB_NAME`

**ODM Model** (`src/lightodm/model.py`)
- `MongoBaseModel`: Pydantic v2 base class
- Dual API: sync methods + async methods (prefixed with `a`)
- Automatic `id` ↔ `_id` field mapping
- Collection name via inner `Settings` class

---

## Development Workflow

```bash
# Create feature branch
git checkout -b feature/my-feature

# Make changes and test
uv run pytest --cov=lightodm

# Format and lint
uv run black src tests
uv run ruff check --fix src tests

# Commit using Conventional Commits
git commit -m "feat: add new feature"

# Push and create PR
git push origin feature/my-feature
```

---

## Semantic Versioning Quick Guide

- **Patch** (0.1.0 → 0.1.1): Bug fixes only
- **Minor** (0.1.0 → 0.2.0): New features, backward compatible
- **Major** (0.9.0 → 1.0.0): Breaking changes

---

## Emergency: Manual Publishing

If GitHub Actions fails:

```bash
cd /Users/vykhand/DEV/lightodm
uv run python -m build
uv run twine upload dist/*
# Enter: __token__ (username)
# Enter: pypi-AgE... (your PyPI token)
```

---

## MongoDB for Testing

```bash
# Start MongoDB with Docker (with authentication)
docker run -d -p 27017:27017 \
  -e MONGO_INITDB_ROOT_USERNAME=test \
  -e MONGO_INITDB_ROOT_PASSWORD=test \
  --name mongo-test \
  mongo:latest

# Set environment variables for tests
export MONGO_URL="mongodb://localhost:27017"
export MONGO_USER="test"
export MONGO_PASSWORD="test"
export MONGO_DB_NAME="test_db"

# Stop MongoDB
docker stop mongo-test

# Remove container
docker rm mongo-test
```

---

## Useful Git Commands

```bash
# View recent commits
git log --oneline -10

# View uncommitted changes
git status
git diff

# Undo last commit (keep changes)
git reset --soft HEAD~1

# Delete local branch
git branch -d feature/old-feature

# Update from main
git checkout main
git pull origin main
git checkout feature/my-feature
git rebase main

# View all tags
git tag -l

# Delete tag (local and remote)
git tag -d v0.1.0
git push origin :refs/tags/v0.1.0
```

---

## Environment Setup

```bash
# Set MongoDB connection for testing
export MONGO_URL="mongodb://localhost:27017"
export MONGO_DB_NAME="lightodm_test"

# Or create .env file
cat > .env <<EOF
MONGO_URL=mongodb://localhost:27017
MONGO_DB_NAME=lightodm_test
EOF
```

---

## Usage Examples

### Define a Model
```python
from lightodm import MongoBaseModel, generate_id
from typing import Optional

class User(MongoBaseModel):
    class Settings:
        name = "users"  # MongoDB collection name

    name: str
    email: str
    age: Optional[int] = None
```

### Sync Operations
```python
# Create and save
user = User(name="Alice", email="alice@example.com")
user.save()

# Find
users = User.find({"name": "Alice"})
user = User.find_one({"email": "alice@example.com"})

# Update
user.age = 30
user.save()

# Delete
user.delete()
```

### Async Operations
```python
import asyncio

async def main():
    # Create and save
    user = User(name="Bob", email="bob@example.com")
    await user.asave()

    # Find
    users = await User.afind({"name": "Bob"})
    user = await User.afind_one({"email": "bob@example.com"})

    # Update
    user.age = 25
    await user.asave()

    # Delete
    await user.adelete()

asyncio.run(main())
```

---

## Key Design Patterns

**ID Field Mapping**
- Models use `id` field, MongoDB uses `_id`
- Automatic conversion via `_to_mongo_dict()` and `_from_mongo_dict()`
- Override with: `id: str = Field(default_factory=generate_id, alias="_id")`

**Custom Connection**
```python
@classmethod
def get_collection(cls):
    client = MongoClient("mongodb://custom:27017")
    return client["custom_db"]["custom_collection"]
```

**Method Pairs (Sync/Async)**
- `save()` / `asave()`
- `find()` / `afind()`
- `find_one()` / `afind_one()`
- `update_one()` / `aupdate_one()`
- `delete()` / `adelete()`
- `find_iter()` / `afind_iter()`

---

## Testing Best Practices

- Use `mongomock` for unit tests
- Reset `MongoConnection` singleton between tests
- Test both sync and async code paths
- Target >95% code coverage
- Use `monkeypatch` to override `get_collection()`

---

## Documentation

```bash
# Build and view docs locally
cd docs && \
uv run sphinx-build -b html . _build/html && \
open _build/html/index.html

# Docs auto-deploy to ReadTheDocs on push to main
# URL: https://lightodm.readthedocs.io
```

---

## Code Style

- **Formatter**: Black (line length: 100)
- **Linter**: Ruff
- **Type Checking**: mypy
- **Docstrings**: Google style
- **Commits**: Conventional Commits (`feat:`, `fix:`, `docs:`, `test:`, `refactor:`)

---

## Important Links

- **Repository**: https://github.com/Aprova-GmbH/lightodm
- **PyPI**: https://pypi.org/project/lightodm/
- **Documentation**: https://lightodm.readthedocs.io
- **Issues**: https://github.com/Aprova-GmbH/lightodm/issues

---

## Clean Up

```bash
# Remove build artifacts
rm -rf dist/ build/ *.egg-info/

# Remove pytest cache
rm -rf .pytest_cache/ __pycache__/

# Remove coverage reports
rm -rf htmlcov/ .coverage

# Remove docs build
rm -rf docs/_build/

# All at once
rm -rf dist/ build/ *.egg-info/ .pytest_cache/ __pycache__/ htmlcov/ .coverage docs/_build/
```
