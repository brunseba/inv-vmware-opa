# Docker Image Variants

## Overview

The VMware Inventory Dashboard is available in two Docker image variants to suit different needs:

1. **Slim** - Optimized for size (~730MB)
2. **Full** - Complete with advanced features (~859MB)

## Variants Comparison

| Feature | Slim | Full |
|---------|------|------|
| **Size** | ~730MB | ~859MB |
| **Packages** | 104 | 176 |
| **Streamlit Dashboard** | ✅ | ✅ |
| **Data Visualization** | ✅ (Plotly) | ✅ (Plotly + more) |
| **PDF Reports** | ✅ | ✅ |
| **PyGWalker Explorer** | ❌ | ✅ |
| **Jupyter Components** | ❌ | ✅ |
| **Cloud Integrations** | ❌ | ✅ (Snowflake, AWS) |
| **Build Time** | ~2m30s | ~3m00s |
| **Use Case** | Most users | Advanced analysis |

## Quick Start

### Slim Variant (Recommended)

```bash
# Run slim variant
docker run -p 8501:8501 vmware-inventory-dashboard:latest

# Or explicitly use slim tag
docker run -p 8501:8501 vmware-inventory-dashboard:slim
```

### Full Variant

```bash
# Run full variant
docker run -p 8501:8501 vmware-inventory-dashboard:full

# Or with version
docker run -p 8501:8501 vmware-inventory-dashboard:v0.7.2-full
```

## Available Tags

### Slim Variant Tags
- `latest` - Always points to latest slim build
- `slim` - Explicitly slim variant
- `v0.7.2` - Specific version (slim)
- `v0.7.*` - Version-specific

### Full Variant Tags
- `full` - Latest full variant
- `v0.7.2-full` - Specific version (full)

## Building Images

### Build Both Variants

```bash
# Build both slim and full
./docker-build-all.sh

# Build and push to registry
DOCKER_REGISTRY=ghcr.io/myorg ./docker-build-all.sh --push
```

### Build Individual Variants

```bash
# Build only slim
./docker-build.sh

# Build only full
DOCKERFILE=Dockerfile.full IMAGE_NAME=vmware-inventory-dashboard-full ./docker-build.sh
```

## Choosing the Right Variant

### Choose Slim if:
- ✅ You want the smallest image size
- ✅ You're deploying to resource-constrained environments
- ✅ You don't need advanced data exploration
- ✅ Standard Plotly visualizations are sufficient
- ✅ You want faster builds and deployments

### Choose Full if:
- ✅ You need PyGWalker interactive data exploration
- ✅ You require Jupyter notebook integration
- ✅ You use Snowflake or AWS integrations
- ✅ You want all available features
- ✅ Image size is not a concern

## What's Included

### Slim Variant Includes:
- Core CLI tools
- Streamlit dashboard
- Plotly visualizations
- Basic data exploration
- PDF report generation
- Excel import/export
- Database management
- All essential features

### Full Variant Adds:
- **PyGWalker** - Drag-and-drop data exploration
- **IPython** - Enhanced Python shell
- **Jupyter Widgets** - Interactive components
- **DuckDB** - Advanced analytics
- **Snowflake** - Cloud data warehouse connector
- **Boto3** - AWS SDK
- **QuickJS** - JavaScript engine
- And ~70 additional packages

## Feature Availability

### Dashboard Pages

| Page | Slim | Full | Notes |
|------|------|------|-------|
| Home | ✅ | ✅ | |
| Overview | ✅ | ✅ | |
| Analytics | ✅ | ✅ | Custom explorer disabled in slim |
| Data Explorer | ✅ | ✅ | Shows warning + fallback in slim |
| Advanced Explorer | ✅ | ✅ | Shows warning + fallback in slim |
| Migration Planner | ✅ | ✅ | |
| Labels | ✅ | ✅ | |
| Data Import | ✅ | ✅ | |
| Settings | ✅ | ✅ | |

**Note:** Slim variant shows helpful warnings when accessing PyGWalker-dependent features and provides alternative basic visualizations.

