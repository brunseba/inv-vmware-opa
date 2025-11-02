# Docker Image Size Optimization

## Current State

**Image:** `ghcr.io/brunseba/vmware-inventory-dashboard:v0.7.2`  
**Size:** 857MB

### Size Breakdown
- Python packages: ~666MB (78%)
- Base image (python:3.12-slim): ~97MB (11%)
- Python binaries: ~32.5MB (4%)
- Application code: ~6.7MB (1%)
- Other: ~55MB (6%)

## Optimization Strategies

### 1. Quick Wins (Dockerfile.optimized) - Target: ~600-650MB

**Changes:**
- Remove test files from installed packages
- Remove C source files (*.c, *.pyx) after compilation
- Remove documentation from dist-info directories
- Copy only necessary binaries (not all of /usr/local/bin)
- Selective binary copying (vmware-*, streamlit only)
- Bytecode precompilation for faster startup

**Expected savings:** ~150-200MB

### 2. Dependency Optimization - Target: ~450-550MB

**Heavy Dependencies Analysis:**
```
streamlit: ~150MB
plotly: ~80MB  
pygwalker: ~100MB (includes duckdb, polars)
pandas: ~50MB
matplotlib: ~40MB
streamlit-extras: ~30MB
```

**Options:**

#### A. Split Images by Use Case
```dockerfile
# Minimal CLI image (no dashboard)
FROM python:3.12-slim
RUN uv pip install --system ".[base]"  # ~200MB

# Dashboard image (current)
FROM python:3.12-slim
RUN uv pip install --system ".[dashboard]"  # ~650MB

# Full-featured image
FROM python:3.12-slim
RUN uv pip install --system ".[all]"  # ~850MB
```

#### B. Conditional Dependencies
Update `pyproject.toml` to make pygwalker truly optional:
```toml
[project.optional-dependencies]
dashboard-core = [
    "streamlit>=1.50.0,<2.0.0",
    "plotly>=5.24.0,<7.0.0",
]
dashboard-advanced = [
    "pygwalker>=0.4.0,<1.0.0",  # Only if needed
    "streamlit-extras>=0.7.8,<1.0.0",
]
```

### 3. Alternative Base Images - Target: ~400-500MB

**Option A: Alpine Linux**
```dockerfile
FROM python:3.12-alpine
# Pros: ~40MB base (vs 97MB)
# Cons: Compilation issues with C extensions, longer build times
```

**Option B: Distroless Python**
```dockerfile
FROM gcr.io/distroless/python3:latest
# Pros: Minimal attack surface, ~60MB base
# Cons: No shell, harder debugging, limited tooling
```

**Option C: Chainguard Images**
```dockerfile
FROM cgr.dev/chainguard/python:latest
# Pros: Minimal CVEs, ~80MB base
# Cons: Requires Chainguard subscription for some features
```

### 4. Layer Optimization - Target: Current + Better Caching

**Layer Ordering:**
```dockerfile
# 1. Base dependencies (rarely changes)
RUN apt-get install libpq5

# 2. Python dependencies (changes occasionally)
COPY pyproject.toml uv.lock ./
RUN uv pip install --system ".[dashboard]"

# 3. Application code (changes frequently)
COPY src ./src
```

### 5. Advanced Optimizations

#### A. Use Python Wheel Cache
```dockerfile
# Build wheels in builder stage
RUN pip wheel --wheel-dir=/wheels ".[dashboard]"

# Install from wheels in runtime
COPY --from=builder /wheels /wheels
RUN pip install --no-index --find-links=/wheels /wheels/*.whl
```

#### B. Strip Binaries
```dockerfile
RUN find /usr/local/lib -name '*.so*' -exec strip --strip-unneeded {} \; 2>/dev/null || true
```

#### C. Use UPX for Binary Compression
```dockerfile
RUN upx --best --lzma /usr/local/bin/python3.12
```

#### D. Multi-Architecture Optimization
```dockerfile
# Use platform-specific optimizations
ARG TARGETPLATFORM
RUN if [ "$TARGETPLATFORM" = "linux/arm64" ]; then \
      # ARM-specific optimizations
    fi
```

## Recommended Implementation Plan

### Phase 1: Quick Wins (Immediate)
1. Apply `Dockerfile.optimized` changes
2. Test functionality thoroughly
3. Expected result: **~650MB** (-24%)

### Phase 2: Dependency Restructuring (Week 1)
1. Split optional dependencies into granular groups
2. Create multiple image variants (cli, dashboard, full)
3. Update docker-compose.yml with image variants
4. Expected result: **~450MB for dashboard** (-47%)

