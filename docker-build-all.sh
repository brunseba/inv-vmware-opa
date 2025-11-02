#!/usr/bin/env bash
# Build both Docker image variants (slim and full)
# Usage: ./docker-build-all.sh [--push]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="${IMAGE_NAME:-vmware-inventory-dashboard}"
DOCKER_REGISTRY="${DOCKER_REGISTRY:-}"
PUSH_IMAGE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --push)
            PUSH_IMAGE=true
            shift
            ;;
        -h|--help)
            cat << EOF
Build Both Docker Image Variants

Usage: $0 [OPTIONS]

Options:
    --push              Push images to registry after build
    -h, --help          Show this help message

Environment Variables:
    IMAGE_NAME          Docker image name (default: vmware-inventory-dashboard)
    DOCKER_REGISTRY     Docker registry URL (e.g., ghcr.io/username)

Builds:
    1. Slim variant:  ${IMAGE_NAME}:${VERSION}        (~730MB, no pygwalker)
    2. Full variant:  ${IMAGE_NAME}:${VERSION}-full   (~859MB, with pygwalker)

Examples:
    # Build both variants locally
    $0

    # Build and push to registry
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

# Get build metadata
APP_VERSION=$(git describe --tags 2>/dev/null || echo "dev")
BUILD_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
VCS_REF=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
GIT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")

# Construct full image names
if [ -n "$DOCKER_REGISTRY" ]; then
    FULL_IMAGE_NAME="${DOCKER_REGISTRY}/${IMAGE_NAME}"
else
    FULL_IMAGE_NAME="${IMAGE_NAME}"
fi

# Display build information
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Docker Build - VMware Inventory Dashboard (All)${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Version:${NC}      ${APP_VERSION}"
echo -e "${GREEN}Build Date:${NC}   ${BUILD_DATE}"
echo -e "${GREEN}Git Commit:${NC}   ${VCS_REF}"
echo -e "${GREEN}Git Branch:${NC}   ${GIT_BRANCH}"
echo -e "${GREEN}Base Name:${NC}    ${FULL_IMAGE_NAME}"
echo -e "${GREEN}Push:${NC}         ${PUSH_IMAGE}"
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo

# Check if Dockerfiles exist
if [ ! -f "Dockerfile" ]; then
    echo -e "${RED}Error: Dockerfile not found${NC}"
    exit 1
fi

if [ ! -f "Dockerfile.full" ]; then
    echo -e "${RED}Error: Dockerfile.full not found${NC}"
    exit 1
fi

# =============================================================================
# Build Slim Variant
# =============================================================================
echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  Building Slim Variant (without pygwalker)${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
echo

docker build \
    --build-arg APP_VERSION="${APP_VERSION}" \
    --build-arg BUILD_DATE="${BUILD_DATE}" \
    --build-arg VCS_REF="${VCS_REF}" \
    --tag "${FULL_IMAGE_NAME}:${APP_VERSION}" \
    --tag "${FULL_IMAGE_NAME}:latest" \
    --tag "${FULL_IMAGE_NAME}:slim" \
    --file "Dockerfile" \
    .

if [ $? -eq 0 ]; then
    SLIM_SIZE=$(docker images "${FULL_IMAGE_NAME}:${APP_VERSION}" --format "{{.Size}}")
    echo -e "${GREEN}✓ Slim variant built successfully! Size: ${SLIM_SIZE}${NC}"
    echo
    echo -e "${GREEN}Tagged as:${NC}"
    echo -e "  - ${FULL_IMAGE_NAME}:${APP_VERSION}"
    echo -e "  - ${FULL_IMAGE_NAME}:latest"
    echo -e "  - ${FULL_IMAGE_NAME}:slim"
else
    echo -e "${RED}✗ Slim variant build failed!${NC}"
    exit 1
fi

echo

# =============================================================================
# Build Full Variant
# =============================================================================
echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  Building Full Variant (with pygwalker)${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
echo

docker build \
    --build-arg APP_VERSION="${APP_VERSION}" \
    --build-arg BUILD_DATE="${BUILD_DATE}" \
    --build-arg VCS_REF="${VCS_REF}" \
    --tag "${FULL_IMAGE_NAME}:${APP_VERSION}-full" \
    --tag "${FULL_IMAGE_NAME}:full" \
    --file "Dockerfile.full" \
    .

if [ $? -eq 0 ]; then
    FULL_SIZE=$(docker images "${FULL_IMAGE_NAME}:${APP_VERSION}-full" --format "{{.Size}}")
    echo -e "${GREEN}✓ Full variant built successfully! Size: ${FULL_SIZE}${NC}"
    echo
    echo -e "${GREEN}Tagged as:${NC}"
    echo -e "  - ${FULL_IMAGE_NAME}:${APP_VERSION}-full"
    echo -e "  - ${FULL_IMAGE_NAME}:full"
else
    echo -e "${RED}✗ Full variant build failed!${NC}"
    exit 1
fi

echo

# =============================================================================
# Push to registry if requested
# =============================================================================
if [ "$PUSH_IMAGE" = true ]; then
    if [ -z "$DOCKER_REGISTRY" ]; then
        echo -e "${YELLOW}Warning: DOCKER_REGISTRY not set. Pushing to Docker Hub.${NC}"
    fi

    echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  Pushing images to registry${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
    echo

    # Push slim variant
    echo -e "${YELLOW}Pushing slim variant...${NC}"
    for tag in "${APP_VERSION}" "latest" "slim"; do
        docker push "${FULL_IMAGE_NAME}:${tag}"
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ Pushed ${FULL_IMAGE_NAME}:${tag}${NC}"
        else
            echo -e "${RED}✗ Failed to push ${FULL_IMAGE_NAME}:${tag}${NC}"
            exit 1
        fi
    done

    echo

    # Push full variant
    echo -e "${YELLOW}Pushing full variant...${NC}"
    for tag in "${APP_VERSION}-full" "full"; do
        docker push "${FULL_IMAGE_NAME}:${tag}"
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ Pushed ${FULL_IMAGE_NAME}:${tag}${NC}"
        else
            echo -e "${RED}✗ Failed to push ${FULL_IMAGE_NAME}:${tag}${NC}"
            exit 1
        fi
    done
fi

echo

# =============================================================================
# Display summary
# =============================================================================
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ All Builds Complete!${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo

echo -e "${CYAN}Slim Variant (${SLIM_SIZE}):${NC}"
echo -e "  docker run -p 8501:8501 ${FULL_IMAGE_NAME}:${APP_VERSION}"
echo -e "  docker run -p 8501:8501 ${FULL_IMAGE_NAME}:slim"
echo

echo -e "${CYAN}Full Variant (${FULL_SIZE}):${NC}"
echo -e "  docker run -p 8501:8501 ${FULL_IMAGE_NAME}:${APP_VERSION}-full"
echo -e "  docker run -p 8501:8501 ${FULL_IMAGE_NAME}:full"
echo

echo -e "${CYAN}Compare sizes:${NC}"
echo -e "  docker images ${FULL_IMAGE_NAME} --format 'table {{.Repository}}\\t{{.Tag}}\\t{{.Size}}'"
echo

echo -e "${CYAN}Inspect labels:${NC}"
echo -e "  docker inspect ${FULL_IMAGE_NAME}:slim | jq '.[].Config.Labels.variant'"
echo -e "  docker inspect ${FULL_IMAGE_NAME}:full | jq '.[].Config.Labels.variant'"
echo
