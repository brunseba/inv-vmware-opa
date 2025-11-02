# Wheel-Based Docker Build Evaluation

## Overview

This document evaluates using `uv build` to create Python wheels in a builder stage, then installing from wheels in the runtime stage, compared to the direct installation approach.

## Approach Comparison

### Current: Direct Installation (Dockerfile.optimized)
```dockerfile
# Builder stage
RUN uv pip install --system --no-cache ".[dashboard]"
COPY --from=builder /usr/local/lib/python3.12/site-packages ...
```

### Alternative: Wheel-Based (Dockerfile.wheel)
```dockerfile
# Builder stage
RUN uv build --wheel --out-dir /wheels
RUN uv pip wheel --wheel-dir /wheels --requirement requirements.txt

# Runtime stage
COPY --from=builder /wheels /wheels
RUN pip install --no-index --find-links=/wheels /wheels/*.whl
```

## Advantages of Wheel-Based Approach

### 1. **Cleaner Separation** ✅
- Build artifacts isolated in builder stage
- Runtime only contains installed packages
- No build tools or intermediate files leaked

### 2. **Better Caching** ✅
- Wheels are immutable artifacts
- Can be cached between builds
- Docker layer caching more predictable

### 3. **Reproducibility** ✅
- Exact same wheels used across environments
- Lock file ensures consistency
- Less prone to timing/network issues

### 4. **Faster Reinstalls** ✅
- No compilation in runtime stage
- Pre-compiled C extensions
- Faster image rebuild on code changes

### 5. **Size Reduction Potential** ⚠️
- Wheels don't include build artifacts
- No intermediate compilation files
- But: wheels themselves add temporary size

### 6. **Security** ✅
- No compilers in final image
- Smaller attack surface
- Easier to scan and audit

## Disadvantages of Wheel-Based Approach

### 1. **Build Complexity** ❌
- More steps in Dockerfile
- Need to manage requirements compilation
- Potential uv version compatibility issues

### 2. **Build Time** ❌
- Additional wheel building step
- May be slower for first build
- Two-stage process overhead

### 3. **Storage During Build** ❌
- Wheels stored temporarily in layer
- Increases intermediate image size
- Requires cleanup step

### 4. **Debugging Difficulty** ❌
- Harder to inspect what's installed
- Wheels are binary format
- Less transparent than direct install

## Benchmark Expectations

### Image Size
```
Direct Install:     ~650-700MB
Wheel-Based:        ~620-680MB (5-10% smaller)
```

**Why:** Wheels exclude:
- Build scripts (setup.py, etc.)
- Test files in source packages
- Documentation and examples
- Unused source files

### Build Time
```
Direct Install:     ~2m30s
Wheel-Based:        ~2m45s (+10%)
```

**Why:** Additional wheel creation step, but offset by:
- Better Docker layer caching
- No repeated compilation

### Rebuild Time (code change only)
```
Direct Install:     ~1m15s
Wheel-Based:        ~0m45s (40% faster)
```

**Why:** Wheels cached, only app code changes

## Testing the Wheel Approach

### Build Test
```bash
# Build with wheel-based approach
DOCKERFILE=Dockerfile.wheel IMAGE_NAME=vmware-inventory-dashboard-wheel ./docker-build.sh

# Compare sizes
docker images | grep vmware-inventory

# Test functionality
docker run -p 8501:8501 vmware-inventory-dashboard-wheel:v0.7.2
```

### Verification
```bash
# Check installed packages
docker run --rm vmware-inventory-dashboard-wheel:v0.7.2 pip list

# Verify no build tools
docker run --rm vmware-inventory-dashboard-wheel:v0.7.2 which gcc
# Should output nothing

# Test application
docker run --rm vmware-inventory-dashboard-wheel:v0.7.2 --help
```

## Implementation Issues to Watch

### 1. UV Build Compatibility
```bash
# uv build may not work with all project structures
# Test: Does uv.lock include all dashboard extras?
uv pip compile pyproject.toml --extra dashboard
```

