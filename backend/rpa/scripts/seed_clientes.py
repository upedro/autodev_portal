"""
Script para popular a collection 'clientes' no MongoDB do Portal.
Deve ser executado uma vez para configurar os clientes iniciais.

Uso:
    python scripts/seed_clientes.py
"""
import sys
import os

# Adiciona o diretório pai ao path para imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from pymongo import MongoClient

from settings import settings


def seed_clientes():
    """
    Popula a collection 'clientes' com os clientes suportados pelo RPA.
    Usa upsert para evitar duplicatas.
    """
    print(f"Conectando ao MongoDB: {settings.PORTAL_MONGODB_DB_NAME}")

    client = MongoClient(settings.MONGODB_URL)
    db = client[settings.PORTAL_MONGODB_DB_NAME]

    # Lista de clientes suportados
    clientes = [
        {
            "nome": "COGNA",
            "codigo": "cogna",
            "ativo": True,
            "descricao": "eLaw COGNA - Sistema de gestão jurídica",
            "config_rpa": {
                "sistema": "elaw_cogna",
                "timeout_minutos": 30,
                "max_retries": 3,
            },
        },
        {
            "nome": "Loft",
            "codigo": "loft",
            "ativo": True,
            "descricao": "BCLegal Loft - Sistema jurídico com SSO",
            "config_rpa": {
                "sistema": "bclegal",
                "timeout_minutos": 30,
                "max_retries": 3,
            },
        },
        {
            "nome": "SuperSim",
            "codigo": "supersim",
            "ativo": True,
            "descricao": "Lexxy SuperSim - Sistema de automação jurídica",
            "config_rpa": {
                "sistema": "lexxy",
                "timeout_minutos": 30,
                "max_retries": 3,
            },
        },
        {
            "nome": "Mercantil",
            "codigo": "mercantil",
            "ativo": True,
            "descricao": "eLaw Mercantil - Sistema de gestão jurídica",
            "config_rpa": {
                "sistema": "elaw_cogna",  # Usa mesmo sistema que COGNA
                "timeout_minutos": 30,
                "max_retries": 3,
            },
        },
    ]

    inserted = 0
    updated = 0

    for cliente in clientes:
        # Adiciona timestamps
        cliente["updated_at"] = datetime.utcnow()

        # Verifica se já existe
        existing = db.clientes.find_one({"codigo": cliente["codigo"]})

        if existing:
            # Atualiza (mantém created_at original)
            result = db.clientes.update_one(
                {"codigo": cliente["codigo"]},
                {"$set": cliente}
            )
            if result.modified_count > 0:
                updated += 1
                print(f"  [ATUALIZADO] {cliente['nome']} ({cliente['codigo']})")
            else:
                print(f"  [SEM MUDANÇA] {cliente['nome']} ({cliente['codigo']})")
        else:
            # Insere novo
            cliente["created_at"] = datetime.utcnow()
            db.clientes.insert_one(cliente)
            inserted += 1
            print(f"  [INSERIDO] {cliente['nome']} ({cliente['codigo']})")

    print(f"\nResumo:")
    print(f"  - Inseridos: {inserted}")
    print(f"  - Atualizados: {updated}")
    print(f"  - Total de clientes: {len(clientes)}")

    # Cria índice no campo 'codigo'
    db.clientes.create_index("codigo", unique=True)
    print("\nÍndice criado em 'codigo' (unique)")

    client.close()
    print("\nSeed concluído com sucesso!")


def list_clientes():
    """Lista todos os clientes cadastrados"""
    print(f"Conectando ao MongoDB: {settings.PORTAL_MONGODB_DB_NAME}")

    client = MongoClient(settings.MONGODB_URL)
    db = client[settings.PORTAL_MONGODB_DB_NAME]

    clientes = list(db.clientes.find({}))

    if not clientes:
        print("\nNenhum cliente cadastrado.")
        return

    print(f"\nClientes cadastrados ({len(clientes)}):")
    print("-" * 60)

    for c in clientes:
        status = "ATIVO" if c.get("ativo", True) else "INATIVO"
        sistema = c.get("config_rpa", {}).get("sistema", "N/A")
        print(f"  {c['nome']:<15} | {c['codigo']:<12} | {sistema:<15} | {status}")

    client.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Gerenciamento de clientes do Portal RPA")
    parser.add_argument(
        "--list",
        action="store_true",
        help="Lista clientes cadastrados"
    )
    parser.add_argument(
        "--seed",
        action="store_true",
        help="Popula/atualiza clientes"
    )

    args = parser.parse_args()

    if args.list:
        list_clientes()
    elif args.seed:
        seed_clientes()
    else:
        # Comportamento padrão: seed
        seed_clientes()
