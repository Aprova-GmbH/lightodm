"""Tests for MongoConnection singleton"""

import os

import pytest

from lightodm.connection import MongoConnection, connect, get_database


class TestMongoConnection:
    """Test MongoConnection singleton class"""

    @pytest.mark.integration
    def test_singleton_pattern(self, reset_connection):
        """Test that MongoConnection is a singleton with real MongoDB"""
        conn1 = MongoConnection()
        conn2 = MongoConnection()

        assert conn1 is conn2
        assert MongoConnection._instance is conn1

    @pytest.mark.integration
    def test_get_collection_sync(self, reset_connection):
        """Test getting synchronous collection with real MongoDB"""
        conn = MongoConnection()
        collection = conn.get_collection("test_collection")

        assert collection is not None
        assert collection.name == "test_collection"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_async_client(self, reset_connection):
        """Test getting async client with real MongoDB"""
        conn = MongoConnection()
        client = await conn.get_async_client()

        assert client is not None
        # Verify it's a real Motor client by checking it can ping
        result = await client.admin.command("ping")
        assert result["ok"] == 1

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_async_database(self, reset_connection):
        """Test getting async database with real MongoDB"""
        conn = MongoConnection()
        db = await conn.get_async_database()

        assert db is not None
        assert db.name == os.getenv("MONGO_DB_NAME", "test_db")

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_async_database_custom_name(self, reset_connection):
        """Test getting async database with custom name using real MongoDB"""
        conn = MongoConnection()
        db = await conn.get_async_database("custom_db")

        assert db is not None
        assert db.name == "custom_db"

    @pytest.mark.integration
    def test_close_connection(self, reset_connection):
        """Test connection cleanup with real MongoDB"""
        conn = MongoConnection()
        _ = conn.client  # Initialize sync client

        # Verify client exists
        assert conn._client is not None

        conn.close_connection()

        assert conn._client is None
        assert conn._db is None

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_close_async_connection(self, reset_connection):
        """Test async connection cleanup with real MongoDB"""
        conn = MongoConnection()
        await conn.get_async_client()  # Initialize async client

        # Verify async client exists
        assert conn._async_client is not None

        conn.close_connection()

        assert conn._async_client is None

    @pytest.mark.integration
    def test_missing_env_vars_raises_error(self, reset_connection):
        """Test that missing environment variables raise error"""
        # Save current env vars
        saved_env = {
            key: os.environ.get(key)
            for key in ["MONGO_URL", "MONGO_USER", "MONGO_PASSWORD", "MONGO_DB_NAME"]
        }

        try:
            # Clear environment variables
            for key in ["MONGO_URL", "MONGO_USER", "MONGO_PASSWORD"]:
                if key in os.environ:
                    del os.environ[key]

            with pytest.raises(ValueError, match="MongoDB connection parameters"):
                MongoConnection()
        finally:
            # Restore env vars
            for key, value in saved_env.items():
                if value is not None:
                    os.environ[key] = value
                elif key in os.environ:
                    del os.environ[key]

    @pytest.mark.integration
    def test_connect_helper(self, reset_connection):
        """Test connect helper function with real MongoDB"""
        # Use environment variables to get connection details
        url = os.getenv("MONGO_URL", "mongodb://localhost:27017")
        username = os.getenv("MONGO_USER", "test")
        password = os.getenv("MONGO_PASSWORD", "test")
        db_name = os.getenv("MONGO_DB_NAME", "test_db")

        db = connect(
            url=url,
            username=username,
            password=password,
            db_name=db_name,
        )

        assert db is not None
        assert MongoConnection._instance is not None

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_async_client_lazy_initialization(self, reset_connection):
        """Test that async client is only created when requested with real MongoDB"""
        conn = MongoConnection()

        # Async client should not be initialized yet
        assert conn._async_client is None

        # Now request async client
        client = await conn.get_async_client()

        assert client is not None
        assert conn._async_client is not None

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_async_client_connection_error(self, reset_connection):
        """Test handling of async connection errors"""
        # Save current env vars
        saved_env = {
            key: os.environ.get(key)
            for key in ["MONGO_URL", "MONGO_USER", "MONGO_PASSWORD", "MONGO_DB_NAME"]
        }

        try:
            # Set invalid connection URL
            os.environ["MONGO_URL"] = "mongodb://invalid:99999"
            os.environ["MONGO_USER"] = "invalid"
            os.environ["MONGO_PASSWORD"] = "invalid"
            os.environ["MONGO_DB_NAME"] = "invalid"

            # Force reset to pick up new env vars
            MongoConnection._instance = None

            conn = MongoConnection()

            # Attempting to get async client with invalid URL should fail
            with pytest.raises(ConnectionError):
                await conn.get_async_client()

            # Ensure client is cleaned up on error
            assert conn._async_client is None
        finally:
            # Restore env vars
            for key, value in saved_env.items():
                if value is not None:
                    os.environ[key] = value
                elif key in os.environ:
                    del os.environ[key]
