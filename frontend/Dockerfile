# =============================================================================
# Portal AutoDev - Frontend Dockerfile (React/Vite)
# =============================================================================

FROM node:20-alpine

WORKDIR /app

# Copia package files
COPY package*.json ./

# Instala dependencias
RUN npm install

# Copia codigo fonte
COPY . .

# Expoe porta do Vite
EXPOSE 5173

# Comando de desenvolvimento
CMD ["npm", "run", "dev", "--", "--host"]
