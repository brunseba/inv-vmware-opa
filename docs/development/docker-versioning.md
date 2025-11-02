# Docker Image Versioning

## Overview

Docker images are automatically versioned based on git tags, ensuring that each release has a corresponding versioned Docker image with proper metadata.

## How It Works

### Version Detection

The Docker build system automatically detects the version from git tags:

1. **Tagged Commit**: Uses exact tag (e.g., `v0.7.2`)
2. **After Tag**: Uses tag + commit info (e.g., `v0.7.2-3-g4ae8ab1`)
3. **No Tags**: Uses branch + commit (e.g., `main-4ae8ab1`)
4. **Custom**: Manual override with `--tag` option

### Build Arguments

The Dockerfile accepts three build arguments:

- `APP_VERSION`: Application version (auto-detected or manual)
- `BUILD_DATE`: ISO 8601 build timestamp
- `VCS_REF`: Git commit SHA (short form)

These are embedded as OCI-compliant labels in the image.

## Usage

### Quick Start

```bash
# Build with automatic version from git tag
./docker-build.sh

# Build and push to registry
./docker-build.sh --push

# Build with custom version
./docker-build.sh --tag v1.0.0

# Build with registry
DOCKER_REGISTRY=ghcr.io/myorg ./docker-build.sh --push
```

### Using docker-build.sh

**Features:**
- Automatic version detection from git tags
- OCI-compliant image labels
- Multi-tag support (version + latest)
- Optional registry push
- Colorized output with build summary

**Options:**
```bash
./docker-build.sh [OPTIONS]

Options:
  --push              Push image to registry after build
  --tag TAG           Use custom tag instead of git tag
  -h, --help          Show help message
```

**Environment Variables:**
```bash
IMAGE_NAME          Docker image name (default: vmware-inventory-dashboard)
DOCKER_REGISTRY     Registry URL (e.g., ghcr.io/username)
DOCKERFILE          Dockerfile path (default: Dockerfile)
```

### Using docker-compose

**1. Set version in environment:**
```bash
# Automatic from git
export APP_VERSION=$(git describe --tags)
export BUILD_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
export VCS_REF=$(git rev-parse --short HEAD)

# Or edit .env file
cp .env.example .env
# Edit APP_VERSION in .env
```

**2. Build and run:**
```bash
docker-compose build
docker-compose up
```

### Manual Docker Build

```bash
# Get version info
APP_VERSION=$(git describe --tags)
BUILD_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
VCS_REF=$(git rev-parse --short HEAD)

# Build image
docker build \
  --build-arg APP_VERSION="${APP_VERSION}" \
  --build-arg BUILD_DATE="${BUILD_DATE}" \
  --build-arg VCS_REF="${VCS_REF}" \
  --tag "vmware-inventory-dashboard:${APP_VERSION}" \
  --tag "vmware-inventory-dashboard:latest" \
  .
```

## Image Labels

Built images include OCI-compliant labels:

```bash
# Inspect labels
docker inspect vmware-inventory-dashboard:v0.7.2 | jq '.[].Config.Labels'
```

**Labels included:**
```json
{
  "org.opencontainers.image.title": "VMware Inventory Dashboard",
  "org.opencontainers.image.description": "Interactive web dashboard for VMware vSphere inventory analysis",
  "org.opencontainers.image.version": "v0.7.2",
  "org.opencontainers.image.authors": "brunseba",
  "org.opencontainers.image.url": "https://github.com/brunseba/inv-vmware-opa",
  "org.opencontainers.image.documentation": "https://github.com/brunseba/inv-vmware-opa/blob/main/README.md",
  "org.opencontainers.image.source": "https://github.com/brunseba/inv-vmware-opa",
  "org.opencontainers.image.licenses": "MIT",
  "org.opencontainers.image.created": "2025-11-02T16:00:00Z",
  "org.opencontainers.image.revision": "4ae8ab1",
  "version": "v0.7.2",
  "maintainer": "sebastien.brun@lepervier.org"
}
```

## Version Formats

### Release Versions
```bash
v0.7.2          # Tagged release
v1.0.0          # Major release
v1.0.0-beta.1   # Pre-release
```

### Development Versions
```bash
v0.7.2-3-g4ae8ab1    # 3 commits after v0.7.2
main-4ae8ab1         # No tags, on main branch
feature-abc-1234567  # Feature branch with commit
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Build Docker Image

on:
  push:
    tags:
      - 'v*'
  
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Full history for git describe
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      
      - name: Login to Registry
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Build and Push
        env:
          DOCKER_REGISTRY: ghcr.io/${{ github.repository_owner }}
        run: ./docker-build.sh --push
```

### GitLab CI

```yaml
build-docker:
  stage: build
  image: docker:latest
  services:
    - docker:dind
  before_script:
    - apk add --no-cache git
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
  script:
    - export DOCKER_REGISTRY=$CI_REGISTRY_IMAGE
    - ./docker-build.sh --push
  only:
    - tags
```

## Registry Publishing

