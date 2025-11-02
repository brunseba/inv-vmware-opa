# pygwalker GCC Dependency Explanation

## Overview

**pygwalker** requires **gcc** during installation because one of its dependencies, **quickjs**, contains C/C++ extensions that must be compiled from source.

## Dependency Chain

```
pygwalker
  └── quickjs  ← Requires GCC for compilation
```

## What is quickjs?

**quickjs** is a Python binding for the QuickJS JavaScript engine, which is written in C.

### Key Facts:
- **Purpose**: Embeds a lightweight JavaScript engine in Python
- **Language**: C implementation (QuickJS engine itself)
- **Installation**: Requires compilation of C extensions
- **Output**: Creates `.so` (shared object) files for Python to import

### Why pygwalker needs it:
pygwalker uses JavaScript evaluation for certain data transformation operations, particularly:
- Complex data queries
- Dynamic expression evaluation
- Advanced filtering logic
- Client-side computation delegation

## The Compiled Artifact

When quickjs is installed, it produces a compiled binary:

```bash
_quickjs.cpython-312-aarch64-linux-gnu.so
# Format: _{module}.cpython-{version}-{arch}-{os}-{abi}.so
```

This file:
- Contains native machine code
- Specific to CPU architecture (arm64/amd64)
- Specific to Python version (3.12)
- Cannot be "pip installed" without compilation

## Why GCC is Required

### Compilation Process:

1. **Download Source**: pip downloads quickjs source code
2. **Configure Build**: setuptools prepares C extension build
3. **Compile C Code**: gcc compiles C source to machine code
4. **Link Libraries**: creates `.so` shared library
5. **Install**: places compiled binary in site-packages

### What GCC Does:

```c
// QuickJS C code example (simplified)
#include <Python.h>
#include "quickjs.h"

static PyObject* js_eval(PyObject* self, PyObject* args) {
    // C code that interfaces Python <-> JavaScript
    JSRuntime *rt = JS_NewRuntime();
    JSContext *ctx = JS_NewContext(rt);
    // ... evaluation logic ...
    return result;
}
```

GCC transforms this C code into machine code that Python can load.

## Full pygwalker Dependency Tree

```
pygwalker (0.4.x)
├── quickjs ← **NEEDS GCC**
├── duckdb ← May need GCC on some platforms
├── pyarrow ← May need GCC on some platforms
├── numpy ← Usually has pre-built wheels
├── pandas
├── sqlalchemy
├── streamlit (indirectly)
├── ipython
├── ipywidgets
├── jinja2
├── pydantic
├── psutil
├── cachetools
├── arrow
├── astor
├── appdirs
├── anywidget
├── gw-dsl-parser
├── ipylab
├── kanaries-track
├── packaging
├── pytz
├── requests
├── segment-analytics-python
├── sqlglot
├── traitlets
└── typing-extensions
```

### Dependencies Requiring Compilation:

| Package | Requires GCC? | Why |
|---------|---------------|-----|
| **quickjs** | ✅ Yes | C extension for JS engine |
| **duckdb** | ⚠️ Sometimes | Has wheels for common platforms |
| **pyarrow** | ⚠️ Sometimes | Has wheels for common platforms |
| **numpy** | ❌ No* | Pre-built wheels available |
| **psutil** | ⚠️ Sometimes | Platform-specific |

*numpy DOES contain C code, but PyPI provides pre-built wheels for most platforms

## Docker Image Impact

### Without Pre-compilation (Runtime Install):

```dockerfile
FROM python:3.12-slim
RUN pip install pygwalker
# ❌ FAILS: gcc: command not found
```

### With GCC in Runtime (Bad Practice):

```dockerfile
FROM python:3.12-slim
RUN apt-get install gcc g++ python3-dev
RUN pip install pygwalker
# ✅ Works but image is huge (~1.5GB+)
```

### Proper Multi-Stage Build:

```dockerfile
# Builder: Has GCC
FROM python:3.12-slim AS builder
RUN apt-get install gcc g++
RUN pip install --target /deps pygwalker

# Runtime: No GCC needed
FROM python:3.12-slim
COPY --from=builder /deps /usr/local/lib/python3.12/site-packages
# ✅ Works, smaller image (~800-900MB)
```