## Docker Compose

### Using Both Variants

```yaml
version: '3.8'

services:
  dashboard-slim:
    image: vmware-inventory-dashboard:slim
    ports:
      - "8501:8501"
    volumes:
      - ./data:/app/data
    environment:
      - VMWARE_INV_DB_URL=sqlite:///data/vmware_inventory.db

  dashboard-full:
    image: vmware-inventory-dashboard:full
    ports:
      - "8502:8501"
    volumes:
      - ./data:/app/data
    environment:
      - VMWARE_INV_DB_URL=sqlite:///data/vmware_inventory.db
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Build Docker Variants

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      
      - name: Login to GHCR
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Build and Push Both Variants
        env:
          DOCKER_REGISTRY: ghcr.io/${{ github.repository_owner }}
        run: ./docker-build-all.sh --push
```

## Size Breakdown

### Slim Variant (~730MB)

```
Base image:               ~150MB
Python packages:          ~400MB
Streamlit + Plotly:       ~150MB
Application code:           ~7MB
Other dependencies:        ~23MB
                         --------
Total:                    ~730MB
```

### Full Variant (~859MB)

```
Slim variant:             ~730MB
PyGWalker:                 ~50MB
Jupyter components:        ~30MB
Cloud integrations:        ~30MB
DuckDB + analytics:        ~19MB
                         --------
Total:                    ~859MB
```

## Migration Guide

### From Full to Slim

If migrating from full to slim:

1. **Check Usage**: Identify if you use PyGWalker features
2. **Test Fallbacks**: Verify dataframe fallbacks work for you
3. **Update Docs**: Update deployment documentation
4. **Retag Images**: Update image tags in compose/k8s files

```bash
# Before
docker pull vmware-inventory-dashboard:full

# After
docker pull vmware-inventory-dashboard:slim
```

### From Slim to Full

If you need more features:

```bash
# Simply switch to full variant
docker pull vmware-inventory-dashboard:full
docker run -p 8501:8501 vmware-inventory-dashboard:full
```

## Troubleshooting

### "PyGWalker not installed" Warning

**Problem:** Seeing warnings about PyGWalker in slim variant

**Solution:** This is expected. Either:
- Use the full variant: `docker run vmware-inventory-dashboard:full`
- Or accept the basic dataframe view as alternative

### Wrong Variant Running

**Problem:** Not sure which variant is running

**Solution:** Check the variant label:
```bash
docker inspect vmware-inventory-dashboard:latest | jq '.[].Config.Labels.variant'
# Output: "slim" or "full"
```

### Image Too Large

**Problem:** Full variant is too large for your environment

**Solution:** Use slim variant:
```bash
docker pull vmware-inventory-dashboard:slim
```

## Best Practices

### For Development
- Use **full** variant for feature-complete development
- Mount volumes for data persistence
- Use docker-compose for easy management

### For Production
- Use **slim** variant for most deployments
- Pin specific version tags (not `latest`)
- Use health checks
- Configure resource limits

### For CI/CD
- Build both variants in parallel
- Tag appropriately (version + variant)
- Push to registry
- Run smoke tests on both

## FAQ

**Q: Which variant should I use?**  
A: Start with slim. Upgrade to full only if you need PyGWalker or cloud integrations.

**Q: Can I upgrade from slim to full without data loss?**  
A: Yes! Both variants use the same database format. Just switch the image.

**Q: Do both variants receive updates?**  
A: Yes, both are built from the same codebase and receive updates simultaneously.

**Q: Is there a performance difference?**  
A: No significant runtime performance difference. Full variant has slightly longer startup due to more packages.

**Q: Can I build a custom variant?**  
A: Yes! Edit `pyproject.toml` optional dependencies and create your own Dockerfile.

## Related Documentation

- [Docker Versioning](./docker-versioning.md)
- [Docker Optimization](./docker-optimization.md)
- [Package Inventory](./docker-packages-inventory.md)
- [PyGWalker GCC Dependency](./pygwalker-gcc-dependency.md)
