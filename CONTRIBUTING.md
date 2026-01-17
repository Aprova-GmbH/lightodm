# Contributing to LightODM

Thank you for considering contributing to LightODM! This document provides guidelines and instructions for contributing.

## Code of Conduct

Please be respectful and constructive in all interactions. We're here to build something useful together.

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in [Issues](https://github.com/Aprova-GmbH/lightodm/issues)
2. If not, create a new issue with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - Python version, MongoDB version
   - Code sample if applicable

### Suggesting Features

1. Check [Issues](https://github.com/Aprova-GmbH/lightodm/issues) for existing feature requests
2. Create a new issue describing:
   - The problem you're trying to solve
   - Your proposed solution
   - Alternative solutions you've considered
   - Why this fits LightODM's minimalistic philosophy

### Pull Requests

1. **Fork the repository**

2. **Clone your fork**
   ```bash
   git clone https://github.com/YOUR_USERNAME/lightodm.git
   cd lightodm
   ```

3. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

4. **Set up development environment**
   ```bash
   # Install uv (if you don't have it)
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Install development dependencies
   uv pip install -e ".[dev]"
   ```

5. **Make your changes**
   - Write code following our style guide (see below)
   - Add tests for new functionality
   - Update documentation if needed

6. **Run tests**
   ```bash
   # Run all tests
   uv run pytest

   # Run with coverage
   uv run pytest --cov=lightodm --cov-report=term-missing

   # Lint code
   uv run black --check src tests
   uv run ruff check src tests
   ```

7. **Format code**
   ```bash
   uv run black src tests
   uv run ruff check --fix src tests
   ```

8. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add amazing feature"
   ```

   Follow [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat:` new feature
   - `fix:` bug fix
   - `docs:` documentation changes
   - `test:` add or update tests
   - `refactor:` code refactoring
   - `style:` formatting changes
   - `chore:` maintenance tasks

9. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

10. **Create Pull Request**
    - Go to the original repository
    - Click "New Pull Request"
    - Select your fork and branch
    - Fill in the PR template
    - Link related issues

## Development Setup

### Prerequisites

- Python 3.11+
- MongoDB 4.0+ (for integration tests)
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Quick Start

```bash
# Clone repository
git clone https://github.com/Aprova-GmbH/lightodm.git
cd lightodm

# Install with development dependencies
uv pip install -e ".[dev]"

# Run tests
uv run pytest

# Start MongoDB (if not running)
# Option 1: Docker
docker run -d -p 27017:27017 mongo:latest

# Option 2: Local installation
mongod --dbpath /path/to/data
```

## Code Style

### Python Style

We use:
- **Black** for code formatting (line length: 88)
- **Ruff** for linting
- **Type hints** for all public APIs
- **Docstrings** (Google style) for all public functions/classes

### Example

```python
from typing import Optional


def find_user(email: str) -> Optional[User]:
    """
    Find a user by email address.

    Args:
        email: The user's email address

    Returns:
        User instance if found, None otherwise

    Example:
        >>> user = find_user("john@example.com")
        >>> print(user.name)
        'John Doe'
    """
    return User.find_one({"email": email})
```

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

Examples:
```
feat(model): add support for custom ID generation

Allow users to override ID generation by providing a custom
generate_id function in model Settings.

Closes #123
```

```
fix(connection): handle connection timeout gracefully

Previously, connection timeout would raise unhandled exception.
Now catches timeout and logs appropriate error.

Fixes #456
```

## Testing

### Running Tests

```bash
# All tests
uv run pytest

# With coverage
uv run pytest --cov=lightodm --cov-report=html

# Specific file
uv run pytest tests/test_model.py

# Specific test
uv run pytest tests/test_model.py::test_model_creation

# Verbose output
uv run pytest -v

# Stop on first failure
uv run pytest -x
```

### Writing Tests

- Use `pytest` framework
- Use `mongomock` for unit tests (fast)
- Use real MongoDB for integration tests (mark with `@pytest.mark.integration`)
- Aim for >95% code coverage
- Test both sync and async APIs

Example test:

```python
import pytest
from lightodm import MongoBaseModel


class User(MongoBaseModel):
    class Settings:
        name = "test_users"

    name: str
    email: str


def test_user_creation(mock_mongo_client, monkeypatch):
    """Test creating and saving a user"""
    collection = mock_mongo_client.test_db.test_users
    monkeypatch.setattr(User, "get_collection", lambda: collection)

    user = User(name="John", email="john@example.com")
    user.save()

    assert user.id is not None
    assert User.get(user.id).name == "John"
```

## Documentation

### Building Documentation Locally

```bash
cd docs
uv run sphinx-build -b html . _build/html
open _build/html/index.html  # macOS
# or
xdg-open _build/html/index.html  # Linux
```

### Writing Documentation

- Use reStructuredText (.rst) for Sphinx docs
- Add docstrings to all public APIs
- Include code examples in docstrings
- Update docs/ when adding features

## Project Structure

```
lightodm/
├── src/lightodm/        # Source code
│   ├── __init__.py      # Package exports
│   ├── model.py         # Core MongoBaseModel
│   └── connection.py    # Connection management
├── tests/               # Test files
│   ├── conftest.py      # Pytest fixtures
│   ├── test_model.py    # Model tests
│   ├── test_async.py    # Async tests
│   └── test_connection.py
├── docs/                # Sphinx documentation
│   ├── conf.py
│   ├── index.rst
│   └── ...
├── examples/            # Usage examples
├── .github/workflows/   # CI/CD
└── pyproject.toml       # Package metadata
```

## Release Process

Only maintainers can create releases. See [PUBLISHING.md](PUBLISHING.md) for detailed instructions.

## Design Philosophy

LightODM follows these principles:

1. **Minimalistic**: Keep the codebase small and focused
2. **Explicit > Implicit**: No magic, clear behavior
3. **Dual Support**: Both sync and async APIs
4. **Pydantic Native**: Leverage Pydantic v2 fully
5. **MongoDB Direct**: Expose PyMongo/Motor directly
6. **Zero Abstraction Penalty**: Minimal overhead over raw PyMongo

### What We Accept

✅ Bug fixes
✅ Performance improvements
✅ Documentation improvements
✅ Test coverage improvements
✅ Small API enhancements that fit the philosophy

### What We Don't Accept

❌ Heavy abstractions (query builders, etc.)
❌ Features that significantly increase complexity
❌ Breaking changes without strong justification
❌ Dependencies beyond pydantic, pymongo, motor

## Getting Help

- **Issues**: [GitHub Issues](https://github.com/Aprova-GmbH/lightodm/issues)
- **Email**: vya@aprova.ch
- **Discussions**: Use GitHub Discussions for questions

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

Thank you for contributing to LightODM! 🚀
