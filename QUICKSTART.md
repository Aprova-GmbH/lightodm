# Quick Start Guide

This guide will help you get started with LightODM in minutes.

## Installation

### From PyPI (once published)

```bash
pip install lightodm
```

### For Development

```bash
# Clone the repository
git clone https://github.com/Aprova-GmbH/lightodm.git
cd lightodm

# Install in development mode
pip install -e .

# Or with dev dependencies
pip install -e ".[dev]"
```

## Basic Setup

### 1. Configure MongoDB Connection

Set environment variables for your MongoDB connection:

```bash
export MONGO_URL="mongodb://localhost:27017"
export MONGO_USER="your_username"
export MONGO_PASSWORD="your_password"
export MONGO_DB_NAME="your_database"
```

Or create a `.env` file:

```env
MONGO_URL=mongodb://localhost:27017
MONGO_USER=your_username
MONGO_PASSWORD=your_password
MONGO_DB_NAME=your_database
```

### 2. Define Your First Model

Create a file `models.py`:

```python
from lightodm import MongoBaseModel
from typing import Optional

class User(MongoBaseModel):
    class Settings:
        name = "users"  # MongoDB collection name

    name: str
    email: str
    age: Optional[int] = None
    active: bool = True
```

### 3. Use Your Model

#### Synchronous Usage

```python
from models import User

# Create a user
user = User(name="Alice", email="alice@example.com", age=25)
user.save()
print(f"Created user with ID: {user.id}")

# Find users
users = User.find({"active": True})
for u in users:
    print(f"{u.name}: {u.email}")

# Get by ID
user = User.get("some_id")
if user:
    print(f"Found: {user.name}")

# Update
User.update_one({"email": "alice@example.com"}, {"$set": {"age": 26}})

# Delete
user.delete()
```

#### Asynchronous Usage

```python
import asyncio
from models import User

async def main():
    # Create a user
    user = User(name="Bob", email="bob@example.com", age=30)
    await user.asave()
    print(f"Created user with ID: {user.id}")

    # Find users
    users = await User.afind({"active": True})
    for u in users:
        print(f"{u.name}: {u.email}")

    # Get by ID
    user = await User.aget("some_id")
    if user:
        print(f"Found: {user.name}")

    # Update
    await User.aupdate_one(
        {"email": "bob@example.com"},
        {"$set": {"age": 31}}
    )

    # Delete
    await user.adelete()

asyncio.run(main())
```

## Complete Example

Here's a complete working example:

```python
import asyncio
from typing import Optional
from lightodm import MongoBaseModel

class Product(MongoBaseModel):
    class Settings:
        name = "products"

    name: str
    price: float
    sku: str
    in_stock: bool = True
    quantity: Optional[int] = None

async def demo():
    # Create products
    products = [
        Product(name="Widget", price=9.99, sku="WDG-001", quantity=100),
        Product(name="Gadget", price=19.99, sku="GDG-001", quantity=50),
        Product(name="Doohickey", price=14.99, sku="DOO-001", quantity=75),
    ]

    # Bulk insert
    ids = await Product.ainsert_many(products)
    print(f"Inserted {len(ids)} products")

    # Find in-stock products
    in_stock = await Product.afind({"in_stock": True})
    print(f"\nIn-stock products: {len(in_stock)}")
    for p in in_stock:
        print(f"  {p.name}: ${p.price} ({p.quantity} units)")

    # Find products under $15
    cheap_products = await Product.afind({"price": {"$lt": 15.0}})
    print(f"\nProducts under $15: {len(cheap_products)}")

    # Update product price
    await Product.aupdate_one(
        {"sku": "WDG-001"},
        {"$set": {"price": 12.99}}
    )
    print("\nUpdated Widget price")

    # Aggregation - average price
    pipeline = [
        {"$group": {
            "_id": None,
            "avg_price": {"$avg": "$price"},
            "total_quantity": {"$sum": "$quantity"}
        }}
    ]
    result = await Product.aaggregate(pipeline)
    if result:
        print(f"\nAverage price: ${result[0]['avg_price']:.2f}")
        print(f"Total quantity: {result[0]['total_quantity']}")

    # Clean up
    await Product.adelete_many({})
    print("\nCleaned up test data")

if __name__ == "__main__":
    asyncio.run(demo())
```

## Next Steps

- Read the [full documentation](README.md)
- Check out [examples/](examples/) for more use cases
- Learn about [custom connections](examples/custom_connection.py)
- Explore the [API reference](README.md#api-reference)

## Common Patterns

### Pagination

```python
# Get page 2, 10 items per page
page = 2
page_size = 10
skip = (page - 1) * page_size

users = User.find({}, skip=skip, limit=page_size)
```

### Sorting

```python
# Sort by age descending
users = User.find({}, sort=[("age", -1)])

# Async
users = await User.afind({}, sort=[("age", -1)])
```

### Projection

```python
# Only get name and email fields
users = User.find({}, projection={"name": 1, "email": 1})
```

### Memory-Efficient Iteration

```python
# Process large result sets without loading all into memory
for user in User.find_iter({"active": True}):
    process_user(user)

# Async
async for user in User.afind_iter({"active": True}):
    await process_user(user)
```

## Troubleshooting

### Connection Issues

If you get connection errors, verify:
1. MongoDB is running
2. Environment variables are set correctly
3. User has proper permissions
4. Network/firewall allows connection

### Import Errors

If imports fail, ensure dependencies are installed:

```bash
pip install pydantic pymongo motor
```

### Model Not Found

Make sure your model has a `Settings` class with a `name` attribute:

```python
class MyModel(MongoBaseModel):
    class Settings:
        name = "my_collection"  # Required!

    field: str
```
