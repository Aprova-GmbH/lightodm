"""
FastAPI Integration Example for LightODM

This example demonstrates building a complete REST API using FastAPI and LightODM
for MongoDB operations.

To run this example:
    pip install fastapi uvicorn

Then:
    uvicorn fastapi_example:app --reload

API will be available at http://localhost:8000
API docs at http://localhost:8000/docs
"""

from fastapi import FastAPI, HTTPException, Query, status
from fastapi.responses import JSONResponse
from lightodm import connect, MongoBaseModel
from typing import Optional, List
from pydantic import EmailStr, Field
from datetime import datetime
import os

# Initialize FastAPI app
app = FastAPI(
    title="LightODM FastAPI Example",
    description="REST API built with FastAPI and LightODM",
    version="1.0.0",
)


# Define models
class User(MongoBaseModel):
    """User document model"""

    class Settings:
        name = "users"

    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    age: Optional[int] = Field(None, ge=0, le=150)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    async def asave(self, **kwargs):
        """Override save to update timestamp"""
        self.updated_at = datetime.now()
        return await super().asave(**kwargs)


class Post(MongoBaseModel):
    """Post document model"""

    class Settings:
        name = "posts"

    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    author_id: str
    published: bool = False
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    async def get_author(self) -> Optional[User]:
        """Get the author of this post"""
        return await User.aget(self.author_id)

    async def asave(self, **kwargs):
        """Override save to update timestamp"""
        self.updated_at = datetime.now()
        return await super().asave(**kwargs)


# Response models (for API documentation)
class UserResponse(User):
    """User response with ID"""

    pass


class PostResponse(Post):
    """Post response with ID"""

    pass


class PostWithAuthor(Post):
    """Post response with author information"""

    author: Optional[User] = None


# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize database connection on startup"""
    mongo_url = os.getenv("MONGO_URL", "mongodb://localhost:27017")
    db_name = os.getenv("MONGO_DB_NAME", "lightodm_fastapi_example")

    connect(url=mongo_url, db_name=db_name)

    # Create indexes
    user_collection = await User.get_async_collection()
    await user_collection.create_index([("email", 1)], unique=True)

    post_collection = await Post.get_async_collection()
    await post_collection.create_index([("author_id", 1)])
    await post_collection.create_index([("published", 1)])

    print("✅ Database connection established and indexes created")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    from lightodm.connection import MongoConnection

    conn = MongoConnection()
    conn.close_connection()
    print("✅ Database connection closed")