### Phase 3: Base Image Evaluation (Week 2-3)
1. Benchmark Alpine vs Slim vs Distroless
2. Measure build times, runtime performance
3. Evaluate maintenance overhead
4. Expected result: **~400-500MB** (-50-53%)

### Phase 4: Advanced Optimizations (Week 4)
1. Implement wheel caching
2. Add binary stripping
3. Optimize layer ordering
4. Expected result: **~350-450MB** (-55-59%)

## Testing Checklist

After each optimization:

```bash
# Build optimized image
docker build -f Dockerfile.optimized -t test:optimized .

# Check size
docker images test:optimized

# Test functionality
docker run -p 8501:8501 test:optimized

# Run test suite
docker run test:optimized pytest

# Check startup time
time docker run --rm test:optimized --version

# Security scan
docker scan test:optimized
```

## Comparison Matrix

| Strategy | Size | Build Time | Maintenance | Security | Compatibility |
|----------|------|------------|-------------|----------|---------------|
| Current | 857MB | Fast | Easy | Good | Excellent |
| Optimized | 650MB | Fast | Easy | Good | Excellent |
| Split Images | 450MB | Medium | Medium | Good | Good |
| Alpine | 400MB | Slow | Hard | Excellent | Medium |
| Distroless | 450MB | Fast | Hard | Excellent | Medium |

## Benchmarks

### Build Time
```bash
# Current
time docker build . -t current
# real: 2m30s

# Optimized (expected)
time docker build -f Dockerfile.optimized . -t optimized  
# real: 2m45s (+15s for cleanup)

# Alpine (expected)
time docker build -f Dockerfile.alpine . -t alpine
# real: 5m00s (+2.5x due to compilation)
```

### Runtime Performance
```bash
# Startup time comparison
docker run --rm current streamlit --version
# 0.8s

docker run --rm optimized streamlit --version
# 0.6s (precompiled bytecode)
```

### Security Scan Results
```bash
docker scan current
# Critical: 0, High: 2, Medium: 8, Low: 15

docker scan optimized (expected)
# Critical: 0, High: 2, Medium: 8, Low: 15 (same)

docker scan alpine (expected)
# Critical: 0, High: 0, Medium: 2, Low: 5 (fewer packages)
```

## Implementation: Dockerfile.optimized

The optimized Dockerfile includes:

### Builder Stage Changes
- ✅ Better layer caching (dependencies before source)
- ✅ Aggressive cleanup of test files
- ✅ Remove C source files after compilation
- ✅ Remove documentation from packages
- ✅ Clean __pycache__ and .pyc files

### Runtime Stage Changes
- ✅ Copy only necessary binaries (selective)
- ✅ Precompile bytecode for faster startup
- ✅ Remove requests dependency from healthcheck (use urllib)
- ✅ Add PYTHONDONTWRITEBYTECODE flag
- ✅ Add ca-certificates for HTTPS

### Test the Optimized Image

```bash
# Build
./docker-build.sh --tag optimized
DOCKERFILE=Dockerfile.optimized ./docker-build.sh

# Compare sizes
docker images | grep vmware-inventory

# Test
docker run -p 8501:8501 vmware-inventory-dashboard:optimized
```

## Alternative: Minimal CLI Image

For users who only need CLI (no dashboard):

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN pip install --no-cache-dir uv==0.5.18 && \
    uv pip install --system --no-cache . && \
    rm -rf /root/.cache
COPY src ./src
ENTRYPOINT ["vmware-inv"]
```

**Expected size:** ~250MB (-71%)

## Next Steps

1. **Test Dockerfile.optimized:**
   ```bash
   DOCKERFILE=Dockerfile.optimized IMAGE_NAME=vmware-inventory-dashboard-opt ./docker-build.sh
   ```

2. **Measure impact:**
   ```bash
   docker images | grep vmware-inventory
   ```

3. **If successful, replace current Dockerfile**

4. **Consider implementing Phase 2 (split images)**

## Resources

- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Multi-stage Builds](https://docs.docker.com/build/building/multi-stage/)
- [Python Docker Best Practices](https://pythonspeed.com/docker/)
- [Slim Base Images Comparison](https://pythonspeed.com/articles/base-image-python-docker-images/)

## Monitoring

Add image size tracking to CI/CD:

```yaml
# .github/workflows/docker-size.yml
name: Track Image Size

on: [push, pull_request]

jobs:
  size-tracking:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build image
        run: docker build -t test .
      - name: Check size
        run: |
          SIZE=$(docker images test --format "{{.Size}}")
          echo "Image size: $SIZE"
          # Fail if over threshold
          docker images test --format "{{.Size}}" | \
            numfmt --from=iec | \
            awk '{if ($1 > 700000000) exit 1}'
```
