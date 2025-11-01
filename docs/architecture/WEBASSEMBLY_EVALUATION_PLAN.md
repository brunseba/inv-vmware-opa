# WebAssembly Frontend Evaluation Plan

## Executive Summary

This document outlines a comprehensive evaluation plan for integrating WebAssembly (WASM) into the inv-vmware-opa project's frontend, potentially replacing or augmenting the current Streamlit-based dashboard.

---

## Current Architecture

### Stack
- **Backend**: Python 3.10+ with SQLAlchemy, Click CLI
- **Frontend**: Streamlit 1.50+ web dashboard
- **Visualization**: Plotly 5.24+, Matplotlib 3.10+
- **Data Processing**: Pandas 2.3+, extensive Python data manipulation

### Challenges
- Performance bottlenecks with large datasets (>10,000 VMs)
- Streamlit's reactive model can cause full page rerenders
- Limited offline capabilities
- Heavy server-side computation requirements

---

## Phase 1: Research & Feasibility Assessment (Week 1-2)

### 1.1 Technology Stack Evaluation

#### Option A: PyScript/Pyodide
**Pros:**
- Run existing Python code in browser via WASM
- Minimal code rewrite (pandas, numpy work)
- Leverage existing Python expertise

**Cons:**
- Large bundle sizes (~40-100 MB initial load)
- Performance slower than native WASM
- Limited browser API access

**Action Items:**
- [ ] Create proof-of-concept with Pyodide loading sample VM inventory data
- [ ] Benchmark Pyodide performance with 1K, 10K, 100K VM records
- [ ] Measure bundle size and initial load time
- [ ] Test pandas operations in browser

#### Option B: Rust + WASM (wasm-bindgen/wasm-pack)
**Pros:**
- Near-native performance
- Small bundle sizes (< 1 MB)
- Direct DOM manipulation via web-sys
- Strong typing and safety

**Cons:**
- Complete frontend rewrite required
- Learning curve for Rust
- Need to reimplement data processing logic
- Less mature data science ecosystem

**Action Items:**
- [ ] Create POC with Rust parsing VMware CSV/JSON data
- [ ] Implement basic table rendering with yew/leptos framework
- [ ] Benchmark data processing vs Python pandas
- [ ] Estimate effort for full rewrite

#### Option C: AssemblyScript
**Pros:**
- TypeScript-like syntax (easier transition)
- Good performance
- Moderate bundle sizes

**Cons:**
- Limited library ecosystem
- Still requires significant rewrite
- Less mature than Rust WASM

**Action Items:**
- [ ] Evaluate AssemblyScript data processing capabilities
- [ ] Create simple data table POC

#### Option D: Hybrid Approach (WASM modules + TypeScript/React)
**Pros:**
- Use WASM only for performance-critical operations
- Keep existing Python backend API
- Modern web framework (React/Vue + Material UI)
- Gradual migration path

**Cons:**
- More complex architecture
- Need to maintain multiple codebases
- API design overhead

**Action Items:**
- [ ] Design REST/GraphQL API for Python backend
- [ ] Create TypeScript frontend with Material UI
- [ ] Implement WASM module for data filtering/sorting
- [ ] Benchmark hybrid vs pure approaches

### 1.2 Use Case Prioritization

Rank features by WASM benefit:

| Feature | Current Bottleneck | WASM Benefit | Priority |
|---------|-------------------|--------------|----------|
| VM list filtering/sorting | High (>10K records) | High | P0 |
| Advanced search with regex | Medium | High | P0 |
| Real-time chart updates | Medium | Medium | P1 |
| PDF generation | Low (server-side OK) | Low | P3 |
| Data import/parsing | Low | Medium | P2 |
| Migration cost calculation | Medium | High | P1 |

### 1.3 Performance Benchmarks (Baseline)

**Action Items:**
- [ ] Profile current Streamlit dashboard with 10K, 50K, 100K records
- [ ] Identify top 5 performance bottlenecks
- [ ] Measure Time to Interactive (TTI), First Contentful Paint (FCP)
- [ ] Document memory usage patterns

