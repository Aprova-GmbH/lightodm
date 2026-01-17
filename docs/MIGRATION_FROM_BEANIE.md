# Migration from Beanie to LightODM

This guide helps you migrate from Beanie to LightODM.

## Key Differences

| Aspect | Beanie | LightODM |
|--------|--------|----------|
| Initialization | Required `init_beanie()` | Environment variables |
| Sync Support | No | Yes |
| Async Support | Yes | Yes |
| Model Definition | `Document` class | `MongoBaseModel` class |
| Collection Name | `Settings.name` | `Settings.name` |
| ID Field | `id` (PydanticObjectId) | `id` (str) |
| Relations | Built-in `Link` | Manual MongoDB refs |

## Step-by-Step Migration

### 1. Model Definition

**Beanie:**
```python
from beanie import Document
from typing import Optional

class User(Document):
    name: str
    email: str
    age: Optional[int] = None

    class Settings:
        name = "users"
```

**LightODM:**
```python
from lightodm import MongoBaseModel
from typing import Optional

class User(MongoBaseModel):
    name: str
    email: str
    age: Optional[int] = None

    class Settings:
        name = "users"
```

**Changes:**
- Replace `from beanie import Document` with `from lightodm import MongoBaseModel`
- Replace `Document` with `MongoBaseModel`
- Settings class remains the same

### 2. Initialization

**Beanie:**
```python
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

async def init():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    await init_beanie(
        database=client.db_name,
        document_models=[User, Product, Order]
    )
```

**LightODM:**
```python
# Set environment variables (once, at app startup)
import os
os.environ["MONGO_URL"] = "mongodb://localhost:27017"
os.environ["MONGO_USER"] = "username"
os.environ["MONGO_PASSWORD"] = "password"
os.environ["MONGO_DB_NAME"] = "db_name"

# No initialization needed - connection is lazy and automatic
```

**Changes:**
- Remove `init_beanie()` calls
- Set environment variables instead
- Connection happens automatically on first use

### 3. CRUD Operations

Most CRUD operations are similar, but LightODM also supports synchronous operations.

#### Create & Save

**Beanie:**
```python
# Async only
user = User(name="John", email="john@example.com")
await user.insert()  # or await user.save()
```

**LightODM:**
```python
# Sync
user = User(name="John", email="john@example.com")
user.save()

# Async
user = User(name="John", email="john@example.com")
await user.asave()
```

**Changes:**
- `insert()` → `save()` (sync) or `asave()` (async)
- Both use upsert semantics

#### Find

**Beanie:**
```python
# Find all
users = await User.find_all().to_list()

# Find with filter
users = await User.find(User.age >= 18).to_list()

# Find one
user = await User.find_one(User.email == "john@example.com")
```

**LightODM:**
```python
# Sync - Find all
users = User.find({})

# Sync - Find with filter
users = User.find({"age": {"$gte": 18}})

# Sync - Find one
user = User.find_one({"email": "john@example.com"})

# Async versions
users = await User.afind({})
users = await User.afind({"age": {"$gte": 18}})
user = await User.afind_one({"email": "john@example.com"})
```

**Changes:**
- Use MongoDB query syntax instead of Beanie's query builder
- Add `a` prefix for async methods
- `find_all()` → `find({})`
- `to_list()` not needed - returns list directly

#### Get by ID

**Beanie:**
```python
user = await User.get(user_id)
```

**LightODM:**
```python
# Sync
user = User.get(user_id)

# Async
user = await User.aget(user_id)
```

**Changes:**
- Add sync version with `get()`
- Async version is `aget()`

#### Update

**Beanie:**
```python
# Update instance
user.age = 31
await user.save()

# Update query
await User.find(User.name == "John").update({"$set": {"age": 31}})
```

**LightODM:**
```python
# Sync - Update instance
user.age = 31
user.save()

# Sync - Update query
User.update_one({"name": "John"}, {"$set": {"age": 31}})
User.update_many({"age": {"$lt": 18}}, {"$set": {"minor": True}})

# Async versions
await user.asave()
await User.aupdate_one({"name": "John"}, {"$set": {"age": 31}})
await User.aupdate_many({"age": {"$lt": 18}}, {"$set": {"minor": True}})
```

**Changes:**
- Use MongoDB update operators directly
- `find().update()` → `update_one()` or `update_many()`

#### Delete

**Beanie:**
```python
# Delete instance
await user.delete()

# Delete query
await User.find(User.age < 18).delete()
```

**LightODM:**
```python
# Sync - Delete instance
user.delete()

# Sync - Delete query
User.delete_one({"age": {"$lt": 18}})
User.delete_many({"age": {"$lt": 18}})

# Async versions
await user.adelete()
await User.adelete_one({"age": {"$lt": 18}})
await User.adelete_many({"age": {"$lt": 18}})
```

**Changes:**
- `find().delete()` → `delete_one()` or `delete_many()`

