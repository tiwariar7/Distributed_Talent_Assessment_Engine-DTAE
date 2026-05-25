# ⚡ DTAE — Technology Stack Reference

> **Distributed Talent Assessment Engine** — A production-grade, distributed coding assessment platform.
> This document catalogues **every technology** used in the project and explains **why** it was chosen.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Backend — Core Framework](#backend--core-framework)
3. [Databases & Data Stores](#databases--data-stores)
4. [Async Task Processing & Message Broker](#async-task-processing--message-broker)
5. [Real-Time Communication](#real-time-communication)
6. [Sandboxed Code Execution](#sandboxed-code-execution)
7. [Object Storage](#object-storage)
8. [Frontend](#frontend)
9. [Reverse Proxy & Load Balancing](#reverse-proxy--load-balancing)
10. [Containerization & Orchestration](#containerization--orchestration)
11. [Observability & Monitoring](#observability--monitoring)
12. [Authentication & Security](#authentication--security)
13. [CI/CD & Code Quality](#cicd--code-quality)
14. [Testing](#testing)
15. [Developer Tooling](#developer-tooling)
16. [Complete Dependency Table](#complete-dependency-table)

---

## Architecture Overview

```
┌──────────────┐      ┌─────────────┐      ┌──────────────────┐
│   Next.js    │◄────►│    Nginx     │◄────►│   Django / DRF   │
│   Frontend   │      │  (Reverse   │      │   (REST API +    │
│  (React 19)  │      │   Proxy)    │      │   WebSockets)    │
└──────────────┘      └─────────────┘      └────────┬─────────┘
                                                    │
                    ┌───────────────────────────────┼───────────────────────────┐
                    │                               │                           │
             ┌──────▼──────┐              ┌─────────▼──────────┐     ┌─────────▼─────────┐
             │ PostgreSQL  │              │     CouchDB        │     │      Redis        │
             │ (Relational │              │ (Document Store /  │     │ (Cache / Channel  │
             │  ACID, 3NF) │              │  MVCC / MapReduce) │     │  Layer / ZSETs)   │
             └─────────────┘              └────────────────────┘     └───────────────────┘
                                                                              │
                    ┌─────────────────────────────────────────────────────────┘
                    │
             ┌──────▼──────┐       ┌────────────────┐       ┌──────────────────┐
             │  RabbitMQ   │◄─────►│  Celery Workers │◄─────►│ Docker Sandbox   │
             │  (AMQP      │       │ (Task Execution │       │ (Isolated Code   │
             │   Broker)   │       │  & Routing)     │       │  Execution)      │
             └─────────────┘       └────────────────┘       └──────────────────┘
                                                                     │
                                                              ┌──────▼──────┐
                                                              │   MinIO     │
                                                              │ (S3 Object  │
                                                              │  Storage)   │
                                                              └─────────────┘
```

---

## Backend — Core Framework

| Technology | Version | Why It's Used |
|---|---|---|
| **Python** | 3.12 | Primary backend language. Mature ecosystem, excellent library support for web, async, and data processing. |
| **Django** | 5.0–5.1 | Full-featured web framework providing ORM, admin panel, auth system, migrations, and middleware pipeline. Chosen for its "batteries-included" philosophy and mature security posture. |
| **Django REST Framework (DRF)** | 3.15 | Extends Django with serializers, viewsets, pagination, throttling, and permission classes to build a robust RESTful API. |
| **django-environ** | 0.11 | 12-factor-style environment variable management. Loads `.env` files and casts values to correct Python types. |
| **django-cors-headers** | 4.3 | Handles Cross-Origin Resource Sharing headers so the Next.js frontend (running on a different port/domain) can call the Django API. |
| **django-csp** | 3.7 | Adds Content Security Policy headers to HTTP responses, preventing XSS and data injection attacks. |
| **Gunicorn** | 22.x | Production WSGI HTTP server. Multi-worker process model for serving Django in production behind Nginx. |
| **Daphne** | 4.1 | ASGI server that supports both HTTP and WebSocket protocols. Used in development and Docker Compose to serve Django Channels. |
| **Kombu** | (via Celery) | Messaging library used to define AMQP exchanges, queues, and dead-letter routing topology for Celery. |

---

## Databases & Data Stores

### PostgreSQL 16 (Alpine)

| Aspect | Details |
|---|---|
| **Role** | Primary relational database (ACID-compliant, 3NF-normalized) |
| **Why** | Stores all structured data — users, roles, organizations, assessments, problems, submissions, invitations, proctoring sessions, and audit logs. Provides transactional integrity via `SELECT FOR UPDATE` and atomic `transaction.atomic()` blocks. |
| **Driver** | `psycopg` 3.x (async-capable PostgreSQL adapter) |
| **Key Features Used** | Unique constraints, composite indexes, `JSONField`, `BigAutoField`, optimistic concurrency via `update_fields` |

### Apache CouchDB 3.3

| Aspect | Details |
|---|---|
| **Role** | Document store for unstructured/semi-structured data |
| **Why** | Stores source code blobs, execution logs, test case definitions, and leaderboard entries. Its MVCC (Multi-Version Concurrency Control) model allows lock-free concurrent appends — multiple Celery workers can simultaneously write to the same execution log document using `_rev` tokens and exponential backoff retries. |
| **Client** | Custom HTTP client built on `requests` library (REST API) |
| **Key Features Used** | MVCC conflict resolution, MapReduce views, design documents, append-only log pattern |

### Redis 7 (Alpine)

| Aspect | Details |
|---|---|
| **Role** | Multi-purpose in-memory data store |
| **Why** | Serves **four distinct roles**: |
| | 1. **Django Cache Backend** — Page/query caching via `RedisCache` |
| | 2. **Django Channels Layer** — Pub/sub backbone for WebSocket message routing |
| | 3. **Celery Result Backend** — Stores task results from asynchronous jobs |
| | 4. **Leaderboard Rankings** — Sorted sets (`ZSET`) and hashes for O(log N) real-time ranking with `ZREVRANGE` |
| **Client** | `redis-py` 5.x + `redis.asyncio` for WebSocket consumers |

---

## Async Task Processing & Message Broker

### Celery 5.3

| Aspect | Details |
|---|---|
| **Role** | Distributed task queue for asynchronous code evaluation |
| **Why** | Offloads CPU-intensive and I/O-heavy work (Docker container spin-up, code execution, scoring) from the request-response cycle. Supports priority queues, automatic retries with exponential backoff, task revocation, and dead-letter routing. |
| **Key Features Used** | `shared_task`, `autoretry_for`, `retry_backoff`, `apply_async` with queue routing, task revocation via `app.control.revoke()` |

**Queue Topology:**

| Queue | Purpose |
|---|---|
| `high_priority` | Submission evaluation tasks (priority 10) |
| `medium_priority` | Leaderboard update tasks |
| `low_priority` | Recruiter re-evaluation tasks |
| `maintenance` | Cleanup and housekeeping tasks |
| `dead_letter` | Failed tasks routed via DLX for analysis |
| `lang_python`, `lang_cpp`, `lang_java`, `lang_javascript` | Language-specific queues for distributed scaling |

### RabbitMQ 3.13 (Management Alpine)

| Aspect | Details |
|---|---|
| **Role** | AMQP message broker for Celery |
| **Why** | Provides reliable message delivery with acknowledgments, dead-letter exchanges (DLX), priority queues (`x-max-priority`), and a management UI on port 15672 for operational visibility. More robust than Redis as a broker for production workloads. |

---

## Real-Time Communication

### Django Channels 4.x + channels-redis 4.2

| Aspect | Details |
|---|---|
| **Role** | WebSocket support for live execution streaming |
| **Why** | Enables real-time, bidirectional communication between Celery workers and browser clients. When a test case completes in a Docker sandbox, the result is published to a Redis channel group, and all connected WebSocket clients receive the update instantly — no polling required. |
| **Consumers** | `SubmissionExecutionConsumer` — streams execution logs, status changes, and scoring results |
| | Leaderboard consumer — broadcasts live ranking updates |
| | Proctoring consumer — relays anti-cheating violation events |
| **Auth** | JWT-based WebSocket authentication via query parameter (`?token=<jwt>`) |
| **Security** | Per-user connection limits enforced via Redis counters, token expiry validation |

---

## Sandboxed Code Execution

### Docker SDK for Python 7.x

| Aspect | Details |
|---|---|
| **Role** | Programmatic Docker container management for isolated code execution |
| **Why** | Each candidate's code runs inside an ephemeral, hardened Docker container. The host machine never executes untrusted code directly. |

**Sandbox Security Hardening:**

| Security Measure | Implementation |
|---|---|
| Network isolation | `network_disabled=True` |
| Read-only filesystem | `read_only=True` |
| Privilege restriction | `security_opt=["no-new-privileges"]`, `cap_drop=["ALL"]` |
| Memory limits | Configurable via `DOCKER_EXECUTOR_MEMORY_MB` (default 128MB) |
| Process limits | `pids_limit=64` |
| Time limits | Configurable timeout with `container.wait(timeout=...)` |
| Non-root execution | `user="nobody"` inside container |
| Temp filesystem | `tmpfs={"/tmp": "rw,size=64m"}` |

**Supported Languages (Strategy Pattern):**

| Language | Runtime | Sandbox Image |
|---|---|---|
| Python 3 | `python3` interpreter | `dtae/multi-sandbox:latest` |
| JavaScript | Node.js (`node`) | `dtae/multi-sandbox:latest` |
| C++ (C++20) | `g++ -O3 -std=c++20` | `dtae/multi-sandbox:latest` |
| Java (JDK 21) | `javac` + `java` (1.5x timeout multiplier) | `dtae/multi-sandbox:latest` |

### Tecnativa Docker Socket Proxy

| Aspect | Details |
|---|---|
| **Role** | Secure proxy for Docker socket access in production |
| **Why** | Instead of mounting `/var/run/docker.sock` directly (security risk), the API container communicates with Docker via a restricted TCP proxy that only allows container, image, and network operations. |

---

## Object Storage

### MinIO (S3-Compatible)

| Aspect | Details |
|---|---|
| **Role** | Object storage for execution artifacts |
| **Why** | Stores stdout/stderr log files from code executions as persistent artifacts. S3-compatible API via `boto3`, enabling future migration to AWS S3 without code changes. |
| **Client** | `boto3` 1.34 with S3v4 signature |
| **Bucket** | `dtae-artifacts` (auto-created on startup) |

---

## Frontend

| Technology | Version | Why It's Used |
|---|---|---|
| **Next.js** | 16.2.6 | React meta-framework with App Router, SSR/SSG, file-based routing, and optimized production builds. Provides the candidate workspace, recruiter dashboard, and authentication flows. |
| **React** | 19.2.4 | UI component library. Hooks-based architecture for state management, side effects, and WebSocket lifecycle management. |
| **TypeScript** | 5.x | Adds static typing to JavaScript for safer refactoring, better IDE support, and self-documenting interfaces. |
| **Monaco Editor** | 4.7 (`@monaco-editor/react`) | VS Code's editor component embedded in the browser. Provides syntax highlighting, IntelliSense, and language-aware editing for Python, JavaScript, C++, and Java. |
| **CSS Modules** | (built-in Next.js) | Scoped component styling via `page.module.css` preventing class name collisions. |
| **ESLint** | 9.x + `eslint-config-next` | Static analysis and linting for TypeScript/React code quality. |
| **Node.js** | 20 (Alpine) | Runtime for Next.js server and build toolchain. |

**Frontend Pages/Routes:**

| Route | Purpose |
|---|---|
| `/` | Login + Candidate workspace (code editor, execution logs, leaderboard) |
| `/register` | Account registration |
| `/forgot-password` | Password reset flow |
| `/verify` | Email verification |
| `/profile` | User profile management |
| `/candidate/invitations` | Assessment invitations for candidates |
| `/recruiter/*` | Recruiter dashboard and assessment management |
| `/assessment/*` | Assessment-taking interface |
| `/dsa-intelligence` | DSA practice and question bank |

---

## Reverse Proxy & Load Balancing

### Nginx 1.25 (Alpine)

| Aspect | Details |
|---|---|
| **Role** | Reverse proxy, load balancer, and static asset server |
| **Why** | Single entry point (port 80) that routes traffic to appropriate upstream services. Handles WebSocket upgrade headers for `/ws/` routes, proxies API calls to Django, and serves the Next.js frontend. |

**Routing Rules:**

| Path | Upstream |
|---|---|
| `/` | Next.js frontend (port 3000) |
| `/api/*` | Django backend (port 8000) |
| `/admin/*` | Django admin (port 8000) |
| `/ws/*` | Django Channels WebSocket (port 8000, HTTP/1.1 upgrade) |
| `/health/*` | Django health checks (port 8000) |
| `/metrics` | Prometheus metrics endpoint (port 8000) |
| `/static/*` | Django static files (port 8000) |

---

## Containerization & Orchestration

### Docker & Docker Compose

| Aspect | Details |
|---|---|
| **Role** | Application containerization and local orchestration |
| **Why** | Provides consistent, reproducible environments across development and production. Multi-stage builds minimize image sizes. |

**Docker Compose Profiles:**

| File | Purpose | Services |
|---|---|---|
| `docker-compose.yml` | Development | PostgreSQL, CouchDB, Redis, RabbitMQ, API |
| `docker-compose.prod.yml` | Production | All above + Worker, Frontend, Nginx, MinIO, Docker Proxy |
| `docker-compose.monitoring.yml` | Observability stack | Prometheus, Grafana, Jaeger |

### Kubernetes (Manifests + Helm)

| Aspect | Details |
|---|---|
| **Role** | Production container orchestration |
| **Why** | Provides horizontal scaling, rolling deployments, health-based routing, and auto-scaling. |

**K8s Manifests:**

| Manifest | Purpose |
|---|---|
| `namespace.yaml` | Isolated `dtae` namespace |
| `django-api.yaml` | API server Deployment + Service |
| `celery-worker.yaml` | Worker Deployment with resource limits |
| `hpa-worker.yaml` | Horizontal Pod Autoscaler for Celery workers |
| `postgres.yaml` | PostgreSQL StatefulSet |
| `couchdb.yaml` | CouchDB StatefulSet |
| `redis.yaml` | Redis Deployment |
| `rabbitmq.yaml` | RabbitMQ Deployment |
| `minio.yaml` | MinIO StatefulSet |
| `ingress.yaml` | Ingress resource for external traffic routing |

---

## Observability & Monitoring

### Prometheus

| Aspect | Details |
|---|---|
| **Role** | Metrics collection and alerting |
| **Why** | Scrapes the `/metrics` endpoint exposed by the Django `PrometheusMiddleware`. Tracks HTTP latency, request counts, sandbox execution durations, container failures, WebSocket connections, CouchDB conflict retries, leaderboard update latency, and Celery queue depths. |
| **Client** | `prometheus-client` 0.19 |

**Custom Metrics Exposed:**

| Metric | Type | Description |
|---|---|---|
| `http_request_latency_seconds` | Histogram | HTTP request latency by method/endpoint |
| `http_requests_total` | Counter | Total HTTP requests by method/endpoint/status |
| `celery_queue_depth` | Gauge | Current depth of each Celery queue |
| `sandbox_execution_duration_seconds` | Histogram | Docker sandbox execution time by language |
| `sandbox_startup_seconds` | Histogram | Container startup time by language |
| `sandbox_container_failures_total` | Counter | Sandbox failures by language/reason |
| `websocket_connections_active` | Gauge | Active WebSocket connections |
| `couchdb_conflict_retries_total` | Counter | MVCC conflict retry count |
| `leaderboard_update_latency_seconds` | Histogram | Leaderboard upsert latency |
| `leaderboard_cache_hits_total` / `misses` | Counter | Redis cache hit/miss ratio |

### OpenTelemetry (OTel)

| Aspect | Details |
|---|---|
| **Role** | Distributed tracing across Django, Celery, CouchDB, and Docker |
| **Why** | Provides end-to-end request tracing. Instruments Django HTTP handlers and Celery tasks automatically. Custom spans track CouchDB operations and Docker execution. |
| **Packages** | `opentelemetry-api`, `opentelemetry-sdk`, `opentelemetry-instrumentation-django`, `opentelemetry-instrumentation-celery`, `opentelemetry-exporter-otlp` |
| **Exporter** | OTLP/gRPC to Jaeger (falls back to console if unavailable) |

### Grafana 10.4

| Aspect | Details |
|---|---|
| **Role** | Metrics visualization and dashboarding |
| **Why** | Pre-provisioned dashboards for DTAE metrics. Connected to Prometheus as a data source. Includes a `grafana-dashboard.json` with panels for all custom metrics. |

### Jaeger 1.55

| Aspect | Details |
|---|---|
| **Role** | Distributed trace visualization |
| **Why** | Receives OpenTelemetry trace data via OTLP (port 4317/4318). Provides a UI (port 16686) to inspect end-to-end request flows across Django → Celery → CouchDB → Docker. |

### Structured Logging

| Aspect | Details |
|---|---|
| **Role** | Production-ready log management |
| **Why** | Custom `JsonFormatter` emits single-line JSON logs with structured fields (`submission_id`, `problem_id`, etc.) for log aggregation tools. Switchable between human-readable and JSON format via `LOG_FORMAT` env var. |

---

## Authentication & Security

| Technology | Why It's Used |
|---|---|
| **JWT (SimpleJWT 5.3)** | Stateless authentication via access/refresh token pairs. Access tokens expire in 60 minutes; refresh tokens in 7 days. Tokens carry role claims for RBAC. |
| **RBAC (Role-Based Access Control)** | Normalized `Role` and `Membership` models enforce recruiter/candidate/admin permissions. Custom DRF permission classes gate API endpoints. |
| **django-csp** | Content Security Policy headers prevent XSS by whitelisting allowed script/style/font sources. |
| **CORS (django-cors-headers)** | Controls which origins can access the API from browser-based clients. |
| **Rate Limiting (DRF Throttling)** | Configurable per-endpoint throttles: `200/hour` for general use, `10/min` for submissions, `5/min` for login, `100/sec` anti-DoS. |
| **Security Headers** | `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `X-XSS-Protection`, HSTS support. |
| **Audit Logging** | `AuditLog` model tracks security-relevant actions with IP address and user agent. |
| **Session Tracking** | `UserSession` model monitors active sessions and device info. |
| **Proctoring System** | Real-time anti-cheating: tab switches, copy/paste detection, camera/mic monitoring, fullscreen exit, idle timeout — with configurable auto-submit on violation threshold. |

---

## CI/CD & Code Quality

### GitHub Actions

| Workflow | Trigger | What It Does |
|---|---|---|
| **CI Pipeline** (`ci.yml`) | Push/PR to `main` | Spins up PostgreSQL, Redis, CouchDB as services → installs Python 3.12 deps → runs migrations → executes `pytest` |
| **Security & Linting** (`security.yml`) | Push/PR to `main` | Runs `ruff check .` for linting and `bandit -r` for security vulnerability scanning |
| **Build Sandbox Image** (`docker.yml`) | Changes to `docker/sandbox/` | Builds the multi-language sandbox Docker image |

### Code Quality Tools

| Tool | Purpose |
|---|---|
| **Ruff** | Ultra-fast Python linter and formatter (replaces flake8, isort, black) |
| **Bandit** | Static security analysis for Python — detects common vulnerabilities |
| **ESLint** | JavaScript/TypeScript linting with Next.js-specific rules |

---

## Testing

| Tool | Version | Purpose |
|---|---|---|
| **pytest** | 8.x | Test runner with rich assertion introspection and plugin ecosystem |
| **pytest-django** | 4.8 | Django integration — provides `@pytest.mark.django_db`, `client` fixture, settings override |
| **pytest-asyncio** | 0.23 | Async test support for testing Channels consumers and async views |
| **pytest-mock** | 3.14 | `mocker` fixture for mocking Docker, CouchDB, and external services |
| **responses** | 0.25 | Mock HTTP responses for CouchDB client tests without a live server |

**Test Coverage Areas:**

| Test File | What It Covers |
|---|---|
| `test_auth.py` | User registration, login, JWT issuance |
| `test_auth_upgrade.py` | Role upgrades, token refresh, session management |
| `test_couchdb_mvcc.py` | MVCC conflict resolution, exponential backoff retries |
| `test_concurrency_resilience.py` | Race conditions, concurrent document updates |
| `test_submissions_api.py` | Submission creation, queueing, status transitions |
| `test_events.py` | WebSocket event publishing and channel layer integration |
| `test_execution_log.py` | CouchDB execution log append operations |
| `test_leaderboard.py` | Score aggregation, ranking calculation |
| `test_leaderboard_zset.py` | Redis ZSET operations for real-time rankings |
| `test_recruiter_api.py` | Recruiter endpoints, assessment CRUD, invitation flow |
| `test_runners.py` | Language execution strategy pattern (Python, JS, C++, Java) |
| `test_health.py` | Dependency health probes (PostgreSQL, CouchDB, Redis) |
| `test_dsa_ingestion.py` | DSA question bank data ingestion |
| `test_seed_command.py` | Demo data seeding management command |

---

## Developer Tooling

| Tool | Purpose |
|---|---|
| **django-environ** | `.env` file parsing for local development configuration |
| **Docker Compose** | One-command local environment (`docker-compose up --build`) |
| **Django Admin** | Built-in admin panel for data inspection and management |
| **Management Commands** | `bootstrap_couchdb` (DB setup), `seed_demo_data` (demo data), DSA question ingestion |
| **pyproject.toml** | Python project metadata and tool configuration |
| **git_committer.py** | Custom Git automation script for structured commits |

---

## Complete Dependency Table

### Backend (Python — `requirements.txt`)

| Package | Category | Purpose |
|---|---|---|
| `Django>=5.0` | Core | Web framework |
| `djangorestframework>=3.15` | Core | REST API toolkit |
| `djangorestframework-simplejwt>=5.3` | Auth | JWT authentication |
| `django-environ>=0.11` | Config | Environment variable management |
| `django-cors-headers>=4.3` | Security | CORS header handling |
| `django-csp>=3.7` | Security | Content Security Policy |
| `psycopg[binary]>=3.1` | Database | PostgreSQL driver |
| `requests>=2.31` | HTTP | CouchDB REST client |
| `celery[redis]>=5.3` | Async | Distributed task queue |
| `redis>=5.0` | Cache/Broker | Redis client |
| `channels>=4.0` | WebSocket | ASGI WebSocket support |
| `channels-redis>=4.2` | WebSocket | Redis-backed channel layer |
| `daphne>=4.1` | Server | ASGI HTTP/WS server |
| `docker>=7.0` | Execution | Docker SDK for sandbox |
| `boto3>=1.34` | Storage | MinIO/S3 client |
| `prometheus-client>=0.19` | Monitoring | Prometheus metrics |
| `opentelemetry-api>=1.22` | Tracing | OTel API |
| `opentelemetry-sdk>=1.22` | Tracing | OTel SDK |
| `opentelemetry-instrumentation-django` | Tracing | Django auto-instrumentation |
| `opentelemetry-instrumentation-celery` | Tracing | Celery auto-instrumentation |
| `opentelemetry-exporter-otlp>=1.22` | Tracing | OTLP gRPC exporter |
| `gunicorn>=22.0` | Server | Production WSGI server |
| `ruff>=0.4` | Dev | Linter/formatter |
| `pytest>=8.0` | Test | Test runner |
| `pytest-django>=4.8` | Test | Django test integration |
| `pytest-asyncio>=0.23` | Test | Async test support |
| `pytest-mock>=3.14` | Test | Mocking utilities |
| `responses>=0.25` | Test | HTTP response mocking |

### Frontend (Node.js — `package.json`)

| Package | Category | Purpose |
|---|---|---|
| `next@16.2.6` | Core | React meta-framework (App Router) |
| `react@19.2.4` | Core | UI component library |
| `react-dom@19.2.4` | Core | React DOM renderer |
| `@monaco-editor/react@4.7` | Editor | VS Code editor component |
| `typescript@5.x` | Dev | Static typing |
| `eslint@9.x` | Dev | Code linting |
| `eslint-config-next@16.2.6` | Dev | Next.js ESLint rules |
| `@types/node`, `@types/react`, `@types/react-dom` | Dev | TypeScript type definitions |

### Infrastructure (Docker Images)

| Image | Version | Purpose |
|---|---|---|
| `python` | 3.12-slim | Backend API container base |
| `node` | 20-alpine | Frontend container base |
| `postgres` | 16-alpine | Relational database |
| `couchdb` | 3.3 | Document store |
| `redis` | 7-alpine | Cache, channel layer, result backend |
| `rabbitmq` | 3.13-management-alpine | Message broker |
| `minio/minio` | latest | S3-compatible object storage |
| `nginx` | 1.25-alpine | Reverse proxy |
| `alpine` | 3.19 | Multi-language sandbox base |
| `prom/prometheus` | v2.51.0 | Metrics server |
| `grafana/grafana` | 10.4.1 | Metrics dashboards |
| `jaegertracing/all-in-one` | 1.55 | Distributed tracing |
| `tecnativa/docker-socket-proxy` | latest | Secure Docker socket access |

---

## Key Design Decisions

| Decision | Rationale |
|---|---|
| **Hybrid PostgreSQL + CouchDB** | Relational data (users, assessments) needs ACID; unstructured data (execution logs, source code) benefits from CouchDB's schema-free documents and MVCC. |
| **RabbitMQ over Redis as Celery broker** | RabbitMQ provides message acknowledgments, dead-letter exchanges, and priority queues — critical for reliable task processing at scale. |
| **Docker-in-Docker sandbox** | Complete isolation of untrusted candidate code. No shared process space, filesystem, or network with the host. |
| **Strategy Pattern for languages** | Adding a new language requires only a new `LanguageRunner` subclass — no changes to the executor or task code (Open/Closed Principle). |
| **Redis ZSET for leaderboard** | O(log N) insert and O(log N + M) range queries for real-time rankings, with PostgreSQL as the source of truth on cache miss. |
| **WebSockets for live updates** | Eliminates polling overhead. Candidates see test case results streaming in real-time as each Docker container completes. |
| **MVCC over pessimistic locking** | CouchDB's `_rev`-based concurrency allows multiple Celery workers to append to the same execution log without database-level locks. |

---

> **Last Updated:** May 2026
> **Maintainer:** DTAE Engineering Team
