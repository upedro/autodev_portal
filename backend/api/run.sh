#!/bin/bash
# Script para executar o servidor FastAPI

# Development mode com Uvicorn
if [ "$1" == "dev" ]; then
    echo "Starting FastAPI in development mode..."
    uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
# Production mode com Gunicorn
elif [ "$1" == "prod" ]; then
    echo "Starting FastAPI in production mode..."
    gunicorn backend.main:app \
        --workers 4 \
        --worker-class uvicorn.workers.UvicornWorker \
        --bind 0.0.0.0:8000 \
        --timeout 120
else
    echo "Usage: ./run.sh [dev|prod]"
    echo "  dev  - Run in development mode with auto-reload"
    echo "  prod - Run in production mode with Gunicorn"
fi

