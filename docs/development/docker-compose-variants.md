# Docker Compose Variant Selection

This guide explains how to use `docker-compose` to build and run different Docker image variants.

## Overview

The project provides two Docker image variants:

| Variant | Size | Packages | Features |
|---------|------|----------|----------|
| **Slim** | 730MB | 104 | Core features, production-optimized |
| **Full** | 863MB | 176 | All features including PyGWalker |

## Configuration

The variant is selected using environment variables in your `.env` file.

### Environment Variables

```bash
# Select which Dockerfile to use
DOCKERFILE=Dockerfile          # slim variant (default)
# or
DOCKERFILE=Dockerfile.full     # full variant

# Image tag to use/create
IMAGE_TAG=latest              # or slim, full, v0.7.2, etc.
```

## Usage

### 1. Using Slim Variant (Default)

```bash
# Use default .env settings
docker-compose up -d
```

Or explicitly set environment:

```bash
# Set in .env
DOCKERFILE=Dockerfile
IMAGE_TAG=slim

# Run
docker-compose up -d
```

### 2. Using Full Variant

```bash
# Option A: Set environment variables inline
DOCKERFILE=Dockerfile.full IMAGE_TAG=full docker-compose up -d

# Option B: Update .env file
# Edit .env:
DOCKERFILE=Dockerfile.full
IMAGE_TAG=full

# Run
docker-compose up -d
```

### 3. Build Only (No Start)

```bash
# Build slim
docker-compose build

# Build full
DOCKERFILE=Dockerfile.full docker-compose build
```

### 4. Force Rebuild

```bash
# Rebuild slim
docker-compose build --no-cache

# Rebuild full
DOCKERFILE=Dockerfile.full docker-compose build --no-cache
```

## Complete Workflow Examples

### Example 1: Test Both Variants

```bash
# Build and test slim variant
DOCKERFILE=Dockerfile IMAGE_TAG=slim docker-compose up -d
# Access at http://localhost:8501
docker-compose logs -f
docker-compose down

# Build and test full variant
DOCKERFILE=Dockerfile.full IMAGE_TAG=full docker-compose up -d
# Access at http://localhost:8501
docker-compose logs -f
docker-compose down
```

### Example 2: Development Workflow

```bash
# Create .env from template
cp .env.example .env

# Edit .env to select variant
# DOCKERFILE=Dockerfile        # for slim
# DOCKERFILE=Dockerfile.full   # for full

# Build and run
docker-compose up -d

# View logs
docker-compose logs -f vmware-inventory

# Stop when done
docker-compose down
```

### Example 3: Production Deployment

```bash
# Set production environment
cat > .env << EOF
APP_VERSION=v0.7.2
CONTAINER_NAME=vmware-inventory-prod
DOCKERFILE=Dockerfile
IMAGE_TAG=slim

HOST_PORT=8501
CONTAINER_PORT=8501

CPU_LIMIT=4.0
CPU_RESERVATION=1.0
MEMORY_LIMIT=4G
MEMORY_RESERVATION=1G

RESTART_POLICY=always
EOF

# Deploy
docker-compose up -d

# Verify health
docker-compose ps
docker inspect vmware-inventory-prod | grep -A 5 Health
```

## Environment File Templates

### `.env.slim` - Slim Variant

```bash
APP_VERSION=v0.7.2
CONTAINER_NAME=vmware-inventory-dashboard
DOCKERFILE=Dockerfile
IMAGE_TAG=slim

HOST_PORT=8501
CONTAINER_PORT=8501

CPU_LIMIT=2.0
MEMORY_LIMIT=2G
RESTART_POLICY=unless-stopped
```

### `.env.full` - Full Variant

```bash
APP_VERSION=v0.7.2
CONTAINER_NAME=vmware-inventory-dashboard-full
DOCKERFILE=Dockerfile.full
IMAGE_TAG=full

HOST_PORT=8502
CONTAINER_PORT=8501

CPU_LIMIT=2.5
MEMORY_LIMIT=3G
RESTART_POLICY=unless-stopped
```

## Switching Between Variants

### Method 1: Environment Variables

