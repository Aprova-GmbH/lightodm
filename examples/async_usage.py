"""
Asynchronous Usage Example for LightODM

This example demonstrates using LightODM's async API with Motor for
asynchronous MongoDB operations.
"""

import asyncio
from typing import Optional
from datetime import datetime
from lightodm import connect, MongoBaseModel


# Define a User model
class User(MongoBaseModel):
    """User document model"""

    class Settings:
        name = "users"

    name: str
    email: str
    age: Optional[int] = None
    created_at: datetime = datetime.now()


# Define a Post model
class Post(MongoBaseModel):
    """Post document model with reference to User"""

    class Settings:
        name = "posts"

    title: str
    content: str
    author_id: str  # Reference to User
    created_at: datetime = datetime.now()
    likes: int = 0

    async def get_author(self) -> Optional[User]:
        """Get the author of this post"""
        return await User.aget(self.author_id)


async def main():
    """Main async function demonstrating CRUD operations"""

    # Connect to MongoDB
    print("Connecting to MongoDB...")
    connect(
        url="mongodb://localhost:27017",
        db_name="lightodm_async_example",
    )

    print("\n=== Async CRUD Operations ===\n")

    # CREATE - Create and save users
    print("1. Creating users...")
    user1 = User(name="Alice", email="alice@example.com", age=28)
    await user1.asave()
    print(f"Created user: {user1.name} (ID: {user1.id})")

    user2 = User(name="Bob", email="bob@example.com", age=35)
    await user2.asave()
    print(f"Created user: {user2.name} (ID: {user2.id})")

    user3 = User(name="Charlie", email="charlie@example.com", age=42)
    await user3.asave()
    print(f"Created user: {user3.name} (ID: {user3.id})")

    # CREATE - Create posts
    print("\n2. Creating posts...")
    post1 = Post(
        title="First Post",
        content="This is my first post!",
        author_id=user1.id,
    )
    await post1.asave()
    print(f"Created post: {post1.title} (ID: {post1.id})")

    post2 = Post(
        title="Async Programming",
        content="Async/await makes concurrent code easier!",
        author_id=user1.id,
    )
    await post2.asave()
    print(f"Created post: {post2.title} (ID: {post2.id})")

    # READ - Get by ID
    print("\n3. Retrieving user by ID...")
    found_user = await User.aget(user1.id)
    if found_user:
        print(f"Found user: {found_user.name}, {found_user.email}")

    # READ - Find one
    print("\n4. Finding user by email...")
    found_user = await User.afind_one({"email": "bob@example.com"})
    if found_user:
        print(f"Found user: {found_user.name}")

    # READ - Find multiple
    print("\n5. Finding users older than 30...")
    older_users = await User.afind({"age": {"$gt": 30}})
    for user in older_users:
        print(f"  - {user.name}, age {user.age}")

    # READ - Async iteration for large datasets
    print("\n6. Iterating through all posts...")
    async for post in Post.afind_iter({}):
        author = await post.get_author()
        print(f"  - '{post.title}' by {author.name if author else 'Unknown'}")

    # UPDATE - Update one document
    print("\n7. Updating user age...")
    result = await User.aupdate_one(
        {"_id": user1.id}, {"$set": {"age": 29}}
    )
    if result:
        updated_user = await User.aget(user1.id)
        print(f"Updated {updated_user.name}'s age to {updated_user.age}")

    # UPDATE - Update many documents
    print("\n8. Incrementing likes on all posts...")
    modified_count = await Post.aupdate_many(
        {}, {"$inc": {"likes": 1}}
    )
    print(f"Updated {modified_count} posts")

    # UPDATE - Instance update
    print("\n9. Updating post title...")
    post1.title = "My Updated First Post"
    await post1.asave()
    print(f"Updated post title to: {post1.title}")

    # COUNT - Count documents
    print("\n10. Counting documents...")
    total_users = await User.acount()
    total_posts = await Post.acount()
    print(f"Total users: {total_users}")
    print(f"Total posts: {total_posts}")

    # Count with filter
    adult_users = await User.acount({"age": {"$gte": 18}})
    print(f"Adult users (18+): {adult_users}")

    # AGGREGATION - Group posts by author
    print("\n11. Aggregating posts by author...")
    pipeline = [
        {
            "$group": {
                "_id": "$author_id",
                "post_count": {"$sum": 1},
                "total_likes": {"$sum": "$likes"},
            }
        }
    ]

    results = await Post.aaggregate(pipeline)
    for result in results:
        author = await User.aget(result["_id"])
        if author:
            print(
                f"  - {author.name}: {result['post_count']} posts, "
                f"{result['total_likes']} total likes"
            )

    # BULK INSERT - Insert many documents
    print("\n12. Bulk inserting users...")
    new_users = [
        User(name=f"User{i}", email=f"user{i}@example.com", age=20 + i)
        for i in range(5)
    ]
    ids = await User.ainsert_many(new_users)
    print(f"Inserted {len(ids)} users")

    # DELETE - Delete one document
    print("\n13. Deleting a post...")
    deleted = await Post.adelete_one({"_id": post2.id})
    if deleted:
        print(f"Deleted post: {post2.title}")

    # DELETE - Delete instance
    print("\n14. Deleting user instance...")
    user_to_delete = await User.aget(user3.id)
    if user_to_delete:
        await user_to_delete.adelete()
        print(f"Deleted user: {user_to_delete.name}")

    # DELETE - Delete many
    print("\n15. Deleting bulk inserted users...")
    deleted_count = await User.adelete_many(
        {"email": {"$regex": r"^user\d+@example\.com$"}}
    )
    print(f"Deleted {deleted_count} users")

    # Final count
    print("\n=== Final Statistics ===")
    final_users = await User.acount()
    final_posts = await Post.acount()
    print(f"Remaining users: {final_users}")
    print(f"Remaining posts: {final_posts}")

    # Cleanup - delete all test data
    print("\n16. Cleaning up test data...")
    await User.adelete_many({})
    await Post.adelete_many({})
    print("Cleanup complete!")


async def advanced_async_patterns():
    """Demonstrate advanced async patterns"""

    print("\n=== Advanced Async Patterns ===\n")

    # Concurrent operations
    print("1. Running concurrent queries...")

    async def get_user_stats(user_id: str):
        user = await User.aget(user_id)
        post_count = await Post.acount({"author_id": user_id})
        return user, post_count

    # Create test data
    user1 = User(name="Alice", email="alice@example.com")
    user2 = User(name="Bob", email="bob@example.com")
    await user1.asave()
    await user2.asave()

    # Run queries concurrently
    results = await asyncio.gather(
        get_user_stats(user1.id), get_user_stats(user2.id)
    )

    for user, count in results:
        print(f"  - {user.name}: {count} posts")

    # Cleanup
    await User.adelete_many({})


if __name__ == "__main__":
    print("LightODM Async Usage Example")
    print("=" * 50)

    # Run main async function
    asyncio.run(main())

    # Run advanced patterns
    asyncio.run(advanced_async_patterns())

    print("\nExample complete!")
