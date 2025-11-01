# Docker Deployment Guide

This guide explains how to run the VMware Inventory Dashboard using Docker and Docker Compose.

## Prerequisites

- Docker Engine 20.10 or higher
- Docker Compose 1.29 or higher
- 2GB RAM minimum (4GB recommended)
- 2 CPU cores minimum

## Quick Start

### 1. Build and Start

```bash
# Build and start the container
docker-compose up -d

# View logs
docker-compose logs -f
```

### 2. Access Dashboard

Open your browser and navigate to:
```
http://localhost:8501
```

### 3. Import Data

1. Navigate to **Management > Data Import**
2. Upload your VMware inventory Excel file (RVTools export)
3. Select sheet and click "Import Data"
4. Return to Overview to see your infrastructure

## Docker Commands

### Basic Operations

```bash
# Start containers
docker-compose up -d

# Stop containers
docker-compose stop

# Stop and remove containers
docker-compose down

# View logs
docker-compose logs -f vmware-inventory

# Restart container
docker-compose restart

# Check container status
docker-compose ps
```

### Build Operations

```bash
# Build image
docker-compose build

# Build without cache
docker-compose build --no-cache

# Pull latest base images and build
docker-compose build --pull
```

### Data Management

```bash
# Backup database
docker-compose exec vmware-inventory cp /app/data/vmware_inventory.db /app/data/backup.db

# Copy database out of container
docker cp vmware-inventory-dashboard:/app/data/vmware_inventory.db ./backup.db

# Copy database into container
docker cp ./vmware_inventory.db vmware-inventory-dashboard:/app/data/

# List volumes
docker volume ls

# Inspect volume
docker volume inspect inv-vmware-opa_vmware-data

# Backup volume
docker run --rm -v inv-vmware-opa_vmware-data:/data -v $(pwd):/backup alpine tar czf /backup/vmware-data-backup.tar.gz -C /data .

# Restore volume
docker run --rm -v inv-vmware-opa_vmware-data:/data -v $(pwd):/backup alpine tar xzf /backup/vmware-data-backup.tar.gz -C /data
```

## Configuration

### Environment Variables

Edit `docker-compose.yml` to customize:

```yaml
environment:
  # Database location
  - VMWARE_INV_DB_URL=sqlite:///data/vmware_inventory.db
  
  # Streamlit settings
  - STREAMLIT_SERVER_HEADLESS=true
  - STREAMLIT_SERVER_ENABLE_CORS=false
  - STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=true
```

### Port Configuration

Change the host port (default 8501):

```yaml
ports:
  - "8080:8501"  # Access at http://localhost:8080
```

### Resource Limits

Adjust CPU and memory limits:

```yaml
deploy:
  resources:
    limits:
      cpus: '4.0'      # Increase to 4 CPUs
      memory: 4G       # Increase to 4GB RAM
    reservations:
      cpus: '1.0'
      memory: 1G
```

### Volume Persistence

Data is stored in a named volume by default:

```yaml
volumes:
  - vmware-data:/app/data  # Named volume (recommended)
```

Or use a bind mount for direct access:

```yaml
volumes:
  - ./data:/app/data  # Bind mount to local directory
```

## Advanced Usage

### Using PostgreSQL Database

1. Add PostgreSQL service to `docker-compose.yml`:

```yaml
services:
  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=vmware_inventory
      - POSTGRES_USER=vmware
      - POSTGRES_PASSWORD=changeme
    volumes:
      - postgres-data:/var/lib/postgresql/data
    networks:
      - vmware-network

volumes:
  postgres-data:
```

2. Update vmware-inventory environment:

```yaml
environment:
  - VMWARE_INV_DB_URL=postgresql://vmware:changeme@postgres:5432/vmware_inventory
```

### Running Behind Reverse Proxy

Example Nginx configuration:

```nginx
server {
    listen 80;
    server_name vmware-inventory.example.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Custom Command Arguments

Override default arguments:

```bash
# Use different port
docker-compose run --rm vmware-inventory --host 0.0.0.0 --port 8080