### 4. Aggregation

**Beanie:**
```python
pipeline = [
    {"$group": {"_id": "$age", "count": {"$sum": 1}}}
]
results = await User.aggregate(pipeline).to_list()
```

**LightODM:**
```python
pipeline = [
    {"$group": {"_id": "$age", "count": {"$sum": 1}}}
]

# Sync
results = User.aggregate(pipeline)

# Async
results = await User.aaggregate(pipeline)
```

**Changes:**
- `aggregate()` (sync) or `aaggregate()` (async)
- No need for `to_list()`

### 5. Relationships

Beanie supports built-in `Link` for relationships. LightODM uses manual MongoDB references.

**Beanie:**
```python
from beanie import Link

class Order(Document):
    user: Link[User]
    items: List[str]

    class Settings:
        name = "orders"

# Usage
order = Order(user=user, items=["item1"])
await order.insert()

# Fetch with relation
await order.fetch_link(Order.user)
print(order.user.name)
```

**LightODM:**
```python
class Order(MongoBaseModel):
    user_id: str  # Store user ID
    items: List[str]

    class Settings:
        name = "orders"

# Usage
order = Order(user_id=user.id, items=["item1"])
order.save()

# Fetch relation manually
user = User.get(order.user_id)
print(user.name)
```

**Changes:**
- Store IDs instead of using `Link`
- Fetch related documents manually
- More explicit but gives you full control

### 6. Indexes

**Beanie:**
```python
class User(Document):
    email: Indexed(str, unique=True)
    name: str

    class Settings:
        name = "users"
        indexes = [
            IndexModel([("name", 1), ("age", -1)])
        ]
```

**LightODM:**
```python
from pymongo import ASCENDING, DESCENDING

class User(MongoBaseModel):
    email: str
    name: str

    class Settings:
        name = "users"

# Create indexes manually
collection = User.get_collection()
collection.create_index("email", unique=True)
collection.create_index([("name", ASCENDING), ("age", DESCENDING)])
```

**Changes:**
- Create indexes manually using PyMongo
- More control but requires explicit management
- Can create indexes in a setup script

### 7. Validation

Both use Pydantic validators, so no changes needed:

```python
from pydantic import field_validator

class User(MongoBaseModel):  # or Document for Beanie
    email: str

    @field_validator('email')
    def validate_email(cls, v):
        if '@' not in v:
            raise ValueError('Invalid email')
        return v.lower()
```

## Complete Migration Example

### Before (Beanie)

```python
from beanie import Document, init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional

class User(Document):
    name: str
    email: str
    age: Optional[int] = None

    class Settings:
        name = "users"

async def main():
    # Initialize
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    await init_beanie(database=client.db_name, document_models=[User])

    # Create
    user = User(name="John", email="john@example.com", age=30)
    await user.insert()

    # Find
    users = await User.find(User.age >= 18).to_list()

    # Update
    user.age = 31
    await user.save()

    # Delete
    await user.delete()
```

### After (LightODM)

```python
from lightodm import MongoBaseModel
from typing import Optional
import os

# Set environment variables (once)
os.environ["MONGO_URL"] = "mongodb://localhost:27017"
os.environ["MONGO_USER"] = "username"
os.environ["MONGO_PASSWORD"] = "password"
os.environ["MONGO_DB_NAME"] = "db_name"

class User(MongoBaseModel):
    name: str
    email: str
    age: Optional[int] = None

    class Settings:
        name = "users"

async def main():
    # No initialization needed!

    # Create
    user = User(name="John", email="john@example.com", age=30)
    await user.asave()

    # Find
    users = await User.afind({"age": {"$gte": 18}})

    # Update
    user.age = 31
    await user.asave()

    # Delete
    await user.adelete()

# Bonus: Sync version
def main_sync():
    user = User(name="John", email="john@example.com", age=30)
    user.save()

    users = User.find({"age": {"$gte": 18}})

    user.age = 31
    user.save()

    user.delete()
```

## Migration Checklist

- [ ] Replace `Document` with `MongoBaseModel`
- [ ] Replace `from beanie import ...` with `from lightodm import ...`
- [ ] Remove `init_beanie()` calls
- [ ] Set environment variables for MongoDB connection
- [ ] Replace query builder syntax with MongoDB query syntax
- [ ] Update async method calls to use `a` prefix (`aget`, `asave`, etc.)
- [ ] Add sync versions where needed
- [ ] Replace `Link` relationships with ID references
- [ ] Create indexes manually if using them
- [ ] Update `insert()` calls to `save()` or `asave()`
- [ ] Remove `to_list()` calls from find operations
- [ ] Test all CRUD operations

## Need Help?

If you encounter issues during migration, please:
1. Check the [API reference](../README.md#api-reference)
2. Review the [examples](../examples/)
3. Open an issue on [GitHub](https://github.com/Aprova-GmbH/lightodm/issues)
