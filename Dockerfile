# ═══════════════════════════════════════════════
# Stage 1: Frontend builder (Node + Python)
# ═══════════════════════════════════════════════
FROM node:20-alpine AS frontend-builder

WORKDIR /build

# Копируем frontend
COPY frontend/package*.json ./frontend/
RUN cd frontend && npm install --no-audit --no-fund

# Копируем core и scripts для трансформера
COPY core/ ./core/
COPY scripts/ ./scripts/

# Node-образ не имеет Python — ставим
RUN apk add --no-cache python3 py3-pip

# Трансформер Python → TS
RUN python3 /build/scripts/transform.py || true

# Копируем остальной frontend
COPY frontend/ ./frontend/

# Сборка фронта
RUN cd frontend && npm run build
