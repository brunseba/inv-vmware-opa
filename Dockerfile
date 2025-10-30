# syntax=docker/dockerfile:1

# ============================================================================
# Stage 1: Builder - Install dependencies and build application
# ============================================================================
FROM python:3.12-slim AS builder

# Set working directory
WORKDIR /build

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install uv package manager
RUN pip install --no-cache-dir uv

# Install dependencies using uv
RUN uv pip install --system --no-cache -r pyproject.toml

# ============================================================================
# Stage 2: Runtime - Slim final image
# ============================================================================
FROM python:3.12-slim

# OpenContainers labels
LABEL org.opencontainers.image.title="VMware Inventory Dashboard" \
      org.opencontainers.image.description="Interactive web dashboard for VMware vSphere inventory analysis with RVTools support" \
      org.opencontainers.image.version="0.6.0" \
      org.opencontainers.image.authors="VMware Inventory Team" \
      org.opencontainers.image.url="https://github.com/brunseba/inv-vmware-opa" \
      org.opencontainers.image.documentation="https://github.com/brunseba/inv-vmware-opa/blob/main/README.md" \
      org.opencontainers.image.source="https://github.com/brunseba/inv-vmware-opa" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.vendor="VMware Inventory Project" \
      org.opencontainers.image.base.name="python:3.12-slim"

# Set labels for better Docker Hub integration
LABEL maintainer="sebastien.brun@lepervier.org" \
      version="0.6.0" \
      description="VMware vSphere Inventory Dashboard"

# Install runtime dependencies only
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd -r vmwareinv && \
    useradd -r -g vmwareinv -u 1000 -d /app -s /sbin/nologin vmwareinv

# Set working directory
WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=vmwareinv:vmwareinv . .

# Create data directory for database
RUN mkdir -p /app/data && \
    chown -R vmwareinv:vmwareinv /app/data

# Create volume mount points
VOLUME ["/app/data"]

# Expose Streamlit default port
EXPOSE 8501

# Switch to non-root user
USER vmwareinv

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8501/_stcore/health', timeout=5)" || exit 1

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    VMWARE_INV_DB_URL="sqlite:///data/vmware_inventory.db" \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_SERVER_ENABLE_CORS=false \
    STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=true

# Entrypoint using fullweb command
ENTRYPOINT ["vmware-inv", "fullweb"]

# Default arguments (can be overridden)
CMD ["--host", "0.0.0.0", "--port", "8501", "--db-path", "/app/data/vmware_inventory.db"]
