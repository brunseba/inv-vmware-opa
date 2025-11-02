# Docker Images

## Quick Start

```bash
# Run slim variant (recommended, ~730MB)
docker run -p 8501:8501 vmware-inventory-dashboard:latest

# Run full variant (with PyGWalker, ~859MB)
docker run -p 8501:8501 vmware-inventory-dashboard:full
```

## Image Variants

| Variant | Size | Tags | Use Case |
|---------|------|------|----------|
| **Slim** | ~730MB | `latest`, `slim`, `v0.7.2` | Most users, production |
| **Full** | ~859MB | `full`, `v0.7.2-full` | Advanced analysis, PyGWalker |

## Building

```bash
# Build both variants
./docker-build-all.sh

# Build only slim
./docker-build.sh

# Build with push to registry
DOCKER_REGISTRY=ghcr.io/myorg ./docker-build-all.sh --push
```

## Documentation

See [docs/development/docker-variants.md](docs/development/docker-variants.md) for complete documentation.

## What's the Difference?

**Slim** includes everything most users need:
- ✅ Full dashboard
- ✅ Data visualization (Plotly)
- ✅ PDF reports
- ✅ All core features

**Full** adds advanced features:
- ✅ PyGWalker drag-and-drop explorer
- ✅ Jupyter components
- ✅ Cloud integrations (Snowflake, AWS)
- ✅ Advanced analytics

## Choosing a Variant

**Use Slim if:**
- You want smaller images
- You don't need interactive data exploration
- Deploying to constrained environments

**Use Full if:**
- You need PyGWalker
- You use Snowflake or AWS
- You want all features

Both variants are fully functional and use the same database format.
