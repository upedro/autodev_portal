"""
MongoDB database connection and utilities
"""
import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import MongoClient
from config.settings import settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Singleton MongoDB database manager"""

    _instance: Optional["DatabaseManager"] = None
    _client: Optional[AsyncIOMotorClient] = None
    _db: Optional[AsyncIOMotorDatabase] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def client(self) -> AsyncIOMotorClient:
        """Get async MongoDB client"""
        if self._client is None:
            self._client = AsyncIOMotorClient(settings.mongodb_uri)
            logger.info(f"Connected to MongoDB: {settings.mongodb_uri}")
        return self._client

    @property
    def db(self) -> AsyncIOMotorDatabase:
        """Get async database instance"""
        if self._db is None:
            self._db = self.client[settings.mongodb_db_name]
            logger.info(f"Using database: {settings.mongodb_db_name}")
        return self._db

    async def close(self):
        """Close database connection"""
        if self._client:
            self._client.close()
            self._client = None
            self._db = None
            logger.info("MongoDB connection closed")

    async def init_indexes(self):
        """Initialize database indexes"""
        try:
            # Users collection indexes
            await self.db.usuarios.create_index("email", unique=True)
            await self.db.usuarios.create_index("created_at")

            # Clients collection indexes
            await self.db.clientes.create_index("codigo", unique=True)
            await self.db.clientes.create_index("ativo")

            # Solicitacoes collection indexes
            await self.db.solicitacoes.create_index("user_id")
            await self.db.solicitacoes.create_index("cliente_id")
            await self.db.solicitacoes.create_index("status")
            await self.db.solicitacoes.create_index("created_at")
            await self.db.solicitacoes.create_index([("user_id", 1), ("created_at", -1)])

            # Events collection indexes (for event-driven architecture)
            await self.db.eventos.create_index("solicitacao_id")
            await self.db.eventos.create_index("tipo_evento")
            await self.db.eventos.create_index("processado")
            await self.db.eventos.create_index("created_at")

            logger.info("Database indexes created successfully")

        except Exception as e:
            logger.error(f"Error creating indexes: {e}")
            raise


# Global database instance
db_manager = DatabaseManager()


def get_database() -> AsyncIOMotorDatabase:
    """Dependency injection for database"""
    return db_manager.db
