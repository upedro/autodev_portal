"""
FastAPI application entry point for Portal de Automação RPA
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, solicitacoes, clientes, documentos, rpa

app = FastAPI(
    title="Portal de Automação RPA",
    description="API para solicitação de serviços automatizados via CNJ",
    version="0.1.0"
)

# CORS middleware para permitir requisições do frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(clientes.router, prefix="/api/clientes", tags=["clientes"])
app.include_router(solicitacoes.router, prefix="/api/solicitacoes", tags=["solicitacoes"])
app.include_router(documentos.router, prefix="/api/documentos", tags=["documentos"])
app.include_router(rpa.router, prefix="/api/rpa", tags=["rpa"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Portal de Automação RPA API",
        "version": "0.1.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

