# Stage 1: Build frontend
FROM node:20-alpine AS frontend-build

WORKDIR /app/web
COPY web/package*.json ./
RUN npm ci
COPY web/ ./
RUN npm run build

# Stage 2: Python application
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd --gid 1001 autoagent && \
    useradd --uid 1001 --gid autoagent --create-home autoagent

# Copy Python project files
COPY pyproject.toml ./
COPY runner.py ./
COPY autoagent.yaml ./
COPY agent/ ./agent/
COPY api/ ./api/
COPY configs/ ./configs/
COPY context/ ./context/
COPY control/ ./control/
COPY core/ ./core/
COPY data/ ./data/
COPY deployer/ ./deployer/
COPY evals/ ./evals/
COPY graders/ ./graders/
COPY judges/ ./judges/
COPY logger/ ./logger/
COPY observer/ ./observer/
COPY optimizer/ ./optimizer/
COPY registry/ ./registry/

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Copy built frontend
COPY --from=frontend-build /app/web/dist ./web/dist

# Create data directory and set ownership
RUN mkdir -p /app/data /app/.autoagent/logs && \
    chown -R autoagent:autoagent /app/data /app/.autoagent

# Environment
ENV AUTOAGENT_DB=/app/data/conversations.db
ENV AUTOAGENT_CONFIGS=/app/data/configs
ENV AUTOAGENT_MEMORY_DB=/app/data/optimizer_memory.db
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

USER autoagent

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/health/ready || exit 1

ENTRYPOINT ["python", "runner.py"]
CMD ["server", "--host", "0.0.0.0", "--port", "8000"]