**Target Metrics:**
- Initial load: < 2 seconds
- Filter operation (10K records): < 100ms
- Search operation: < 200ms
- Table render (paginated): < 500ms

---

## Phase 2: Proof of Concept Development (Week 3-5)

### 2.1 POC #1: Pyodide-based Dashboard

**Scope:**
- Implement VM list page with filtering and sorting
- Load sample dataset (1K-10K VMs) from JSON
- Use pandas in browser for data manipulation
- Plotly for visualization

**Deliverables:**
- [ ] Working HTML page with Pyodide
- [ ] Performance metrics vs Streamlit
- [ ] Bundle size analysis
- [ ] User experience assessment

**Success Criteria:**
- Load time < 5 seconds
- Filter/sort < 500ms for 10K records
- Bundle size < 50 MB

### 2.2 POC #2: Rust + TypeScript Hybrid

**Scope:**
- Rust WASM module for data processing (filter, sort, aggregate)
- TypeScript + React frontend with Material UI
- Python FastAPI backend serving REST API
- VM Explorer page implementation

**Deliverables:**
- [ ] FastAPI backend with `/api/vms` endpoints
- [ ] Rust WASM data processing library
- [ ] React dashboard page with Material UI
- [ ] Performance comparison report

**Success Criteria:**
- Load time < 2 seconds
- Filter/sort < 100ms for 10K records
- Bundle size < 2 MB (WASM + JS)
- Feature parity with current VM Explorer

### 2.3 POC #3: Pure TypeScript (Control)

**Scope:**
- TypeScript + React frontend (no WASM)
- Python FastAPI backend
- Browser-native data processing

**Deliverables:**
- [ ] Same features as POC #2 but pure TS
- [ ] Performance baseline comparison

---

## Phase 3: Architecture Design (Week 6-7)

### 3.1 Recommended Architecture

Based on POC results, design final architecture considering:

#### Option 1: Full Hybrid (Recommended)
```
┌─────────────────────────────────────────┐
│         Frontend (Browser)              │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │   React + TypeScript + Material  │  │
│  │                                  │  │
│  │  ┌────────────────────────────┐ │  │
│  │  │  WASM Modules (Rust)       │ │  │
│  │  │  - Data filtering          │ │  │
│  │  │  - Sorting/aggregation     │ │  │
│  │  │  - Cost calculations       │ │  │
│  │  └────────────────────────────┘ │  │
│  └──────────────────────────────────┘  │
│                 ↕ REST API              │
│  ┌──────────────────────────────────┐  │
│  │   Python FastAPI Backend         │  │
│  │   - Database access (SQLAlchemy) │  │
│  │   - Authentication/RBAC          │  │
│  │   - PDF generation               │  │
│  │   - Excel import/export          │  │
│  └──────────────────────────────────┘  │
│                 ↕                       │
│  ┌──────────────────────────────────┐  │
│  │   Database (SQLite/PostgreSQL)   │  │
│  └──────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

**Key Decisions:**
- [ ] Define API contract (OpenAPI spec)
- [ ] Decide WASM vs TS for each feature
- [ ] Authentication strategy (local + OIDC per user rules)
- [ ] State management (Redux/Zustand)
- [ ] Offline capability requirements

#### Option 2: Pyodide-based
- Keep Python codebase
- All processing in browser
- Minimal backend for data storage

#### Option 3: Status Quo with Optimizations
- Keep Streamlit
- Add caching layers
- Optimize pagination
- Use WASM for specific bottlenecks

### 3.2 Migration Strategy

**Incremental Migration Phases:**

**Phase A: API Layer**
- [ ] Create FastAPI backend preserving Streamlit
- [ ] Expose REST endpoints for all data operations
- [ ] Add authentication layer
- [ ] Deploy alongside existing Streamlit app

**Phase B: Core Pages (V1)**
- [ ] Migrate VM Explorer page
- [ ] Migrate Migration Scenarios page
- [ ] Migrate Migration Targets page
- [ ] Keep other pages in Streamlit

**Phase C: Analytics & Visualization (V2)**
- [ ] Migrate Analytics page with Plotly/D3.js
- [ ] Migrate Comparison Tools
- [ ] Migrate Data Quality page

**Phase D: Administrative (V3)**
- [ ] Migrate Data Import
- [ ] Migrate Backup/Restore
- [ ] Migrate Folder Labelling
- [ ] Deprecate Streamlit

---

## Phase 4: Implementation Plan (Week 8-16)

### 4.1 Technology Stack Selection

Based on evaluation results, select:

**Frontend:**
- Framework: React 18+ with TypeScript
- UI Library: Material UI v6 (per user rules)
- Build Tool: Vite
- State Management: Redux Toolkit or Zustand
- WASM: Rust (wasm-bindgen) for performance-critical operations

**Backend:**
- FastAPI (Python 3.10+)
- SQLAlchemy 2.0+
- Authentication: Python-Jose (JWT) + OIDC
- CORS/Security: FastAPI middleware

**DevOps:**
- Package manager: uv for Python, pnpm for Node.js
- Testing: pytest + vitest
- CI/CD: GitHub Actions
- Container: Docker (multi-stage builds per user rules)

### 4.2 Development Phases

#### Sprint 1-2: API Backend
- [ ] Set up FastAPI project structure
- [ ] Implement VM inventory endpoints
- [ ] Add authentication (local + OIDC)
- [ ] RBAC integration with Kubernetes RBAC if applicable
- [ ] API documentation (Swagger/OpenAPI)

#### Sprint 3-4: Frontend Foundation
- [ ] Set up React + TypeScript + Vite
- [ ] Implement Material UI theming (dark mode support)
- [ ] Create left ribbon navigation menu (per user rules)
- [ ] Create right ribbon for details panel (per user rules)
- [ ] Implement authentication flow

#### Sprint 5-6: WASM Data Processing
- [ ] Create Rust crate for data operations
- [ ] Implement filter/sort/aggregate functions
- [ ] Build WASM module with wasm-pack
- [ ] Create TypeScript bindings
- [ ] Benchmark and optimize

#### Sprint 7-8: VM Explorer Migration
- [ ] Implement VM list with WASM filtering
- [ ] Add advanced search with regex
- [ ] Create detail panels
- [ ] Integrate with backend API
- [ ] Add unit tests

#### Sprint 9-10: Migration Planning Migration
- [ ] Migration Targets CRUD UI
- [ ] Migration Scenarios UI
- [ ] Cost calculation (potentially in WASM)
- [ ] Duration modeling

#### Sprint 11-12: Analytics & Charts
- [ ] Port Plotly charts or use D3.js
- [ ] Implement real-time updates
- [ ] Add comparison tools
- [ ] Performance optimization

#### Sprint 13-14: Testing & Polish
- [ ] End-to-end testing with Playwright
- [ ] Performance testing
- [ ] Security audit
- [ ] Accessibility (WCAG 2.1 AA)

#### Sprint 15-16: Deployment & Documentation
- [ ] Docker containerization (multi-stage)
- [ ] SBOM generation (per user rules)
- [ ] Deployment guides
- [ ] User documentation
- [ ] Migration guide from Streamlit

---

## Phase 5: Testing & Validation (Week 17-18)

### 5.1 Performance Testing
- [ ] Load testing with k6 (1K, 10K, 100K concurrent users)
- [ ] Benchmark against Streamlit baseline
- [ ] Memory profiling
- [ ] Network waterfall analysis

### 5.2 User Acceptance Testing
- [ ] A/B testing with select users
- [ ] Usability testing sessions
- [ ] Gather feedback on UX improvements
- [ ] Identify regressions

### 5.3 Security Testing
- [ ] OWASP Top 10 vulnerability scan
- [ ] Authentication/authorization testing
- [ ] Dependency audit (pip-audit, npm audit)
- [ ] Penetration testing

---

## Phase 6: Documentation & Deployment (Week 19-20)

### 6.1 Documentation
- [ ] API documentation (OpenAPI)
- [ ] Frontend component documentation (Storybook)
- [ ] Deployment guide (Docker, k8s if applicable)
- [ ] User guide updates
- [ ] Developer onboarding guide

### 6.2 Deployment
- [ ] Create Docker image (multi-stage, slim base)
- [ ] Add OCI labels (per user rules)
- [ ] Generate SBOM
- [ ] Set up CI/CD pipeline (GitHub Actions)
- [ ] Deploy to staging environment
- [ ] Production rollout plan

---

## Decision Criteria

### Go/No-Go Criteria for WASM Adoption

**GO if:**
- ✅ Performance improvement > 50% on key operations
- ✅ Bundle size reasonable (< 5 MB initial)
- ✅ Development effort < 6 months with 2 developers
- ✅ Maintenance complexity acceptable
- ✅ Clear migration path with minimal downtime

**NO-GO if:**
- ❌ Performance improvement < 25%
- ❌ Development effort > 1 year
- ❌ Bundle size unacceptable (> 50 MB)
- ❌ Browser compatibility issues
- ❌ Significant UX regressions

---

## Risk Assessment

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Poor WASM performance | High | Medium | Thorough POC testing, fallback to TS |
| Large bundle sizes | Medium | Medium | Code splitting, lazy loading, CDN |
| Browser compatibility | Medium | Low | Polyfills, feature detection, graceful degradation |
| Development timeline overrun | High | Medium | Incremental migration, feature flags |
| User resistance to UI change | Medium | Medium | Gradual rollout, user testing, feedback loops |
| Security vulnerabilities | High | Low | Security audits, dependency scanning, OIDC |

---

## Budget & Resources

### Estimated Effort
- **Phase 1-2 (POCs)**: 2 developers × 5 weeks = 10 dev-weeks
- **Phase 3 (Design)**: 1 architect × 2 weeks = 2 dev-weeks
- **Phase 4 (Implementation)**: 2 developers × 16 weeks = 32 dev-weeks
- **Phase 5 (Testing)**: 1 QA + 1 dev × 2 weeks = 4 dev-weeks
- **Phase 6 (Deploy)**: 1 DevOps + 1 dev × 2 weeks = 4 dev-weeks

**Total**: ~52 dev-weeks (~1 year with 2 developers part-time)

### Required Skills
- Python (FastAPI, SQLAlchemy)
- TypeScript/React
- Rust (for WASM) or willingness to learn
- Material UI
- Docker/CI/CD
- Authentication (JWT, OIDC)

---

## Success Metrics

### Performance KPIs
- Initial page load: < 2s (vs ~5s current)
- Filter 10K records: < 100ms (vs ~1-2s current)
- Memory usage: < 200 MB (vs ~500 MB current)
- Time to Interactive: < 1s

### User Experience KPIs
- Task completion time: 30% reduction
- User satisfaction score: > 4.5/5
- Feature adoption rate: > 80% for new UI

### Business KPIs
- Reduced server costs (client-side computation)
- Improved scalability (10K+ concurrent users)
- Enhanced offline capabilities

---

## Next Steps

1. **Review and approve this plan** with stakeholders
2. **Allocate resources** for POC phase
3. **Set up development environment** for WASM experimentation
4. **Create POC branches** for each evaluated option
5. **Schedule weekly check-ins** to review progress
6. **Document findings** from each POC
7. **Make architecture decision** by end of Phase 2
8. **Proceed to implementation** if approved

---

## Appendix

### A. Useful Resources
- [WebAssembly Official Docs](https://webassembly.org/)
- [Rust WASM Book](https://rustwasm.github.io/book/)
- [Pyodide Documentation](https://pyodide.org/)
- [wasm-bindgen Guide](https://rustwasm.github.io/wasm-bindgen/)
- [Material UI React](https://mui.com/)

### B. Similar Projects
- [Perspective (WASM data tables)](https://github.com/finos/perspective)
- [DuckDB WASM](https://duckdb.org/docs/api/wasm)
- [Polars (potential future WASM support)](https://github.com/pola-rs/polars)

### C. Alternative Approaches Not Evaluated
- WebGPU for compute-heavy operations
- Service Workers for offline-first architecture
- Progressive Web App (PWA) approach
- Electron for desktop app

---

**Document Version**: 1.0  
**Last Updated**: 2025-11-01  
**Owner**: brun_s  
**Status**: Draft for Review