```bash
# Switch to full
DOCKERFILE=Dockerfile.full IMAGE_TAG=full docker-compose up -d

# Switch back to slim
DOCKERFILE=Dockerfile IMAGE_TAG=slim docker-compose up -d
```

### Method 2: Multiple Environment Files

```bash
# Run slim
docker-compose --env-file .env.slim up -d

# Run full
docker-compose --env-file .env.full up -d
```

### Method 3: Docker Compose Profiles (Advanced)

Create `docker-compose.override.yml`:

```yaml
services:
  vmware-inventory-slim:
    extends: vmware-inventory
    profiles: ["slim"]
    build:
      dockerfile: Dockerfile
    image: vmware-inventory-dashboard:slim
    container_name: vmware-inventory-slim

  vmware-inventory-full:
    extends: vmware-inventory
    profiles: ["full"]
    build:
      dockerfile: Dockerfile.full
    image: vmware-inventory-dashboard:full
    container_name: vmware-inventory-full
```

Then run:

```bash
# Run slim
docker-compose --profile slim up -d

# Run full
docker-compose --profile full up -d
```

## Troubleshooting

### Issue: Wrong Image Being Used

**Solution:** Clear existing images and rebuild

```bash
# Stop and remove containers
docker-compose down

# Remove old images
docker rmi vmware-inventory-dashboard:latest
docker rmi vmware-inventory-dashboard:slim
docker rmi vmware-inventory-dashboard:full

# Rebuild with desired variant
DOCKERFILE=Dockerfile IMAGE_TAG=slim docker-compose build --no-cache
```

### Issue: Environment Variables Not Applied

**Solution:** Ensure `.env` file is in the same directory as `docker-compose.yml`

```bash
# Check current directory
pwd
ls -la .env

# Or use explicit env file
docker-compose --env-file /path/to/.env up -d
```

### Issue: Port Conflicts

**Solution:** Use different ports for each variant

```bash
# Slim on 8501
HOST_PORT=8501 DOCKERFILE=Dockerfile docker-compose up -d

# Full on 8502 (different terminal)
HOST_PORT=8502 DOCKERFILE=Dockerfile.full docker-compose -p vmware-full up -d
```

## Best Practices

### 1. Use Named Variants in Production

```bash
# Good: explicit variant
IMAGE_TAG=slim

# Avoid: ambiguous tag
IMAGE_TAG=latest
```

### 2. Document Your Choice

Add comments to `.env`:

```bash
# Using slim variant for production (15% smaller, faster builds)
DOCKERFILE=Dockerfile
IMAGE_TAG=slim
```

### 3. Pin Versions

```bash
# Good: specific version
APP_VERSION=v0.7.2
IMAGE_TAG=v0.7.2-slim

# Risky: floating tag
IMAGE_TAG=latest
```

### 4. Test Before Deploying

```bash
# Always test locally first
DOCKERFILE=Dockerfile docker-compose up

# Check health
docker-compose exec vmware-inventory python -c "import pygwalker" || echo "Slim: PyGWalker not available (expected)"

# Deploy if tests pass
docker-compose up -d
```

## Comparison: docker-compose vs docker-build.sh

| Feature | docker-compose | docker-build.sh |
|---------|---------------|-----------------|
| **Build multiple variants** | Manual (env vars) | Automated (all variants) |
| **Run container** | ✅ Yes | ❌ No |
| **Volume management** | ✅ Yes | ❌ No |
| **Network setup** | ✅ Yes | ❌ No |
| **Health checks** | ✅ Yes | ❌ No |
| **Resource limits** | ✅ Yes | ❌ No |
| **Auto-tagging** | Basic | Advanced |
| **Registry push** | Manual | ✅ Automated |

### When to Use Each

**Use docker-compose:**
- Running containers locally
- Development environment
- Testing single variant
- Need volume/network management

**Use docker-build.sh:**
- Building for distribution
- CI/CD pipelines
- Building all variants at once
- Pushing to registries

**Use docker-build-all.sh:**
- Building both variants
- Complete release builds
- Registry publishing
- Comprehensive tagging

## See Also

- [Docker Quick Reference](../../DOCKER.md) - Quick usage guide
- [Docker Variants Guide](docker-variants.md) - Detailed variant comparison
- [Build Script Documentation](../../docker-build-all.sh) - Automated builds
