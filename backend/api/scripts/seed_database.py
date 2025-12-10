"""
Script to seed database with initial data
Run: python -m scripts.seed_database
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from config.settings import settings
from utils.auth import hash_password

async def seed_database():
    """Seed database with initial data"""
    print("🌱 Seeding database...")

    # Connect to MongoDB
    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client[settings.mongodb_db_name]

    try:
        # Create indexes
        print("📑 Creating indexes...")
        await db.usuarios.create_index("email", unique=True)
        await db.clientes.create_index("codigo", unique=True)
        print("✅ Indexes created")

        # Seed users
        print("\n👤 Seeding users...")
        users = [
            {
                "nome": "Admin User",
                "email": "admin@portal-rpa.com",
                "senha_hash": hash_password("admin123"),
                "ativo": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            },
            {
                "nome": "Test User",
                "email": "test@portal-rpa.com",
                "senha_hash": hash_password("test123"),
                "ativo": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            },
        ]

        for user in users:
            existing = await db.usuarios.find_one({"email": user["email"]})
            if not existing:
                result = await db.usuarios.insert_one(user)
                print(f"✅ Created user: {user['email']} (ID: {result.inserted_id})")
            else:
                print(f"⏭️  User already exists: {user['email']}")

        # Seed clients
        print("\n🏢 Seeding clients...")
        clients = [
            {
                "nome": "Agibank",
                "codigo": "agibank",
                "ativo": True,
                "descricao": "Banco Agibank - Serviços jurídicos automatizados",
                "config_rpa": {
                    "portal_url": "https://portal.agibank.com.br",
                    "timeout": 30,
                },
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            },
            {
                "nome": "Creditas",
                "codigo": "creditas",
                "ativo": True,
                "descricao": "Creditas - Plataforma de crédito digital",
                "config_rpa": {
                    "portal_url": "https://portal.creditas.com.br",
                    "timeout": 30,
                },
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            },
            {
                "nome": "Cogna Educação",
                "codigo": "cogna",
                "ativo": True,
                "descricao": "Cogna Educação - Grupo educacional",
                "config_rpa": {
                    "portal_url": "https://portal.cogna.com.br",
                    "timeout": 30,
                },
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            },
            {
                "nome": "Cliente Genérico (Demo)",
                "codigo": "demo",
                "ativo": True,
                "descricao": "Cliente genérico para testes e demonstrações",
                "config_rpa": {
                    "portal_url": "https://demo.portal-rpa.com",
                    "timeout": 30,
                },
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            },
        ]

        for client in clients:
            existing = await db.clientes.find_one({"codigo": client["codigo"]})
            if not existing:
                result = await db.clientes.insert_one(client)
                print(f"✅ Created client: {client['nome']} (ID: {result.inserted_id})")
            else:
                print(f"⏭️  Client already exists: {client['nome']}")

        print("\n✅ Database seeding completed successfully!")
        print("\n📝 Test credentials:")
        print("   Email: admin@portal-rpa.com")
        print("   Password: admin123")
        print("\n   Email: test@portal-rpa.com")
        print("   Password: test123")

    except Exception as e:
        print(f"\n❌ Error seeding database: {e}")
        raise
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(seed_database())
