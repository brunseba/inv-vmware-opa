#!/usr/bin/env bash
# Docker build script with automatic version detection from git tags
# Usage: ./docker-build.sh [--push] [--tag custom-tag]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="${IMAGE_NAME:-vmware-inventory-dashboard}"
DOCKER_REGISTRY="${DOCKER_REGISTRY:-}"  # Set to your registry, e.g., ghcr.io/username
DOCKERFILE="${DOCKERFILE:-Dockerfile}"

# Flags
PUSH_IMAGE=false
CUSTOM_TAG=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --push)
            PUSH_IMAGE=true
            shift
            ;;
        --tag)
            CUSTOM_TAG="$2"
            shift 2
            ;;
        -h|--help)
            cat << EOF
Docker Build Script with Git Tag Versioning

Usage: $0 [OPTIONS]

Options:
    --push              Push image to registry after build
    --tag TAG           Use custom tag instead of git tag
    -h, --help          Show this help message

Environment Variables:
    IMAGE_NAME          Docker image name (default: vmware-inventory-dashboard)
    DOCKER_REGISTRY     Docker registry URL (e.g., ghcr.io/username)
    DOCKERFILE          Dockerfile path (default: Dockerfile)

Examples:
    # Build with git tag version
    $0

    # Build and push to registry
    $0 --push

    # Build with custom tag
    $0 --tag v1.0.0

    # Build with registry and push
    DOCKER_REGISTRY=ghcr.io/myorg $0 --push

EOF
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Function to get version from git
get_version() {
    if [ -n "$CUSTOM_TAG" ]; then
        echo "$CUSTOM_TAG"
        return
    fi

    # Try to get version from git tag
    if VERSION=$(git describe --tags --exact-match 2>/dev/null); then
        # We're on a tagged commit
        echo "$VERSION"
    elif VERSION=$(git describe --tags 2>/dev/null); then
        # We're after a tag, add commit info
        echo "$VERSION"
    else
        # No tags found, use branch and commit
        BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
        COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "dev")
        echo "${BRANCH}-${COMMIT}"
    fi
}

# Get build metadata
APP_VERSION=$(get_version)
BUILD_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
VCS_REF=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
GIT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")

# Construct full image name
if [ -n "$DOCKER_REGISTRY" ]; then
    FULL_IMAGE_NAME="${DOCKER_REGISTRY}/${IMAGE_NAME}"
else
    FULL_IMAGE_NAME="${IMAGE_NAME}"
fi

# Display build information
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Docker Build - VMware Inventory Dashboard${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Version:${NC}      ${APP_VERSION}"
echo -e "${GREEN}Build Date:${NC}   ${BUILD_DATE}"
echo -e "${GREEN}Git Commit:${NC}   ${VCS_REF}"
echo -e "${GREEN}Git Branch:${NC}   ${GIT_BRANCH}"
echo -e "${GREEN}Image:${NC}        ${FULL_IMAGE_NAME}:${APP_VERSION}"
echo -e "${GREEN}Dockerfile:${NC}   ${DOCKERFILE}"
echo -e "${GREEN}Push:${NC}         ${PUSH_IMAGE}"
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo

# Check if Dockerfile exists
if [ ! -f "$DOCKERFILE" ]; then
    echo -e "${RED}Error: Dockerfile not found: ${DOCKERFILE}${NC}"
    exit 1
fi

# Build the Docker image
echo -e "${YELLOW}Building Docker image...${NC}"
docker build \
    --build-arg APP_VERSION="${APP_VERSION}" \
    --build-arg BUILD_DATE="${BUILD_DATE}" \
    --build-arg VCS_REF="${VCS_REF}" \
    --tag "${FULL_IMAGE_NAME}:${APP_VERSION}" \
    --tag "${FULL_IMAGE_NAME}:latest" \
    --file "${DOCKERFILE}" \
    .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Build successful!${NC}"
    echo
    echo -e "${GREEN}Tagged as:${NC}"
    echo -e "  - ${FULL_IMAGE_NAME}:${APP_VERSION}"
    echo -e "  - ${FULL_IMAGE_NAME}:latest"
else
    echo -e "${RED}✗ Build failed!${NC}"
    exit 1
fi

# Push to registry if requested
if [ "$PUSH_IMAGE" = true ]; then
    if [ -z "$DOCKER_REGISTRY" ]; then
        echo -e "${YELLOW}Warning: DOCKER_REGISTRY not set. Pushing to Docker Hub.${NC}"
    fi

    echo
    echo -e "${YELLOW}Pushing images to registry...${NC}"
    
    docker push "${FULL_IMAGE_NAME}:${APP_VERSION}"
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Pushed ${FULL_IMAGE_NAME}:${APP_VERSION}${NC}"
    else
        echo -e "${RED}✗ Failed to push ${FULL_IMAGE_NAME}:${APP_VERSION}${NC}"
        exit 1
    fi

    docker push "${FULL_IMAGE_NAME}:latest"
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Pushed ${FULL_IMAGE_NAME}:latest${NC}"
    else
        echo -e "${RED}✗ Failed to push ${FULL_IMAGE_NAME}:latest${NC}"
        exit 1
    fi
fi

# Display final information
echo
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ Build Complete!${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo
echo -e "${GREEN}Run with:${NC}"
echo -e "  docker run -p 8501:8501 ${FULL_IMAGE_NAME}:${APP_VERSION}"
echo
echo -e "${GREEN}Or use docker-compose:${NC}"
echo -e "  export APP_VERSION=${APP_VERSION}"
echo -e "  docker-compose up"
echo
echo -e "${GREEN}Inspect image:${NC}"
echo -e "  docker inspect ${FULL_IMAGE_NAME}:${APP_VERSION}"
echo