## Why Can't We Use Pre-built Wheels?

### Pre-built wheels exist for:
- ✅ Windows (amd64)
- ✅ macOS (x86_64, arm64)
- ✅ Linux (amd64, arm64) for common configurations

### But fail when:
- ❌ Using Alpine Linux (musl libc vs glibc)
- ❌ Uncommon architectures (s390x, ppc64le)
- ❌ Non-standard Python builds
- ❌ Conflicting library versions

## Checking for Compiled Extensions

### In Docker Image:

```bash
# Find all compiled extensions
find /path/to/site-packages -name "*.so" -type f

# Specifically for quickjs
find /path/to/site-packages -name "*quickjs*.so"
```

### File Details:

```bash
$ file _quickjs.cpython-312-aarch64-linux-gnu.so
_quickjs.cpython-312-aarch64-linux-gnu.so: ELF 64-bit LSB shared object, 
ARM aarch64, version 1 (SYSV), dynamically linked, 
BuildID[sha1]=..., stripped
```

This confirms it's a compiled binary, not Python source code.

## Alternatives to pygwalker (If GCC is Problematic)

If avoiding GCC is critical, consider:

### 1. **Remove pygwalker entirely**
- Most dashboard features work without it
- Only advanced data exploration requires it

### 2. **Use streamlit-aggrid**
- Pure Python alternative
- No compilation needed
- Less powerful but sufficient for many use cases

### 3. **Use pandas-profiling**
- Alternative data exploration
- Has pre-built wheels
- Different feature set

### 4. **Use plotly + dash**
- More control over visualizations
- No JS engine embedding
- Steeper learning curve

## Size Impact Analysis

### With pygwalker and dependencies:

```
Base image (python:3.12-slim):     ~150MB
Python packages (no pygwalker):    ~400MB
pygwalker + deps:                  ~300MB
                                   -------
Total:                             ~850MB
```

### Without pygwalker:

```
Base image (python:3.12-slim):     ~150MB
Python packages (streamlit, etc):  ~400MB
                                   -------
Total:                             ~550MB
```

**Savings: ~300MB (35% reduction)**

## Making pygwalker Optional

Update `pyproject.toml`:

```toml
[project.optional-dependencies]
dashboard-core = [
    "streamlit>=1.50.0,<2.0.0",
    "plotly>=5.24.0,<7.0.0",
    # ... other deps
]
dashboard-advanced = [
    "pygwalker>=0.4.0,<1.0.0",  # Only install if needed
]
```

Then in code:

```python
# src/dashboard/pages/advanced_explorer.py
try:
    import pygwalker as pyg
    PYGWALKER_AVAILABLE = True
except ImportError:
    PYGWALKER_AVAILABLE = False

if PYGWALKER_AVAILABLE:
    # Show advanced features
    pyg.walk(df)
else:
    st.warning("Advanced explorer requires pygwalker. Install with: pip install inv-vmware-opa[dashboard-advanced]")
    # Show basic exploration instead
```

## Recommendations

### For Production Dockerfiles:

1. ✅ **Use multi-stage builds** - Compile in builder, copy to runtime
2. ✅ **Cache compiled artifacts** - Don't recompile every build
3. ✅ **Use --target for pip** - Install to specific directory
4. ✅ **Make pygwalker optional** - Not everyone needs it

### For Development:

1. ✅ **Use uv or poetry** - Better dependency resolution
2. ✅ **Lock dependencies** - Ensure reproducible builds
3. ✅ **Test without pygwalker** - Ensure graceful degradation

### For CI/CD:

1. ✅ **Pre-build dependencies** - Save as artifacts
2. ✅ **Use cache layers** - Speed up builds
3. ✅ **Test both variants** - With and without pygwalker

## Conclusion

**pygwalker requires GCC** because:
- It depends on **quickjs**
- **quickjs** embeds a C-based JavaScript engine
- C code must be compiled to native machine code
- This compilation requires a C compiler (gcc/clang)

**Solutions:**
- Multi-stage Docker builds (compile in builder)
- Make pygwalker optional
- Use alternatives without C dependencies
- Accept the compilation requirement

The **original Dockerfile approach (859MB)** handles this correctly by compiling everything in the builder stage with GCC available, then copying only the runtime artifacts.
