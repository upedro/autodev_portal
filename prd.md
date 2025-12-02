🧩 PRD – Módulo de Solicitação de Serviços via CNJ
📘 Contexto

O objetivo deste módulo é permitir que advogados e departamentos jurídicos solicitem serviços automatizados fornecidos pela plataforma, inserindo números de processos CNJ e escolhendo o tipo de serviço desejado.
O primeiro serviço implementado será:
“Buscar documentos no site do cliente” — operação em que o sistema (robô) acessa o portal do cliente e baixa todos os documentos anexos disponíveis para aquele processo.

🎯 Objetivo do MVP

Permitir que o usuário:

Faça login na plataforma web (frontend React);

Informe números de processos (CNJ) manualmente ou via upload de planilha;

Escolha o cliente (empresa contratante) e o serviço desejado;

Envie a solicitação para execução automática (FastAPI);

Visualize o status da execução e faça o download dos documentos quando disponíveis.

🏗️ Arquitetura Geral
Usuário Web (React)
│
▼
[FastAPI Gateway]
├── Auth Service
├── Solicitações API
├── Storage Manager (S3/Azure)
└── Queue Manager → Robôs RPA
▼
[Worker RPA]
▼
[Cloud Storage + Banco de Dados]

🖥️ Frontend (React)
Stack

React + Vite

Ant Design (UI)

Axios (requisições)

Zustand (estado global)

React Router DOM (navegação)

Telas Principais

1. Login

Campos: email, senha

Autenticação via API /auth/login

Armazena token JWT no localStorage

2. Dashboard Inicial

Exibe resumo de solicitações recentes (status, cliente, serviço, criado_em)

Botão: Nova Solicitação

3. Formulário de Solicitação

Campos:

Cliente (select, busca via /clientes)

Serviço (select, apenas “Buscar Documentos” no MVP)

Inserção de CNJs

Opção 1: Textarea (um CNJ por linha)

Opção 2: Upload .xlsx

Botão: Enviar Solicitação

Após envio:

Mostra número de solicitações criadas

Redireciona para tela de acompanhamento

4. Acompanhamento

Tabela com:

CNJ

Cliente

Serviço

Status (pendente, em_execucao, concluido, erro)

Ação: Download (quando concluído)

Atualização via polling a cada 15 segundos

⚙️ Backend (FastAPI)
Stack

FastAPI

MongoDB (persistência)

Celery + Redis (fila de execução)

S3/Azure Blob Storage (armazenamento de documentos)

Pydantic Models (validação)

Uvicorn + Gunicorn (produção)

Endpoints Principais
Método Rota Descrição
POST /auth/login Autentica usuário e retorna JWT
GET /clientes Lista clientes disponíveis (para os quais há robôs ativos)
POST /solicitacoes Cria solicitação de serviço
GET /solicitacoes/{id} Consulta status da solicitação
GET /solicitacoes Lista solicitações do usuário
GET /documentos/{solicitacao_id} Retorna links de download dos documentos concluídos
Modelo Solicitacao
class Solicitacao(BaseModel):
id: str
user_id: str
cliente_id: str
servico: str
cnjs: list[str]
status: Literal["pendente", "em_execucao", "concluido", "erro"]
resultados: list[dict] | None
created_at: datetime
updated_at: datetime

🤖 Worker RPA

Recebe jobs via Celery (buscar_documentos).

Executa scraping ou automação via Selenium (já implementada pela equipe da Luana).

Salva:

Metadados no Mongo (status, links, erros).

Arquivos em S3/Azure com nome padrão {cliente}/{cnj}/{arquivo.pdf}.

Em caso de sucesso, atualiza status para concluido.

🧱 Estrutura de Pastas
.
├── frontend/
│ ├── src/
│ │ ├── pages/
│ │ │ ├── Login.jsx
│ │ │ ├── Dashboard.jsx
│ │ │ └── SolicitarServico.jsx
│ │ ├── store/
│ │ ├── api/
│ │ └── components/
│ └── vite.config.js
└── backend/
├── main.py
├── routers/
│ ├── auth.py
│ ├── solicitacoes.py
│ ├── clientes.py
│ └── documentos.py
├── models/
├── workers/
└── config/

🧩 Integrações Futuras (Fase 2+)

Autenticação via OAuth (Google/Microsoft)

Notificações de conclusão via e-mail ou WhatsApp

Integração direta com API do cliente (quando a chave for liberada)

Dashboard com KPIs de tempo médio de execução, sucesso e falhas

📊 Métricas de Sucesso
Indicador Meta
Tempo médio de resposta API < 1s
Tempo de execução RPA/documentos < 10 min
Taxa de sucesso das solicitações > 95%
Feedback positivo dos usuários (NPS) ≥ 8
📅 Cronograma (Setup + MVP)
Etapa Duração Responsável
Design UX/UI (wireframe e fluxo) 3 dias Pedro + Luana
Setup do FastAPI + MongoDB 2 dias Pedro
Criação do frontend React 3 dias Front-end Dev
Integração API + Upload Planilha 2 dias Pedro
Conexão com RPA e Storage 2 dias Luana
Testes e Deploy 2 dias Equipe
Total estimado 14 dias úteis (~3 semanas)
🚀 Entregável Final

Frontend minimalista funcional (login + solicitação + acompanhamento)

API FastAPI documentada com Swagger

Worker RPA conectado via fila e salvando documentos

Banco de dados e storage integrados

MVP pronto para demonstração a clientes e parceiros
