#!/bin/bash

echo "🚀 Portal Web CNJ - Quick Start Script"
echo "======================================"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Criando arquivo .env..."
    cat > .env << 'ENVFILE'
JWT_SECRET_KEY=my-super-secret-jwt-key-change-in-production-2024
AZURE_STORAGE_CONNECTION_STRING=
AZURE_STORAGE_CONTAINER=portal-documentos
ENVFILE
    echo "✅ Arquivo .env criado"
fi

# Check if backend/.env exists
if [ ! -f backend/.env ]; then
    echo "📝 Criando backend/.env..."
    cat > backend/.env << 'ENVFILE'
MONGODB_URI=mongodb://mongodb:27017
MONGODB_DB_NAME=portal_rpa
REDIS_URL=redis://redis:6379/0
JWT_SECRET_KEY=my-super-secret-jwt-key-change-in-production-2024
AZURE_STORAGE_CONNECTION_STRING=
AZURE_STORAGE_CONTAINER=portal-documentos
ENVFILE
    echo "✅ Arquivo backend/.env criado"
fi

echo ""
echo "🐳 Subindo containers Docker..."
docker-compose up -d

echo ""
echo "⏳ Aguardando serviços iniciarem (30 segundos)..."
sleep 30

echo ""
echo "🌱 Populando banco de dados com dados iniciais..."
docker-compose exec -T backend python -m scripts.seed_database

echo ""
echo "✅ Setup concluído!"
echo ""
echo "📍 Acesse:"
echo "   Frontend: http://localhost:5173"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "🔑 Credenciais de teste:"
echo "   Email: admin@portal-rpa.com"
echo "   Senha: admin123"
echo ""
