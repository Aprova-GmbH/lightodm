# LightODM

[![PyPI version](https://badge.fury.io/py/lightodm.svg)](https://badge.fury.io/py/lightodm)
[![Python versions](https://img.shields.io/pypi/pyversions/lightodm.svg)](https://pypi.org/project/lightodm/)
[![Build Status](https://github.com/Aprova-GmbH/lightodm/workflows/Tests/badge.svg)](https://github.com/Aprova-GmbH/lightodm/actions)
[![Coverage](https://codecov.io/gh/Aprova-GmbH/lightodm/branch/main/graph/badge.svg)](https://codecov.io/gh/Aprova-GmbH/lightodm)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**Lightweight MongoDB ODM** - A simple, fast Object-Document Mapper for MongoDB with full async/sync support.

LightODM is a minimal alternative to [Beanie](https://github.com/roman-right/beanie) that provides essential ODM functionality without the complexity. Built on Pydantic v2, PyMongo, and Motor.

## Features

- **Dual Mode**: Full support for both sync (PyMongo) and async (Motor) operations
- **Lightweight**: Zero dependencies beyond Pydantic, PyMongo, and Motor
- **Type Safe**: Full type hints with py.typed marker
- **Pydantic v2**: Built on Pydantic v2 for robust validation
- **Simple API**: Clean, intuitive interface similar to Beanie
- **Flexible**: Optional connection - override `get_collection()` for custom setups
- **Thread Safe**: Singleton connection manager with automatic cleanup

## Installation

```bash
pip install lightodm
```

## Quick Start

### Define Your Models

```python
from lightodm import MongoBaseModel
from typing import Optional

class User(MongoBaseModel):
    class Settings:
        name = "users"  # MongoDB collection name

    name: str
    email: str
    age: Optional[int] = None
```

### Environment Setup

Set your MongoDB connection via environment variables:

```bash
export MONGO_URL="mongodb://localhost:27017"
export MONGO_USER="your_user"
export MONGO_PASSWORD="your_password"
export MONGO_DB_NAME="your_database"
```

### Sync Usage

```python
# Create and save
user = User(name="John Doe", email="john@example.com", age=30)
user.save()

# Retrieve by ID
user = User.get("some_id")

# Find documents
users = User.find({"age": {"$gte": 18}})
adult_user = User.find_one({"age": {"$gte": 18}})

# Update
User.update_one({"name": "John Doe"}, {"$set": {"age": 31}})

# Delete
user.delete()
User.delete_many({"age": {"$lt": 18}})

# Count
count = User.count({"age": {"$gte": 18}})

# Aggregation
pipeline = [{"$group": {"_id": "$age", "count": {"$sum": 1}}}]
results = User.aggregate(pipeline)
```

### Async Usage

```python
# Create and save
user = User(name="Jane Doe", email="jane@example.com", age=25)
await user.asave()

# Retrieve by ID
user = await User.aget("some_id")

# Find documents
users = await User.afind({"age": {"$gte": 18}})
adult_user = await User.afind_one({"age": {"$gte": 18}})

# Iterate over large result sets
async for user in User.afind_iter({"age": {"$gte": 18}}):
    print(user.name)

# Update
await User.aupdate_one({"name": "Jane Doe"}, {"$set": {"age": 26}})

# Delete
await user.adelete()
await User.adelete_many({"age": {"$lt": 18}})

# Count
count = await User.acount({"age": {"$gte": 18}})

# Aggregation
pipeline = [{"$group": {"_id": "$age", "count": {"$sum": 1}}}]
results = await User.aaggregate(pipeline)
```

## Advanced Usage

### Custom ID Generation

```python
from lightodm import MongoBaseModel, generate_id

class Product(MongoBaseModel):
    class Settings:
        name = "products"

    # Custom ID (default uses ObjectId)
    id: str = None

    name: str
    sku: str

# Default uses ObjectId
product = Product(name="Widget", sku="WDG-001")
print(product.id)  # Generated ObjectId string
```

### Custom Connection

Override `get_collection()` or `get_async_collection()` for custom connection logic:

```python
class CustomUser(MongoBaseModel):
    class Settings:
        name = "custom_users"

    name: str

    @classmethod
    def get_collection(cls):
        # Your custom connection logic
        from pymongo import MongoClient
        client = MongoClient("mongodb://custom-host:27017")
        return client["custom_db"]["custom_users"]
```

### Extra Fields

LightODM supports Pydantic's `extra='allow'` for dynamic fields:

```python
user = User(name="John", email="john@example.com", custom_field="value")
user.save()  # custom_field is preserved in MongoDB
```

### Bulk Operations

```python
# Sync
users = [
    User(name="User 1", email="user1@example.com"),
    User(name="User 2", email="user2@example.com"),
]
ids = User.insert_many(users)

# Async
ids = await User.ainsert_many(users)
```

## LightODM vs Beanie

| Feature | LightODM | Beanie |
|---------|----------|--------|
| **Dependencies** | Pydantic, PyMongo, Motor | Pydantic, PyMongo, Motor, lazy-model, toml |
| **Initialization** | Environment variables | `init_beanie()` required |
| **Sync Support** | ✅ Full | ❌ Async only |
| **Async Support** | ✅ Full | ✅ Full |
| **Connection** | Optional singleton | Required initialization |
| **Learning Curve** | Low | Medium |
| **Code Size** | ~500 lines | ~5000+ lines |
| **Use Case** | Simple projects, microservices | Complex applications |
| **Relations** | Manual (MongoDB refs) | Built-in with Link |
| **Migrations** | Manual | Manual |
| **Indexes** | Manual | Automatic |
| **Validation** | Pydantic v2 | Pydantic v2 |
| **Type Safety** | ✅ Full | ✅ Full |

**Choose LightODM if:**
- You want a simple, lightweight ODM
- You need both sync and async support
- You prefer minimal dependencies
- You want control over connection management
- You're building microservices or simple applications

**Choose Beanie if:**
- You need built-in relations and document links
- You want automatic index management
- You prefer async-first design
- You're building complex applications with many models

## API Reference

### MongoBaseModel

Base class for MongoDB document models.

#### Sync Methods

- `save(exclude_none=False) -> str` - Save/upsert document
- `delete() -> bool` - Delete document
- `get(id) -> Optional[T]` - Get by ID
- `find_one(filter, **kwargs) -> Optional[T]` - Find single document
- `find(filter, **kwargs) -> List[T]` - Find multiple documents
- `find_iter(filter, **kwargs) -> Iterator[T]` - Iterate over results
- `count(filter=None) -> int` - Count documents
- `update_one(filter, update, upsert=False) -> bool` - Update single document
- `update_many(filter, update) -> int` - Update multiple documents
- `delete_one(filter) -> bool` - Delete single document
- `delete_many(filter) -> int` - Delete multiple documents
- `aggregate(pipeline, **kwargs) -> List[dict]` - Run aggregation pipeline
- `insert_many(documents) -> List[str]` - Insert multiple documents

#### Async Methods

All sync methods have async equivalents prefixed with `a`:

- `asave()`, `adelete()`, `aget()`, `afind_one()`, `afind()`, `afind_iter()`, `acount()`,
- `aupdate_one()`, `aupdate_many()`, `adelete_one()`, `adelete_many()`,
- `aaggregate()`, `ainsert_many()`

### Connection Functions

```python
from lightodm import (
    get_mongo_connection,
    get_collection,
    get_database,
    get_client,
    get_async_database,
    get_async_client,
)

# Get singleton connection
conn = get_mongo_connection()

# Sync helpers
collection = get_collection("users")
db = get_database()
client = get_client()

# Async helpers
db = await get_async_database()
client = await get_async_client()
```

## Development

```bash
# Clone repository
git clone https://github.com/Aprova-GmbH/lightodm.git
cd lightodm

# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src tests
ruff check src tests --fix

# Type checking
mypy src
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Author

**Andrey Vykhodtsev** - [vya@aprova.ch](mailto:vya@aprova.ch)

## Links

- **Repository**: https://github.com/Aprova-GmbH/lightodm
- **Issues**: https://github.com/Aprova-GmbH/lightodm/issues
