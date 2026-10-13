# ═══════════════════════════════════════════════
# Stage 1: Frontend builder (Node + Python)
# ═══════════════════════════════════════════════
FROM node:20-slim AS frontend-builder

WORKDIR /build

# Копируем frontend
COPY frontend/package*.json ./frontend/
RUN cd frontend && npm install --no-audit --no-fund

# Копируем core и scripts для трансформера
COPY core/ ./core/
COPY scripts/ ./scripts/

# Debian-образ — ставим Python через apt
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Трансформер Python → TS
RUN python3 /build/scripts/transform.py || true

# Копируем остальной frontend
COPY frontend/ ./frontend/

# Сборка фронта
RUN cd frontend && npm run build


# ═══════════════════════════════════════════════
# Stage 2: Backend runtime (Python)
# ═══════════════════════════════════════════════
FROM python:3.12-slim

WORKDIR /app

# Системные зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python-зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Backend-код
COPY . .

# Frontend dist из Stage 1
COPY --from=frontend-builder /build/frontend/dist ./frontend/dist

EXPOSE 8000

CMD ["python", "main.py"] 
