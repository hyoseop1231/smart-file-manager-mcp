FROM python:3.11-slim

# Install system dependencies including build tools for psutil
RUN apt-get update && apt-get install -y \
    curl \
    libmagic1 \
    supervisor \
    build-essential \
    python3-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application files
COPY enhanced_api.py .
COPY db_manager.py .
COPY indexer.py .
COPY llm_organizer.py .
COPY enhanced_llm_organizer.py .
COPY smart_model_selector.py .
COPY scheduler.py .
COPY mafm_bridge.py .
COPY organizer_bridge.py .
COPY ollama_bridge.py .
COPY multi_agent_manager.py .
COPY embedding_manager.py .
COPY db_connection_pool.py .
COPY performance_monitor.py .

# Copy additional directories
COPY mafm/ ./mafm/
COPY organizer/ ./organizer/

# Create directories for data and logs
RUN mkdir -p /data/db /data/embeddings /data/metadata /var/log/supervisor

# Create supervisor configuration
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8001
ENV DB_PATH=/data/db/file-index.db
ENV EMBEDDINGS_PATH=/data/embeddings
ENV METADATA_PATH=/data/metadata

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Expose port
EXPOSE 8001

# Run both API server and scheduler using supervisor
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]