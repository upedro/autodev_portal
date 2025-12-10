// =============================================================================
// MongoDB Initialization Script - Portal AutoDev
// =============================================================================

db = db.getSiblingDB('portal_autodev');

// Criar collections
db.createCollection('usuarios');
db.createCollection('clientes');
db.createCollection('solicitacoes');
db.createCollection('eventos');
db.createCollection('tasks');

// Indices para usuarios
db.usuarios.createIndex({ "email": 1 }, { unique: true });

// Indices para clientes
db.clientes.createIndex({ "codigo": 1 }, { unique: true });
db.clientes.createIndex({ "ativo": 1 });

// Indices para solicitacoes
db.solicitacoes.createIndex({ "user_id": 1 });
db.solicitacoes.createIndex({ "cliente_id": 1 });
db.solicitacoes.createIndex({ "status": 1 });
db.solicitacoes.createIndex({ "created_at": -1 });
db.solicitacoes.createIndex({ "user_id": 1, "created_at": -1 });

// Indices para eventos
db.eventos.createIndex({ "solicitacao_id": 1 });
db.eventos.createIndex({ "tipo_evento": 1 });
db.eventos.createIndex({ "processado": 1 });
db.eventos.createIndex({ "created_at": -1 });

// Indices para tasks (RPA)
db.tasks.createIndex({ "process_number": 1 });
db.tasks.createIndex({ "status": 1 });
db.tasks.createIndex({ "client_name": 1 });
db.tasks.createIndex({ "created_at": -1 });
db.tasks.createIndex({ "status": 1, "client_name": 1, "created_at": -1 });
db.tasks.createIndex({ "portal_metadata.solicitacao_id": 1 });

// Inserir clientes padrao
db.clientes.insertMany([
  {
    nome: "COGNA Educacao",
    codigo: "cogna",
    ativo: true,
    descricao: "Sistema eLaw COGNA",
    config_rpa: {
      portal_url: "https://elaw.com.br",
      timeout: 300
    },
    created_at: new Date(),
    updated_at: new Date()
  },
  {
    nome: "Loft",
    codigo: "loft",
    ativo: true,
    descricao: "Sistema BCLegal Loft",
    config_rpa: {
      portal_url: "https://bclegal.com.br",
      timeout: 300
    },
    created_at: new Date(),
    updated_at: new Date()
  },
  {
    nome: "SuperSim",
    codigo: "supersim",
    ativo: true,
    descricao: "Sistema Lexxy SuperSim",
    config_rpa: {
      portal_url: "https://lexxy.com.br",
      timeout: 300
    },
    created_at: new Date(),
    updated_at: new Date()
  },
  {
    nome: "Mercantil",
    codigo: "mercantil",
    ativo: true,
    descricao: "Sistema eLaw Mercantil",
    config_rpa: {
      portal_url: "https://elaw.com.br",
      timeout: 300
    },
    created_at: new Date(),
    updated_at: new Date()
  }
]);

print('MongoDB inicializado com sucesso para Portal AutoDev');
print('Collections criadas: usuarios, clientes, solicitacoes, eventos, tasks');
print('Clientes inseridos: cogna, loft, supersim, mercantil');
