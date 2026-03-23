# Comprehensive Code Improvement Plan

## Executive Summary

The inventory management system is a well-structured demo app with solid foundations, but has significant gaps across security, testing, and code quality that would need addressing for production use.

---

## Analysis Ratings

| Aspect | Rating | Key Finding |
|--------|--------|-------------|
| Architecture | Fair | Monolithic main.py, good frontend separation |
| Coding Logic | Fair | Race conditions, O(n*m) lookups, ID collision risk |
| Naming Conventions | Good | Minor inconsistencies (unit_price vs unit_cost) |
| Test Coverage | Poor | 65% backend, 0% frontend |
| Performance | Fair | No pagination, no caching, no debouncing |
| Security | Critical | No auth, CORS wildcard, no input validation |
| Scalability | Poor | In-memory data, no pagination, single process |
| Reliability | Fair | No error handler, no retries, no logging |

---

## Phase 1: Critical Fixes (Security & Correctness)

| # | Task | Files | Effort |
|---|------|-------|--------|
| 1 | Fix CORS - replace wildcard with explicit origins from env var | `main.py` | 1h |
| 2 | Add input validation on all query parameters (whitelist values) | `main.py` | 2h |
| 3 | Fix ID generation - use UUID instead of list length | `main.py:375` | 30m |
| 4 | Add API request timeout in axios (10s) | `api.js` | 15m |
| 5 | Fix race conditions - add AbortController to filter watchers | Vue views | 2h |
| 6 | Add security headers middleware (X-Frame-Options, etc.) | `main.py` | 30m |

## Phase 2: Test Coverage

| # | Task | Effort |
|---|------|--------|
| 7 | Write tests for 6 untested backend endpoints | 4h |
| 8 | Add error handling / edge case tests (4xx, empty results, bad input) | 3h |
| 9 | Set up Vitest + Vue Test Utils for frontend | 1h |
| 10 | Write composable unit tests (useFilters, useI18n, useAuth) | 3h |
| 11 | Write component tests for critical views | 6h |
| 12 | Add CI/CD with GitHub Actions | 2h |

## Phase 3: Architecture & Code Quality

| # | Task | Effort |
|---|------|--------|
| 13 | Split `main.py` into models, filters, routes modules | 2h |
| 14 | Refactor `Reports.vue` to Composition API | 1h |
| 15 | Extract Dashboard.vue modals/KPIs into sub-components | 2h |
| 16 | Replace magic strings with constants (status values, categories) | 1h |
| 17 | Use `QUARTER_MAP` constant instead of hardcoded quarter logic | 30m |
| 18 | Standardize naming (translate* functions, unit_cost vs unit_price) | 1h |

## Phase 4: Performance & Scalability

| # | Task | Effort |
|---|------|--------|
| 19 | Add pagination to list endpoints (inventory, orders, transactions) | 3h |
| 20 | Add HTTP cache headers for static data (demand forecasts, spending) | 1h |
| 21 | Debounce inventory search input | 15m |
| 22 | Optimize backlog-PO lookup with set-based approach | 15m |
| 23 | Add loading skeletons for better perceived performance | 2h |

## Phase 5: Production Readiness

| # | Task | Effort |
|---|------|--------|
| 24 | Add authentication (JWT-based) | 8h |
| 25 | Add rate limiting (slowapi) | 1h |
| 26 | Add structured logging | 2h |
| 27 | Add health check endpoint | 15m |
| 28 | Environment-based configuration (pydantic Settings) | 1h |
| 29 | HTTPS/TLS configuration | 1h |
| 30 | Update outdated dependencies (axios 1.6->1.7) | 30m |

**Total estimated effort: ~50-55 hours**

---

## Detailed Findings

### Security Vulnerabilities

| Vulnerability | Severity | Location |
|--------------|----------|----------|
| CORS wildcard + credentials | CRITICAL | `main.py:50-57` |
| No authentication/authorization | CRITICAL | All endpoints |
| No input validation on query params | HIGH | `main.py:34-48` |
| No HTTPS enforcement | HIGH | `main.py:409` |
| No rate limiting | HIGH | All endpoints |
| No CSRF protection | MEDIUM | POST endpoints |
| No security headers | MEDIUM | Missing X-Frame-Options, etc. |
| No request size limits | MEDIUM | POST endpoints |
| Hardcoded API URL | LOW | `api.js:3` |
| No API request timeout | LOW | `api.js` |

### Untested Endpoints

- `GET /api/orders/{order_id}`
- `GET /api/reports/quarterly`
- `GET /api/reports/monthly-trends`
- `GET /api/restocking/recommendations`
- `POST /api/restocking/orders`
- `GET /api/restocking/orders`

### Data Inconsistencies

- `inventory.json`: Springs and pulleys categorized as "Sensors"
- `demand_forecasts.json`: PSU-501 unit_cost ($34.99) differs from inventory.json ($18.99)
- `demand_forecasts.json`: SNR-420 SKU not in inventory.json
- `spending.json`: Category percentages sum to >100%
