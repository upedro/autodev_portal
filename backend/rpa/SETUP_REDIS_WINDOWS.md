# 🔧 Setup Redis no Windows - Guia Completo

## Opção 1: Memurai (Redis para Windows - Recomendado) ⭐

### Instalação Rápida

1. **Baixar Memurai (Redis nativo para Windows)**
   - Acesse: https://www.memurai.com/get-memurai
   - Clique em "Download Memurai Developer"
   - É gratuito e funciona como Redis

2. **Instalar**
   - Execute o instalador
   - Next → Next → Install
   - Marque "Start Memurai automatically"

3. **Verificar se está rodando**
   ```powershell
   # No PowerShell ou CMD
   netstat -an | findstr "6379"
   ```

   Deve mostrar:
   ```
   TCP    0.0.0.0:6379           0.0.0.0:0              LISTENING
   ```

4. **Pronto!** O Redis está rodando automaticamente

---

## Opção 2: WSL2 com Redis (Mais completo)

### Se você tem WSL2 instalado:

```powershell
# No PowerShell (como Administrador)
wsl sudo apt-get update
wsl sudo apt-get install redis-server -y
wsl sudo service redis-server start

# Verificar
wsl redis-cli ping
# Deve retornar: PONG
```

---

## Opção 3: Redis no Docker Desktop

### Se preferir usar Docker:

1. **Instalar Docker Desktop**
   - Baixe: https://www.docker.com/products/docker-desktop/
   - Instale e reinicie o computador

2. **Iniciar Docker Desktop**
   - Abra o Docker Desktop
   - Aguarde até ficar "Running"

3. **Executar Redis**
   ```powershell
   docker run -d -p 6379:6379 --name redis redis:latest
   ```

4. **Verificar**
   ```powershell
   docker ps
   # Deve mostrar o container redis rodando
   ```

---

## Opção 4: Redis para Windows (Versão Antiga - Funciona)

### Download e Execução Manual:

1. **Baixar Redis para Windows**
   - Acesse: https://github.com/tporadowski/redis/releases
   - Baixe: `Redis-x64-5.0.14.1.zip`

2. **Extrair**
   - Extraia para: `C:\Redis`

3. **Executar**
   ```powershell
   # Navegar até a pasta
   cd C:\Redis

   # Executar Redis
   .\redis-server.exe
   ```

   Deixe este terminal aberto (Redis rodando)

4. **Verificar (em outro terminal)**
   ```powershell
   cd C:\Redis
   .\redis-cli.exe ping
   # Deve retornar: PONG
   ```

---

## ✅ Verificar se Redis está funcionando

Após instalar por qualquer método, teste:

### Teste 1: Verificar Porta
```powershell
netstat -an | findstr "6379"
```
Deve mostrar:
```
TCP    0.0.0.0:6379           0.0.0.0:0              LISTENING
```

### Teste 2: Testar Conexão com Python
```powershell
python -c "import redis; r = redis.Redis(host='localhost', port=6379); print('OK' if r.ping() else 'FALHOU')"
```
Deve imprimir: `OK`

---

## 🚀 Continuar com o Teste

Após o Redis estar rodando:

### Passo 1: Verificar Redis
```powershell
# Teste com Python
python -c "import redis; print('Redis OK!' if redis.Redis().ping() else 'Redis FALHOU')"
```

### Passo 2: Iniciar API (Terminal 1)
```powershell
python main.py
```

### Passo 3: Iniciar Worker (Terminal 2)
```powershell
celery -A worker worker --beat --loglevel=info --pool=solo
```

### Passo 4: Executar Teste (Terminal 3)
```powershell
python test_flow.py
```

---

## 🔥 Solução Mais Rápida (Se não quiser instalar Redis agora)

### Usar Redis na Nuvem (Grátis)

1. **Criar conta no Redis Cloud**
   - Acesse: https://redis.com/try-free/
   - Crie conta gratuita
   - Crie um banco Redis

2. **Pegar URL de Conexão**
   - Formato: `redis://default:password@host:port`

3. **Atualizar .env**
   ```env
   CELERY_BROKER_URL=redis://default:sua_senha@seu_host:porta/0
   CELERY_RESULT_BACKEND=redis://default:sua_senha@seu_host:porta/0
   ```

4. **Pronto!** Não precisa instalar Redis local

---

## 💡 Recomendação

Para testes rápidos no Windows:

1. **Melhor opção:** Memurai (gratuito, instalação simples, funciona como serviço)
   - https://www.memurai.com/get-memurai

2. **Segunda opção:** Redis Cloud (gratuito, sem instalação)
   - https://redis.com/try-free/

3. **Terceira opção:** WSL2 (se já tiver instalado)

---

## ❓ FAQ

### Redis não inicia
```powershell
# Verificar se já está rodando
netstat -an | findstr "6379"

# Matar processo (se necessário)
taskkill /F /IM redis-server.exe
```

### Porta 6379 em uso
```powershell
# Descobrir quem está usando
netstat -ano | findstr "6379"

# Verificar processo
tasklist | findstr "PID_NUMERO"
```

### Worker não conecta ao Redis
```powershell
# Verificar se Redis está acessível
python -c "import redis; redis.Redis().ping()"

# Se falhar, Redis não está rodando ou na porta errada
```

---

## 🎯 Próximo Passo

Escolha uma opção acima, instale o Redis, e depois:

1. Volte para [START_TESTE.md](START_TESTE.md)
2. Continue do Passo 4 (Abrir 2 Terminais)

Boa sorte! 🚀
