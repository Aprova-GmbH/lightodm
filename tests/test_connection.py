"""Tests for MongoConnection singleton"""

import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from lightodm.connection import MongoConnection, connect
from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient


class TestMongoConnection:
    """Test MongoConnection singleton class"""

    def test_singleton_pattern(self, reset_connection):
        """Test that MongoConnection is a singleton"""
        conn1 = MongoConnection()
        conn2 = MongoConnection()

        assert conn1 is conn2
        assert MongoConnection._instance is conn1

    def test_get_collection_sync(self, mock_mongo_client, monkeypatch, reset_connection):
        """Test getting synchronous collection"""
        # Mock the MongoClient
        monkeypatch.setenv("MONGO_URL", "mongodb://localhost:27017")
        monkeypatch.setenv("MONGO_USER", "testuser")
        monkeypatch.setenv("MONGO_PASSWORD", "testpass")
        monkeypatch.setenv("MONGO_DB_NAME", "testdb")

        with patch("lightodm.connection.MongoClient", return_value=mock_mongo_client):
            conn = MongoConnection()
            collection = conn.get_collection("test_collection")

            assert collection is not None
            assert collection.name == "test_collection"

    @pytest.mark.asyncio
    async def test_get_async_client(self, monkeypatch, reset_connection):
        """Test getting async client"""
        monkeypatch.setenv("MONGO_URL", "mongodb://localhost:27017")
        monkeypatch.setenv("MONGO_USER", "testuser")
        monkeypatch.setenv("MONGO_PASSWORD", "testpass")
        monkeypatch.setenv("MONGO_DB_NAME", "testdb")

        mock_motor_client = MagicMock(spec=AsyncIOMotorClient)
        mock_admin = MagicMock()
        mock_admin.command = MagicMock(return_value={"ok": 1})
        mock_motor_client.admin = mock_admin

        with patch("lightodm.connection.AsyncIOMotorClient", return_value=mock_motor_client):
            conn = MongoConnection()
            client = await conn.get_async_client()

            assert client is not None
            # Verify ping was called
            mock_admin.command.assert_called_with("ping")

    @pytest.mark.asyncio
    async def test_get_async_database(self, monkeypatch, reset_connection):
        """Test getting async database"""
        monkeypatch.setenv("MONGO_URL", "mongodb://localhost:27017")
        monkeypatch.setenv("MONGO_USER", "testuser")
        monkeypatch.setenv("MONGO_PASSWORD", "testpass")
        monkeypatch.setenv("MONGO_DB_NAME", "testdb")

        mock_motor_client = MagicMock(spec=AsyncIOMotorClient)
        mock_admin = MagicMock()
        mock_admin.command = MagicMock(return_value={"ok": 1})
        mock_motor_client.admin = mock_admin
        mock_db = MagicMock()
        mock_motor_client.__getitem__ = MagicMock(return_value=mock_db)

        with patch("lightodm.connection.AsyncIOMotorClient", return_value=mock_motor_client):
            conn = MongoConnection()
            db = await conn.get_async_database()

            assert db is not None

    @pytest.mark.asyncio
    async def test_get_async_database_custom_name(self, monkeypatch, reset_connection):
        """Test getting async database with custom name"""
        monkeypatch.setenv("MONGO_URL", "mongodb://localhost:27017")
        monkeypatch.setenv("MONGO_USER", "testuser")
        monkeypatch.setenv("MONGO_PASSWORD", "testpass")
        monkeypatch.setenv("MONGO_DB_NAME", "testdb")

        mock_motor_client = MagicMock(spec=AsyncIOMotorClient)
        mock_admin = MagicMock()
        mock_admin.command = MagicMock(return_value={"ok": 1})
        mock_motor_client.admin = mock_admin
        mock_custom_db = MagicMock()

        def getitem_side_effect(key):
            if key == "custom_db":
                return mock_custom_db
            return MagicMock()

        mock_motor_client.__getitem__ = MagicMock(side_effect=getitem_side_effect)

        with patch("lightodm.connection.AsyncIOMotorClient", return_value=mock_motor_client):
            conn = MongoConnection()
            db = await conn.get_async_database("custom_db")

            assert db is mock_custom_db

    def test_close_connection(self, mock_mongo_client, monkeypatch, reset_connection):
        """Test connection cleanup"""
        monkeypatch.setenv("MONGO_URL", "mongodb://localhost:27017")
        monkeypatch.setenv("MONGO_USER", "testuser")
        monkeypatch.setenv("MONGO_PASSWORD", "testpass")
        monkeypatch.setenv("MONGO_DB_NAME", "testdb")

        with patch("lightodm.connection.MongoClient", return_value=mock_mongo_client):
            conn = MongoConnection()
            _ = conn.client  # Initialize sync client

            conn.close_connection()

            assert conn._client is None
            assert conn._db is None
            mock_mongo_client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_async_connection(self, monkeypatch, reset_connection):
        """Test async connection cleanup"""
        monkeypatch.setenv("MONGO_URL", "mongodb://localhost:27017")
        monkeypatch.setenv("MONGO_USER", "testuser")
        monkeypatch.setenv("MONGO_PASSWORD", "testpass")
        monkeypatch.setenv("MONGO_DB_NAME", "testdb")

        mock_motor_client = MagicMock(spec=AsyncIOMotorClient)
        mock_admin = MagicMock()
        mock_admin.command = MagicMock(return_value={"ok": 1})
        mock_motor_client.admin = mock_admin

        with patch("lightodm.connection.AsyncIOMotorClient", return_value=mock_motor_client):
            conn = MongoConnection()
            await conn.get_async_client()  # Initialize async client

            conn.close_connection()

            assert conn._async_client is None
            mock_motor_client.close.assert_called_once()

    def test_missing_env_vars_raises_error(self, reset_connection):
        """Test that missing environment variables raise error"""
        # Clear environment variables
        for key in ["MONGO_URL", "MONGO_USER", "MONGO_PASSWORD"]:
            if key in os.environ:
                del os.environ[key]

        with pytest.raises(ValueError, match="MongoDB connection parameters"):
            MongoConnection()

    def test_connect_helper(self, monkeypatch, reset_connection):
        """Test connect helper function"""
        mock_client = MagicMock(spec=MongoClient)
        mock_admin = MagicMock()
        mock_admin.command = MagicMock(return_value={"ok": 1})
        mock_client.admin = mock_admin

        with patch("lightodm.connection.MongoClient", return_value=mock_client):
            db = connect(
                url="mongodb://localhost:27017",
                username="testuser",
                password="testpass",
                db_name="testdb"
            )

            assert db is not None
            assert MongoConnection._instance is not None

    @pytest.mark.asyncio
    async def test_async_client_lazy_initialization(self, monkeypatch, reset_connection):
        """Test that async client is only created when requested"""
        monkeypatch.setenv("MONGO_URL", "mongodb://localhost:27017")
        monkeypatch.setenv("MONGO_USER", "testuser")
        monkeypatch.setenv("MONGO_PASSWORD", "testpass")
        monkeypatch.setenv("MONGO_DB_NAME", "testdb")

        mock_sync_client = MagicMock(spec=MongoClient)
        mock_sync_admin = MagicMock()
        mock_sync_admin.command = MagicMock(return_value={"ok": 1})
        mock_sync_client.admin = mock_sync_admin

        with patch("lightodm.connection.MongoClient", return_value=mock_sync_client):
            conn = MongoConnection()

            # Async client should not be initialized yet
            assert conn._async_client is None

            # Now request async client
            mock_motor_client = MagicMock(spec=AsyncIOMotorClient)
            mock_motor_admin = MagicMock()
            mock_motor_admin.command = MagicMock(return_value={"ok": 1})
            mock_motor_client.admin = mock_motor_admin

            with patch("lightodm.connection.AsyncIOMotorClient", return_value=mock_motor_client):
                client = await conn.get_async_client()

                assert client is not None
                assert conn._async_client is mock_motor_client

    @pytest.mark.asyncio
    async def test_async_client_connection_error(self, monkeypatch, reset_connection):
        """Test handling of async connection errors"""
        monkeypatch.setenv("MONGO_URL", "mongodb://localhost:27017")
        monkeypatch.setenv("MONGO_USER", "testuser")
        monkeypatch.setenv("MONGO_PASSWORD", "testpass")
        monkeypatch.setenv("MONGO_DB_NAME", "testdb")

        mock_sync_client = MagicMock(spec=MongoClient)
        mock_sync_admin = MagicMock()
        mock_sync_admin.command = MagicMock(return_value={"ok": 1})
        mock_sync_client.admin = mock_sync_admin

        with patch("lightodm.connection.MongoClient", return_value=mock_sync_client):
            conn = MongoConnection()

            # Mock async client that fails to connect
            mock_motor_client = MagicMock(spec=AsyncIOMotorClient)
            mock_motor_admin = MagicMock()
            mock_motor_admin.command = MagicMock(side_effect=Exception("Connection failed"))
            mock_motor_client.admin = mock_motor_admin

            with patch("lightodm.connection.AsyncIOMotorClient", return_value=mock_motor_client):
                with pytest.raises(Exception, match="Connection failed"):
                    await conn.get_async_client()

                # Ensure client is cleaned up on error
                assert conn._async_client is None
