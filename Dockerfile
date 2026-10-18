# Etapa 1: compila o front-end React
FROM node:22-alpine AS web
WORKDIR /web
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Etapa 2: API Flask que também serve o front-end (mesma origem = cookie de sessão seguro)
FROM python:3.12-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .
COPY --from=web /web/dist ./static
RUN useradd -m app && chown -R app /app
USER app
ENV AUTO_CREATE_DB=0
# aplica as migrações do banco e só então sobe o servidor
CMD flask --app app db upgrade && exec gunicorn app:app --bind 0.0.0.0:${PORT:-10000} --workers 1 --threads 8 --timeout 120