# Health check endpoint
@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint"""
    return {"message": "LightODM FastAPI Example API", "status": "healthy"}


# User endpoints
@app.post(
    "/users/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Users"],
)
async def create_user(user: User):
    """Create a new user"""
    try:
        await user.asave()
        return user
    except Exception as e:
        if "duplicate key error" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}",
        )


@app.get("/users/", response_model=List[UserResponse], tags=["Users"])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    age_min: Optional[int] = Query(None, ge=0),
    age_max: Optional[int] = Query(None, le=150),
):
    """List users with pagination and optional age filters"""
    filter_query = {}

    if age_min is not None or age_max is not None:
        filter_query["age"] = {}
        if age_min is not None:
            filter_query["age"]["$gte"] = age_min
        if age_max is not None:
            filter_query["age"]["$lte"] = age_max

    users = await User.afind(
        filter_query, skip=skip, limit=limit, sort=[("created_at", -1)]
    )
    return users


@app.get("/users/{user_id}", response_model=UserResponse, tags=["Users"])
async def get_user(user_id: str):
    """Get a specific user by ID"""
    user = await User.aget(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user


@app.put("/users/{user_id}", response_model=UserResponse, tags=["Users"])
async def update_user(user_id: str, user_update: User):
    """Update a user"""
    existing_user = await User.aget(user_id)
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Keep the same ID and created_at
    user_update.id = user_id
    user_update.created_at = existing_user.created_at

    try:
        await user_update.asave()
        return user_update
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user: {str(e)}",
        )


@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Users"])
async def delete_user(user_id: str):
    """Delete a user"""
    user = await User.aget(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Also delete all posts by this user
    await Post.adelete_many({"author_id": user_id})

    await user.adelete()
    return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content=None)


@app.get("/users/{user_id}/posts", response_model=List[PostResponse], tags=["Users"])
async def get_user_posts(
    user_id: str, published: Optional[bool] = Query(None)
):
    """Get all posts by a specific user"""
    user = await User.aget(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    filter_query = {"author_id": user_id}
    if published is not None:
        filter_query["published"] = published

    posts = await Post.afind(filter_query, sort=[("created_at", -1)])
    return posts


# Post endpoints
@app.post(
    "/posts/",
    response_model=PostResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Posts"],
)
async def create_post(post: Post):
    """Create a new post"""
    # Verify author exists
    author = await User.aget(post.author_id)
    if not author:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Author does not exist",
        )

    try:
        await post.asave()
        return post
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create post: {str(e)}",
        )


@app.get("/posts/", response_model=List[PostWithAuthor], tags=["Posts"])
async def list_posts(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    published: Optional[bool] = Query(None),
):
    """List posts with pagination and optional published filter"""
    filter_query = {}
    if published is not None:
        filter_query["published"] = published

    posts = await Post.afind(
        filter_query, skip=skip, limit=limit, sort=[("created_at", -1)]
    )

    # Enrich with author information
    posts_with_authors = []
    for post in posts:
        author = await post.get_author()
        post_dict = post.model_dump()
        post_dict["author"] = author
        posts_with_authors.append(PostWithAuthor(**post_dict))

    return posts_with_authors


@app.get("/posts/{post_id}", response_model=PostWithAuthor, tags=["Posts"])
async def get_post(post_id: str):
    """Get a specific post by ID with author information"""
    post = await Post.aget(post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )

    author = await post.get_author()
    post_dict = post.model_dump()
    post_dict["author"] = author

    return PostWithAuthor(**post_dict)


@app.put("/posts/{post_id}", response_model=PostResponse, tags=["Posts"])
async def update_post(post_id: str, post_update: Post):
    """Update a post"""
    existing_post = await Post.aget(post_id)
    if not existing_post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )

    # Verify new author exists if author_id changed
    if post_update.author_id != existing_post.author_id:
        author = await User.aget(post_update.author_id)
        if not author:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New author does not exist",
            )

    # Keep the same ID and created_at
    post_update.id = post_id
    post_update.created_at = existing_post.created_at

    try:
        await post_update.asave()
        return post_update
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update post: {str(e)}",
        )


@app.patch(
    "/posts/{post_id}/publish", response_model=PostResponse, tags=["Posts"]
)
async def publish_post(post_id: str):
    """Publish a post"""
    post = await Post.aget(post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )

    post.published = True
    await post.asave()
    return post


@app.patch(
    "/posts/{post_id}/unpublish", response_model=PostResponse, tags=["Posts"]
)
async def unpublish_post(post_id: str):
    """Unpublish a post"""
    post = await Post.aget(post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )

    post.published = False
    await post.asave()
    return post


@app.delete(
    "/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Posts"]
)
async def delete_post(post_id: str):
    """Delete a post"""
    post = await Post.aget(post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )

    await post.adelete()
    return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content=None)


# Analytics endpoints
@app.get("/analytics/stats", tags=["Analytics"])
async def get_stats():
    """Get overall statistics"""
    total_users = await User.acount()
    total_posts = await Post.acount()
    published_posts = await Post.acount({"published": True})

    return {
        "total_users": total_users,
        "total_posts": total_posts,
        "published_posts": published_posts,
        "draft_posts": total_posts - published_posts,
    }


@app.get("/analytics/top-authors", tags=["Analytics"])
async def get_top_authors(limit: int = Query(10, ge=1, le=100)):
    """Get top authors by post count"""
    pipeline = [
        {"$group": {"_id": "$author_id", "post_count": {"$sum": 1}}},
        {"$sort": {"post_count": -1}},
        {"$limit": limit},
    ]

    results = await Post.aaggregate(pipeline)

    # Enrich with author information
    top_authors = []
    for result in results:
        author = await User.aget(result["_id"])
        if author:
            top_authors.append(
                {
                    "author": author,
                    "post_count": result["post_count"],
                }
            )

    return top_authors


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