### 2. Binary Wheels for ARM64
```bash
# Some packages may not have ARM64 wheels
# May need to build from source anyway
# Check: plotly, pygwalker, numpy on ARM64
```

### 3. Editable Installs
```bash
# Wheel approach doesn't support editable mode
# Development workflow affected
# Solution: Use direct install for dev
```

## Recommendation Matrix

| Criterion | Direct Install | Wheel-Based | Winner |
|-----------|----------------|-------------|---------|
| Image Size | ~650MB | ~620MB | **Wheel** |
| First Build Time | 2m30s | 2m45s | Direct |
| Rebuild Time | 1m15s | 0m45s | **Wheel** |
| Complexity | Low | Medium | Direct |
| Reproducibility | Good | **Excellent** | **Wheel** |
| Security | Good | **Better** | **Wheel** |
| Debugging | Easy | Harder | Direct |
| CI/CD Friendly | Good | **Excellent** | **Wheel** |

## Hybrid Approach (Recommended)

Use wheel-based for production, direct install for development:

```dockerfile
# Dockerfile (production - wheel-based)
FROM python:3.12-slim AS builder
RUN uv build --wheel ...

# Dockerfile.dev (development - direct install)
FROM python:3.12-slim
RUN uv pip install --system ".[dashboard]"
```

Update `docker-compose.yml`:
```yaml
services:
  app:
    build:
      context: .
      dockerfile: ${DOCKERFILE:-Dockerfile}  # Default to wheel-based
```

## Decision Factors

**Use Wheel-Based if:**
- ✅ Production deployments
- ✅ CI/CD pipelines
- ✅ Multi-architecture builds
- ✅ Frequent rebuilds
- ✅ Security is paramount

**Use Direct Install if:**
- ✅ Local development
- ✅ Rapid iteration needed
- ✅ Debugging package issues
- ✅ Simpler is better for team

## Estimated Outcomes

### Best Case Scenario
```
Size:       620MB (28% reduction from 857MB)
Build:      2m45s
Rebuild:    0m45s
Security:   Excellent (no build tools)
```

### Worst Case Scenario
```
Size:       680MB (21% reduction from 857MB)
Build:      3m15s (complexity overhead)
Rebuild:    1m00s
Complexity: Medium (team learning curve)
```

### Most Likely Scenario
```
Size:       650MB (24% reduction from 857MB)
Build:      2m50s
Rebuild:    0m50s
Tradeoff:   Better for CI/CD, slightly more complex
```

## Implementation Plan

### Phase 1: Test & Validate
1. Build `Dockerfile.wheel`
2. Compare size with current
3. Run full test suite
4. Benchmark build times

### Phase 2: Evaluate Results
1. If size < 680MB: **Proceed**
2. If size > 680MB: **Re-evaluate**
3. Compare with direct install approach

### Phase 3: Gradual Rollout
1. Use wheel-based in CI/CD first
2. Keep direct install for local dev
3. Monitor for issues
4. Gather team feedback

### Phase 4: Decision
- **Success criteria:** <680MB, builds work, no regressions
- **Rollback plan:** Revert to Dockerfile.optimized
- **Documentation:** Update all build docs

## Next Steps

1. **Test the approach:**
   ```bash
   DOCKERFILE=Dockerfile.wheel ./docker-build.sh
   ```

2. **Measure actual results:**
   ```bash
   docker images | grep vmware-inventory
   time docker build -f Dockerfile.wheel .
   ```

3. **Compare with optimized:**
   ```bash
   diff Dockerfile.optimized Dockerfile.wheel
   ```

4. **Make decision based on data**

## Conclusion

**Verdict:** Worth testing, likely beneficial for production.

**Rationale:**
- Slight size reduction (5-10%)
- Better security posture
- Improved CI/CD caching
- Industry best practice

**Action:** Run Phase 1 evaluation to get real data.