# Use custom database path
docker-compose run --rm vmware-inventory --db-path /app/data/custom.db
```

## Security

### Best Practices

1. **Non-root user**: Container runs as `vmwareinv` user (UID 1000)
2. **Read-only filesystem**: Consider adding `read_only: true` with tmpfs mounts
3. **Network isolation**: Use custom networks
4. **Secrets management**: Use Docker secrets for sensitive data
5. **Regular updates**: Rebuild image regularly for security patches

### Hardening Options

Add to `docker-compose.yml`:

```yaml
security_opt:
  - no-new-privileges:true
cap_drop:
  - ALL
cap_add:
  - NET_BIND_SERVICE
```

## Monitoring

### Health Check

Check container health:

```bash
docker inspect --format='{{.State.Health.Status}}' vmware-inventory-dashboard
```

### Logs

```bash
# Follow logs
docker-compose logs -f

# Last 100 lines
docker-compose logs --tail=100

# Logs for specific service
docker-compose logs -f vmware-inventory
```

### Resource Usage

```bash
# Real-time stats
docker stats vmware-inventory-dashboard

# All containers
docker-compose stats
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs

# Check container status
docker-compose ps

# Inspect container
docker inspect vmware-inventory-dashboard
```

### Permission Errors

```bash
# Fix volume permissions
docker-compose down
docker volume rm inv-vmware-opa_vmware-data
docker-compose up -d
```

### Network Issues

```bash
# Check network
docker network inspect inv-vmware-opa_vmware-network

# Recreate network
docker-compose down
docker-compose up -d
```

### Database Locked

```bash
# Stop container
docker-compose stop

# Wait a few seconds
sleep 5

# Start again
docker-compose start
```

## Image Information

### Build Details

- **Base Image**: python:3.12-slim
- **Multi-stage**: Yes (builder + runtime)
- **Size**: ~300MB (optimized)
- **Architecture**: linux/amd64, linux/arm64

### OpenContainers Labels

View image labels:

```bash
docker inspect vmware-inventory-dashboard:0.6.0 | jq '.[0].Config.Labels'
```

### SBOM Generation

Generate Software Bill of Materials:

```bash
# Using syft
syft vmware-inventory-dashboard:0.6.0 -o json > sbom.json

# Using Docker SBOM
docker sbom vmware-inventory-dashboard:0.6.0
```

## Production Deployment

### Recommended Setup

1. **Use PostgreSQL** instead of SQLite for better concurrency
2. **Set up reverse proxy** with SSL/TLS (Nginx, Traefik, or Caddy)
3. **Configure backup** jobs for database
4. **Monitor resources** with Prometheus/Grafana
5. **Use secrets** for sensitive configuration
6. **Enable log aggregation** (ELK, Loki, etc.)
7. **Set up health monitoring** (Uptime Kuma, Pingdom, etc.)

### Example Production docker-compose.yml

```yaml
version: '3.8'

services:
  vmware-inventory:
    image: vmware-inventory-dashboard:0.6.0
    container_name: vmware-inventory
    environment:
      - VMWARE_INV_DB_URL=postgresql://vmware:${DB_PASSWORD}@postgres:5432/vmware_inventory
    depends_on:
      - postgres
    restart: always
    networks:
      - internal
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.vmware.rule=Host(`vmware.example.com`)"
      - "traefik.http.routers.vmware.entrypoints=websecure"
      - "traefik.http.routers.vmware.tls.certresolver=letsencrypt"

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=vmware_inventory
      - POSTGRES_USER=vmware
      - POSTGRES_PASSWORD_FILE=/run/secrets/db_password
    secrets:
      - db_password
    volumes:
      - postgres-data:/var/lib/postgresql/data
    restart: always
    networks:
      - internal

secrets:
  db_password:
    file: ./secrets/db_password.txt

networks:
  internal:
    driver: bridge

volumes:
  postgres-data:
```

## Support

For issues or questions:
- GitHub Issues: https://github.com/brunseba/inv-vmware-opa/issues
- Documentation: https://github.com/brunseba/inv-vmware-opa/tree/main/docs
