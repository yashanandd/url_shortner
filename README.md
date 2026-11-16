# LinkFlow – Production-Scale URL Shortening Platform

LinkFlow is a high-throughput, production-ready distributed URL Shortener and Analytics engine built with FastAPI, PostgreSQL, Redis, Redis Streams, and React (Vite).

Product specifications and system design decisions are documented in [PRD.md](./PRD.md).

---

## 1. System Architecture

```text
                  +---------------------------+
                  |   React 19 + Tailwind     |
                  | (Vite SPA + Recharts UI)  |
                  +-------------+-------------+
                                | HTTP REST
                                v
                  +---------------------------+
                  |      FastAPI Backend      |
                  | (Async ASGI / Rate Limit) |
                  +-------------+-------------+
                                |
        +-----------------------+-----------------------+
        |                                               |
        v                                               v
+----------------+                             +----------------+
|  Redis Cache   |                             |   PostgreSQL   |
| - URL 24h TTL  |                             | (SQLAlchemy 2  |
| - 60s Anti-Scan|                             |   + Alembic)   |
| - Sliding Limit|                             +-------+--------+
| - Redis Streams|                                     ^
+-------+--------+                                     |
        | XADD clicks:stream                           | Batch Inserts
        v                                              |
+----------------+                                     |
| Stream Worker  |-------------------------------------+
| (GeoIP/UA/Salt)|
+----------------+
```

### Core Technical Capabilities
- **Sub-Millisecond Redirects**: Cache-aside with 24h Redis TTL, negative caching (60s) for non-existent codes to protect against brute-force database scans, and active invalidation.
- **Cryptographic 7-Character Base62 Generator**: $62^7 \approx 3.52 \times 10^{12}$ unique permutations using `secrets.choice` with automatic database uniqueness retries.
- **SSRF & Abuse Shield**: Scheme validation, loopback/private IP blocking (`127.0.0.0/8`, `10.0.0.0/8`, `192.168.0.0/16`, etc.), circular redirect protection, and reserved route blocklist.
- **Decoupled Asynchronous Analytics**: The redirect path (`GET /{short_code}`) executes a non-blocking `XADD` to Redis Streams and returns HTTP 302 immediately. A background consumer worker parses User-Agents, hashes IPs for privacy compliance, and batch-inserts click metrics and daily aggregates.
- **Dual-Token Authentication**: Short-lived JWT access tokens + Redis-tracked refresh tokens with rotation and instant revocation.
- **Redis Sliding-Window Rate Limiter**: Tiered thresholds across auth endpoints, link creation, and public redirects.

---

## 2. Quickstart

### Prerequisites
- Docker & Docker Compose
- Python 3.10+
- Node.js 18+ and npm

### Step 1: Start Backing Services (PostgreSQL & Redis)
From the repository root:

```powershell
docker compose up -d
```

Verify containers are running and healthy:
```powershell
docker compose ps
```

### Step 2: Backend Setup & API Server
In a terminal window:

```powershell
cd backend
.\env\Scripts\activate
# If dependencies need installing:
python -m pip install -r requirements.txt

# Run database migrations (or tables auto-create in development)
alembic upgrade head

# Start FastAPI API & Redirect Engine
uvicorn main:app --reload --port 8000
```

- API Server: `http://localhost:8000`
- Interactive Swagger Docs: `http://localhost:8000/docs`
- Health Endpoint: `http://localhost:8000/health`

### Step 3: Frontend Development Server
In a second terminal window:

```powershell
cd frontend
npm install
npm run dev
```

- Web UI: `http://localhost:5173`

---

## 3. Running Tests & Quality Checks

### Backend Unit & Security Tests
```powershell
cd backend
.\env\Scripts\python.exe -m pytest tests
```

### Frontend Linting & Production Build
```powershell
cd frontend
npm run lint
npm run build
```

---

## 4. API Reference Summary

| Method | Route | Description | Auth Required |
|---|---|---|---|
| `GET` | `/{short_code}` | Sub-millisecond URL redirect (HTTP 302) | No |
| `POST` | `/api/v1/auth/register` | Register new user account | No |
| `POST` | `/api/v1/auth/login` | Log in and receive access + refresh tokens | No |
| `POST` | `/api/v1/auth/refresh` | Rotate access & refresh tokens | No |
| `POST` | `/api/v1/auth/logout` | Revoke refresh token | No |
| `GET` | `/api/v1/auth/me` | Fetch logged-in user profile | Bearer Token |
| `POST` | `/api/v1/urls/` | Shorten a URL (with optional alias & expiry) | Optional |
| `GET` | `/api/v1/urls/` | List user's shortened URLs with click totals | Bearer Token |
| `GET` | `/api/v1/urls/{id}` | Retrieve specific URL details | Bearer Token |
| `PATCH` | `/api/v1/urls/{id}` | Update destination, status, or expiry | Bearer Token |
| `DELETE` | `/api/v1/urls/{id}` | Delete shortened URL and evict cache | Bearer Token |
| `GET` | `/api/v1/analytics/{code}` | Retrieve click trends, devices, & referrers | Owner / Optional |