### Docker Hub

```bash
# Build and push to Docker Hub
docker login
./docker-build.sh --push
```

### GitHub Container Registry

```bash
# Login to GHCR
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# Build and push
DOCKER_REGISTRY=ghcr.io/username ./docker-build.sh --push
```

### Private Registry

```bash
# Login
docker login registry.example.com

# Build and push
DOCKER_REGISTRY=registry.example.com/myorg ./docker-build.sh --push
```

## Image Tags

Each build creates two tags:

1. **Version Tag**: `vmware-inventory-dashboard:v0.7.2`
   - Immutable reference to specific version
   - Recommended for production
   - Traceable to git commit

2. **Latest Tag**: `vmware-inventory-dashboard:latest`
   - Always points to most recent build
   - Useful for development
   - May change frequently

## Version Inspection

### Check Image Version

```bash
# View all labels
docker inspect vmware-inventory-dashboard:latest | jq '.[].Config.Labels'

# Get specific version
docker inspect vmware-inventory-dashboard:latest | \
  jq -r '.[].Config.Labels."org.opencontainers.image.version"'

# Get build date
docker inspect vmware-inventory-dashboard:latest | \
  jq -r '.[].Config.Labels."org.opencontainers.image.created"'

# Get git commit
docker inspect vmware-inventory-dashboard:latest | \
  jq -r '.[].Config.Labels."org.opencontainers.image.revision"'
```

### Runtime Version

```bash
# Check version of running container
docker exec <container-id> python -c "from src import __version__; print(__version__)"

# Or via labels
docker inspect <container-id> | jq -r '.[].Config.Labels.version'
```

## Best Practices

### Tagging Strategy

1. **Use Semantic Versioning**: `v{major}.{minor}.{patch}`
   ```bash
   git tag v1.0.0
   git push --tags
   ```

2. **Tag After Testing**: Only tag commits that passed tests
   ```bash
   # Run tests first
   pytest
   
   # Then tag
   git tag v1.0.1
   git push --tags
   ```

3. **Annotated Tags**: Include release notes
   ```bash
   git tag -a v1.0.0 -m "Release v1.0.0: Major features"
   git push --tags
   ```

### Building for Release

```bash
# 1. Ensure on tagged commit
git describe --tags --exact-match

# 2. Build with automatic versioning
./docker-build.sh

# 3. Test the image
docker run -p 8501:8501 vmware-inventory-dashboard:v0.7.2

# 4. Push to registry
./docker-build.sh --push
```

### Multi-Architecture Builds

```bash
# Setup buildx
docker buildx create --name multiarch --use

# Build for multiple platforms
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --build-arg APP_VERSION="$(git describe --tags)" \
  --build-arg BUILD_DATE="$(date -u +"%Y-%m-%dT%H:%M:%SZ")" \
  --build-arg VCS_REF="$(git rev-parse --short HEAD)" \
  --tag "vmware-inventory-dashboard:v0.7.2" \
  --push \
  .
```

## Troubleshooting

### Version Not Detected

**Problem**: Script shows `dev` or `unknown` version

**Solutions:**
```bash
# Ensure git repository has tags
git tag

# Fetch all tags from remote
git fetch --tags

# Create a tag if needed
git tag v0.1.0
```

### Build Args Not Working

**Problem**: Labels show `${APP_VERSION}` literally

**Solutions:**
```bash
# Ensure Docker version supports build args in labels
docker version

# Use BuildKit for modern Dockerfile features
export DOCKER_BUILDKIT=1
docker build --build-arg APP_VERSION=v1.0.0 .
```

### Permission Denied

**Problem**: `./docker-build.sh: Permission denied`

**Solution:**
```bash
chmod +x docker-build.sh
./docker-build.sh
```

## Examples

### Development Build

```bash
# Build dev version from branch
./docker-build.sh
# Version: main-4ae8ab1
```

### Release Build

```bash
# On tagged commit v0.7.2
git tag v0.7.2
git push --tags
./docker-build.sh
# Version: v0.7.2
```

### Custom Version

```bash
# Override auto-detection
./docker-build.sh --tag v1.0.0-rc.1
# Version: v1.0.0-rc.1
```

### Build and Push

```bash
# To Docker Hub
./docker-build.sh --push

# To GHCR
DOCKER_REGISTRY=ghcr.io/myorg ./docker-build.sh --push

# To private registry
DOCKER_REGISTRY=registry.example.com ./docker-build.sh --push
```

## Related Files

- `Dockerfile` - Image definition with version ARGs
- `docker-compose.yml` - Compose configuration with version variables
- `.env.example` - Environment variable template
- `docker-build.sh` - Automated build script
- `pyproject.toml` - Python package version (should match)

## References

- [OCI Image Spec](https://github.com/opencontainers/image-spec/blob/main/annotations.md)
- [Docker Build Args](https://docs.docker.com/engine/reference/builder/#arg)
- [Semantic Versioning](https://semver.org/)
- [Git Describe](https://git-scm.com/docs/git-describe)
