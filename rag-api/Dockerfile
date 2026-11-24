# Build stage
FROM node:20-alpine AS builder

# pnpm vía corepack (el proyecto fija la versión en package.json)
RUN corepack enable && corepack prepare pnpm@10.34.9 --activate

WORKDIR /app

# Copiar manifiestos y lockfile de pnpm
COPY package.json pnpm-lock.yaml ./
COPY tsconfig*.json ./
COPY nest-cli.json ./

# Instalar dependencias
RUN pnpm install --frozen-lockfile

# Copiar código fuente
COPY src ./src

# Compilar
RUN pnpm build

# Production stage
FROM node:20-alpine AS production

RUN corepack enable && corepack prepare pnpm@10.34.9 --activate

WORKDIR /app

# dumb-init para manejo correcto de señales
RUN apk add --no-cache dumb-init

# Usuario no root
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nestjs -u 1001

# Dependencias de producción
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile --prod && pnpm store prune

# Copiar build
COPY --from=builder --chown=nestjs:nodejs /app/dist ./dist

USER nestjs

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:3000/api/health || exit 1

ENTRYPOINT ["dumb-init", "--"]
CMD ["node", "dist/main.js"]
