# Product Requirements Document (PRD)

## Production-Scale URL Shortener

Production-grade project

Backend / System Design

Scalable architecture

Version 1.0 · November 2026 · Status: Proposed

## 1. Product Overview

### 1.1 Product Name

LinkFlow – Scalable URL Shortening Platform

### 1.2 Product Vision

Build a highly available, distributed URL shortening platform that converts long URLs into short, shareable links while providing real-time analytics, link management, security controls, and enterprise-level scalability.

The platform should support millions of shortened URLs and handle high-volume redirection traffic with minimal latency.

### 1.3 Problem Statement

Long URLs are difficult to share, remember, and manage. Businesses and developers also lack a centralized solution to:

- Generate short, customizable URLs.
- Track link clicks and user engagement.
- Manage expiration and access permissions.
- Identify suspicious or malicious links.
- Handle high-volume redirection traffic reliably.

LinkFlow aims to solve these problems through a scalable URL management and analytics platform.

### 1.4 Target Users

| User             | Requirements                        |
| ---------------- | ----------------------------------- |
| Individual users | Shorten and share URLs              |
| Developers       | API-based URL shortening            |
| Marketing teams  | Campaign tracking and analytics     |
| Businesses       | Custom domains and team management  |
| Administrators   | Monitoring, moderation and security |

## 2. Product Goals and Non-Goals

### Goals

1. Generate unique short URLs.
2. Redirect users with minimal latency.
3. Support millions of URL records.
4. Provide detailed click analytics.
5. Support custom aliases and expiration.
6. Provide authentication and authorization.
7. Prevent malicious URL abuse.
8. Expose REST APIs for third-party integration.
9. Maintain high availability and fault tolerance.

### Non-Goals (Initial Release)

- URL hosting or file hosting.
- Social networking functionality.
- Browser extensions.
- Native mobile applications.
- Monetization through advertisements.
- Full enterprise billing and invoicing.

## 3. Functional Requirements

These are the core features the platform must implement.

### FR-01: User Authentication

Users should be able to:

- Register using email and password.
- Log in and log out.
- Reset forgotten passwords.
- Verify their email.
- Access protected resources using JWT-based authentication.
- Manage their account profile.

Authorization levels:

| Role  | Permissions                           |
| ----- | ------------------------------------- |
| Guest | Redirect through public links         |
| User  | Create and manage personal links      |
| Admin | Manage users, links and abuse reports |

### FR-02: URL Shortening

Users should be able to submit a long URL and receive a shortened URL.

Example:

Original URL

[https://example.com/products/electronics/smartphones/iphone](https://example.com/products/electronics/smartphones/iphone?utm_source=chatgpt.com)

Short URL

# lnk.to/aB92xK

Requirements:

- Accept valid HTTP and HTTPS URLs.
- Generate unique short codes.
- Support automatic code generation.
- Allow optional custom aliases.
- Prevent duplicate aliases.
- Store original URL and short code.
- Return the generated short URL.
- Support optional expiration dates.
- Allow authenticated users to manage their URLs.

### FR-03: Short Code Generation

The system should generate unique identifiers for every shortened URL.

Proposed approach: Base62 encoding

Character set:

```
0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ
```

Example:

```
Database ID: 125789

Base62: 2Z3z

Short URL: lnk.to/2Z3z
```

Requirements:

- Codes must be unique.
- Codes should be URL-safe.
- Avoid predictable sequential identifiers where possible.
- Handle collisions safely.
- Support future horizontal scaling.

For production, use a distributed ID generator or collision-checked random identifiers rather than relying on a single database's auto-increment counter.

### FR-04: URL Redirection

When a user opens a short URL:

1. Extract the short code.
2. Check Redis cache.
3. If a cache hit occurs, retrieve the destination.
4. Otherwise, retrieve it from the database.
5. Validate link status and expiration.
6. Record click information asynchronously.
7. Redirect to the original URL.

Redirection response:

```
HTTP/1.1 302 Found
Location: https://example.com/products
```

Use HTTP 302 by default because destinations and link status may change. Permanent 301 redirects can be an optional setting.

### FR-05: Link Management

Users should have a dashboard to:

- View all shortened URLs.
- Search URLs.
- Filter by creation date.
- Edit destination URLs.
- Delete or deactivate URLs.
- Set expiration dates.
- Create custom aliases.
- View individual link statistics.

### FR-06: Analytics and Tracking

The system should capture click events.

Click information:

- Short code.
- Timestamp.
- Referrer.
- Device type.
- Browser.
- Operating system.
- Approximate geographic location.
- IP-derived information, subject to privacy controls.
- Campaign parameters (UTM).

Analytics dashboard:

[13 Best URL Shorteners to Shrink Your Links in 2025](https://images.openai.com/static-rsc-4/5IJtIWtLtmt9wyHlOkwjletIOO19RCwXTnu72RDaJzdzfmEN2gT4OYoeDlNzTcILItkfJ9eSSPB9pJy6N5255c4rE8WJklgGnh4cOMcdystkOq7NjNgRsEzsEIwmiMT-7xVDYoY0qVjdLLj3MrcDFedPdmVM9oGwiIz_c0h7pBE?purpose=inline)

[buffer.com](https://buffer.com/resources/best-url-shortener/?utm_source=chatgpt.com)

Metrics:

| Metric                  | Description                 |
| ----------------------- | --------------------------- |
| Total clicks            | All recorded clicks         |
| Unique visitors         | Estimated distinct visitors |
| Daily clicks            | Clicks per day              |
| Geographic distribution | Country-level traffic       |
| Device breakdown        | Mobile, desktop, tablet     |
| Browser breakdown       | Browser usage               |
| Referrer analytics      | Traffic sources             |

Unique visitor counts should be treated as estimates, not guaranteed identification of individual people.

### FR-07: Custom Aliases

Users can choose their own short codes.

Example:

```
lnk.to/my-portfolio
lnk.to/github
lnk.to/project-demo
```

Requirements:

- Alias must be unique.
- Enforce allowed characters.
- Reserve system routes.
- Limit alias length.
- Prevent impersonation and abusive names.

### FR-08: Expiration and Link Lifecycle

Support the following link statuses:

- Active
- Expired
- Disabled
- Deleted
- Flagged

The system should reject expired or disabled links and return an appropriate response page.

### FR-09: API Access

Developers should be able to create and manage links programmatically.

Example:

```
POST /api/v1/urls
Authorization: Bearer <token>
Content-Type: application/json
```

Request:

```
{
  "originalUrl": "https://example.com/products",
  "customAlias": "products",
  "expiresAt": "2027-01-01T00:00:00Z"
}
```

Response:

```
{
  "success": true,
  "data": {
    "shortCode": "products",
    "shortUrl": "https://lnk.to/products",
    "originalUrl": "https://example.com/products"
  }
}
```

## 4. Non-Functional Requirements

These requirements define production readiness.

| Requirement      | Target                         |
| ---------------- | ------------------------------ |
| Availability     | 99.9% initially                |
| Redirect latency | p95 below 100 ms               |
| API latency      | p95 below 300 ms               |
| Scalability      | Horizontal scaling             |
| Reliability      | No single point of failure     |
| Security         | OWASP-aligned practices        |
| Data durability  | Persistent database storage    |
| Cache            | Redis                          |
| Monitoring       | Metrics, logs and traces       |
| Recovery         | Automated backups and recovery |

These are engineering targets to validate through load testing, not guaranteed performance claims.

### Scalability targets

Design around an initial capacity-planning scenario:

- 10 million shortened URLs.
- 100 million redirects per month.
- 1 million registered users.
- Read-heavy workload.
- Traffic spikes during viral link sharing.

The architecture should support increasing traffic by adding application instances and scaling the data infrastructure.

## 5. System Architecture

[Designing a URL Shortener System: A Comprehensive Guide | by Surya Pratap Singh Chauhan | Medium](https://images.openai.com/static-rsc-4/cZ6JA7uakdyL3EJ_rGOsw-tEZF2OBPYZkVkVqZeRqv-atzj1p6S0_HKP1clco6_jj1a-LOaD_vz3Z36czTT7a0bdcACFbyGm87GWAScBy98_kNd_OOSW0TO-bPNM3IaUyXorJxeWWZRYjM6UcOdzTL7bZQ9lPBrYevNMkTrKUD8?purpose=inline)

[medium.com](https://medium.com/%40spsc/designing-a-url-shortener-system-a-comprehensive-guide-b6ad74878e1f?utm_source=chatgpt.com)

### Proposed Architecture

```
                 CLIENT
                    |
                    v
              CDN / WAF
                    |
                    v
              LOAD BALANCER
                    |
                    v
              API APPLICATION
                    |
          +---------+---------+
          |                   |
          v                   v
     URL SERVICE         AUTH SERVICE
          |
          v
      REDIS CACHE
          |
     Cache Miss
          |
          v
      DATABASE
          |
          v
     URL DESTINATION
          |
          v
       REDIRECT
          |
          +----------------------+
                                 |
                                 v
                           EVENT QUEUE
                                 |
                                 v
                         ANALYTICS WORKERS
                                 |
                                 v
                         ANALYTICS DATABASE
                                 |
                                 v
                         DASHBOARD / REPORTS
```

### Architecture components

| Component         | Responsibility                    |
| ----------------- | --------------------------------- |
| CDN               | Edge caching and traffic delivery |
| WAF               | Filter malicious requests         |
| Load Balancer     | Distribute incoming traffic       |
| API Service       | Handle application requests       |
| Redis             | Cache frequently accessed URLs    |
| PostgreSQL        | Store users and URL metadata      |
| Kafka / RabbitMQ  | Asynchronous event processing     |
| Analytics Workers | Process click events              |
| Analytics DB      | Store aggregated metrics          |

Important architectural decision: The redirect path should not wait for analytics processing. Click events should be published asynchronously so analytics failures do not unnecessarily slow down redirects.

## 6. Technology Stack

Considering a backend-oriented implementation, this is the recommended stack.

Frontend

Next.js, TypeScript, Tailwind CSS

Backend

Node.js, Express.js, TypeScript

Database

PostgreSQL, Prisma ORM

Caching

Redis

Message Queue

Apache Kafka

Authentication

JWT, bcrypt / Argon2

Infrastructure

Docker, Kubernetes, Nginx

CI/CD

GitHub Actions

Monitoring

Prometheus, Grafana, OpenTelemetry

## 7. Database Design

Use PostgreSQL as the primary transactional database.

### 7.1 Users Table

| Column        | Type             |
| ------------- | ---------------- |
| id            | UUID (PK)        |
| name          | VARCHAR          |
| email         | VARCHAR (Unique) |
| password_hash | TEXT             |
| role          | VARCHAR          |
| created_at    | TIMESTAMP        |

### 7.2 URLs Table

| Column       | Type             |
| ------------ | ---------------- |
| id           | UUID (PK)        |
| user_id      | UUID (FK)        |
| short_code   | VARCHAR (Unique) |
| original_url | TEXT             |
| custom_alias | VARCHAR          |
| status       | VARCHAR          |
| expires_at   | TIMESTAMP        |
| created_at   | TIMESTAMP        |
| updated_at   | TIMESTAMP        |

### 7.3 Click Events Table

| Column      | Type      |
| ----------- | --------- |
| id          | UUID      |
| short_code  | VARCHAR   |
| clicked_at  | TIMESTAMP |
| referrer    | TEXT      |
| user_agent  | TEXT      |
| ip_hash     | VARCHAR   |
| country     | VARCHAR   |
| device_type | VARCHAR   |

### 7.4 Analytics Aggregates Table

| Column          | Type    |
| --------------- | ------- |
| id              | UUID    |
| short_code      | VARCHAR |
| date            | DATE    |
| total_clicks    | BIGINT  |
| unique_visitors | BIGINT  |
| mobile_clicks   | BIGINT  |
| desktop_clicks  | BIGINT  |

Database indexing strategy:

- Unique index on `short_code`.
- Index on `user_id`.
- Index on `created_at`.
- Composite index on `short_code, clicked_at`.
- Index on expiration and status for lifecycle processing.

For high-volume analytics, partition click events by time and use retention policies. Consider ClickHouse or another analytical database when PostgreSQL aggregation becomes a bottleneck.

## 8. API Specifications

| Method | Endpoint                   | Purpose          |
| ------ | -------------------------- | ---------------- |
| POST   | `/api/v1/auth/register`    | Register         |
| POST   | `/api/v1/auth/login`       | Login            |
| POST   | `/api/v1/urls`             | Create short URL |
| GET    | `/api/v1/urls`             | List user's URLs |
| GET    | `/api/v1/urls/:id`         | Get URL details  |
| PATCH  | `/api/v1/urls/:id`         | Update URL       |
| DELETE | `/api/v1/urls/:id`         | Delete URL       |
| GET    | `/api/v1/analytics/:code`  | Get analytics    |
| GET    | `/:code`                   | Redirect         |
| POST   | `/api/v1/urls/:id/disable` | Disable link     |

All authenticated endpoints must enforce ownership checks and role-based authorization.

## 9. Security Requirements

Security is essential because URL shorteners can be exploited for phishing and malicious redirection.

| Threat              | Mitigation                                   |
| ------------------- | -------------------------------------------- |
| SQL Injection       | Parameterized queries / ORM                  |
| XSS                 | Output encoding and CSP                      |
| Brute Force         | Rate limiting                                |
| Malicious URLs      | Reputation checks and abuse detection        |
| Unauthorized access | JWT and RBAC                                 |
| ID enumeration      | Randomized codes                             |
| API abuse           | API key and request limits                   |
| DDoS                | CDN and WAF                                  |
| Account compromise  | Secure password hashing and session controls |

Additional requirements:

- Validate URL schemes.
- Block internal and private network destinations when checking submitted URLs.
- Protect URL preview and metadata-fetching functionality against SSRF.
- Never blindly fetch user-submitted URLs from backend workers.
- Add abuse reporting and automated moderation.
- Use soft deletion where auditability is required.

## 10. Caching Strategy

Redis will reduce database load and improve redirect performance.

Cache-aside pattern:

```
1. User visits /abc123

2. Check Redis:
   GET url:abc123

3. Cache HIT:
   Return destination

4. Cache MISS:
   Query PostgreSQL

5. Save result in Redis

6. Return destination
```

Example:

```
Key: url:abc123
Value: https://example.com/products
TTL: 3600 seconds
```

Additional considerations:

- Cache invalidation when URLs change.
- Delete cache entries when links are disabled.
- Prevent cache stampedes.
- Use negative caching carefully for nonexistent codes.
- Avoid indefinite caching of expiring links.
- Use distributed Redis infrastructure with appropriate failover.

## 11. Analytics Processing

Analytics should be event-driven.

Processing flow:

1. A redirect request arrives.
2. The redirect service resolves the destination.
3. A click event is published to Kafka.
4. A worker consumes the event.
5. The worker extracts device, browser and geographic information.
6. Aggregated metrics are updated.
7. The dashboard queries the aggregated data.

Example event:

```
{
  "shortCode": "abc123",
  "timestamp": "2026-11-03T12:00:00Z",
  "country": "IN",
  "device": "mobile",
  "browser": "Chrome",
  "referrer": "google.com"
}
```

Reliability requirements:

- At-least-once event delivery.
- Idempotent event processing.
- Dead-letter queue for failed events.
- Retry mechanism.
- Event retention and replay capabilities.

## 12. User Interface Requirements

### Main pages

[Dub Links  Review 2026: Features, Pricing, Pros & Cons](https://images.openai.com/static-rsc-4/_909T1SpTso0M42SAtogZmN63WQAFXSPT2BiYwGD7mHNBNT7Ufjev5zFyzWG6ELSfrU2zgFIGYTbAt2TA_6s8kRaSa4vdb0mn1aomDocGsVwXFLKq_A-Ew8LSSeVdYaR8YNfNejnPOWqQvBzoDU3CMBhr3lfGREyu8DmR0KLgXA?purpose=inline)

1\. Landing Page

URL input, shorten button and product introduction.

["Dub: Essential Tool for My YouTube Channel" | Dub](https://images.openai.com/static-rsc-4/5v8ooLt2t6qBJ-S0osN26YoaFnzLuPYgmocYqGT3rbD-nyEwKv8k3bu9F_zafDek2TG8oTxt3PUZcSOCmERAx8DNhtHL4PE01N8sexObZ9aGed4Qe1nF7NKffclHZ-OAnzpQxSNhdfrN9CK2s6JeyzqxqnvoYkkDmQwmVIpPND0?purpose=inline)

2\. Dashboard

Manage links, search and filter.

[Link Analytics - Track Clicks in Real Time - Linko](https://images.openai.com/static-rsc-4/nryZUuLg9BlyopCzIdyDTc7Hwn4g4ltPFtHqPl8wC4O0uoHVqAOUWCSvJqaDp86pTJVGZcjen8bDpDcqVolNOJOWOV4fhtMm93z7lQK3Z-MiVqWDhzXbpZW5XFgzUb68veWEeMF8NkiWrC_OMG1jfAGsO6V9B_gXKEJeUpB6OLE?purpose=inline)

3\. Analytics

Traffic charts, devices and geographic metrics.

[Security Settings Page Design Examples — 15+ SaaS UI Inspiration | Nicelydone](https://images.openai.com/static-rsc-4/t1R7uGnhYFqyuA0lEIthVD4yNRjgjIaojm03NuPelOoF-20_Tj-qMfSVmzceaufcza00FC9DiO27P6uFVVxxXOQUiQbu3i6wmKcJ0ji3-eTkLbQwQgLvR23HooMjO0V-C0gEdG824off7Dy3JVuX305M12fa5ZySFsJTlmiEbWI?purpose=inline)

4\. Settings

Profile, API keys and account settings.

## 13. Deployment and Infrastructure

Recommended production infrastructure:

| Layer            | Technology            |
| ---------------- | --------------------- |
| Frontend hosting | Vercel / AWS          |
| Backend          | AWS ECS / Kubernetes  |
| Database         | AWS RDS PostgreSQL    |
| Cache            | AWS ElastiCache Redis |
| Messaging        | Amazon MSK / Kafka    |
| CDN              | Cloudflare            |
| Object storage   | AWS S3                |
| Monitoring       | Prometheus + Grafana  |
| CI/CD            | GitHub Actions        |

### Deployment requirements

- Dockerize all services.
- Use separate development, staging and production environments.
- Implement CI/CD pipelines.
- Configure health checks.
- Enable database backups.
- Use secrets management.
- Implement horizontal autoscaling.
- Configure centralized logging.
- Implement disaster recovery procedures.

## 14. Project Development Roadmap

A realistic implementation plan for an individual developer or small team.

1. Phase 1 – Core URL Shortening

   MVP
   - Project setup.
   - Database schema.
   - URL creation.
   - Base62/random code generation.
   - Redirect functionality.
   - Basic link management.
2. Phase 2 – Authentication and Management
   - Registration and login.
   - JWT authentication.
   - User dashboard.
   - Custom aliases.
   - Expiration and deletion.
3. Phase 3 – Analytics
   - Click event tracking.
   - Background workers.
   - Redis caching.
   - Kafka integration.
   - Analytics dashboard.
4. Phase 4 – Production Hardening
   - Rate limiting.
   - Abuse detection.
   - Security checks.
   - API documentation.
   - Logging and monitoring.
5. Phase 5 – Distributed Infrastructure
   - Docker.
   - CI/CD.
   - Load balancing.
   - Kubernetes deployment.
   - Load and stress testing.

## 15. Testing Requirements

| Test Type           | What to validate                  |
| ------------------- | --------------------------------- |
| Unit Testing        | Code generation, URL validation   |
| Integration Testing | API and database                  |
| Load Testing        | Concurrent redirects              |
| Stress Testing      | Maximum traffic capacity          |
| Security Testing    | Injection, abuse, SSRF            |
| Failure Testing     | Redis, database and queue outages |
| End-to-End Testing  | Complete shortening workflow      |

Suggested tools:

- Jest / Vitest
- Supertest
- k6
- Postman
- OWASP ZAP

### Initial load-testing targets

| Scenario                     | Target                       |
| ---------------------------- | ---------------------------- |
| Concurrent redirect requests | 1,000                        |
| Redirect p95 latency         | Under 100 ms                 |
| URL creation p95             | Under 300 ms                 |
| Cache hit ratio              | Above 90% for hot links      |
| Error rate                   | Under 0.1% under target load |

These are test objectives, not assumed results.

## 16. Success Metrics (KPIs)

The product will be considered successful when it achieves:

- Successful URL creation rate above 99.9%.
- Redirect availability of 99.9%.
- Redirect p95 latency below 100 ms.
- Analytics processing lag below 30 seconds under normal load.
- No duplicate short codes.
- Reliable recovery from application and infrastructure failures.
- Successful handling of expected traffic spikes.

## 17. Future Enhancements

Features that can make this project more impressive:

1. Custom branded domains.
2. QR code generation.
3. Password-protected links.
4. Geo-targeted redirection.
5. A/B testing for destination URLs.
6. Bulk URL shortening.
7. API keys and developer portal.
8. Team workspaces and collaboration.
9. AI-powered suspicious URL detection.
10. Link preview and social sharing metadata.
11. Webhooks for click events.
12. Advanced bot detection.

## 18. Critical System Design Decisions

These are particularly important when presenting this project in a backend/SDE interview.

| Design question                      | Proposed decision                               |
| ------------------------------------ | ----------------------------------------------- |
| How to generate unique codes?        | Distributed ID / random code + uniqueness check |
| How to handle high redirect traffic? | Redis + horizontal scaling                      |
| How to avoid slow analytics?         | Async event processing                          |
| How to handle duplicate aliases?     | Database unique constraint                      |
| How to avoid cache inconsistency?    | Cache invalidation and TTL                      |
| How to scale analytics?              | Kafka + partitioned analytical storage          |
| How to handle a Redis failure?       | Database fallback with circuit breakers         |
| How to prevent abuse?                | Rate limiting, URL reputation and moderation    |
| How to ensure availability?          | Multi-instance deployment and health checks     |

## 19. Final Project Scope Recommendation

I recommend building this in three levels rather than implementing every component immediately.

Level 1 – Must build

Functional production-ready core

- Node.js + Express + TypeScript
- PostgreSQL + Prisma
- Redis caching
- JWT authentication
- URL generation and redirection
- Link management
- Basic analytics
- Docker deployment

  Level 2 – Strong engineering depth

  Distributed systems
- Kafka
- Background workers
- Analytics aggregation
- Rate limiting
- Custom domains
- Load testing
- Monitoring

  Level 3 – Advanced

  Production infrastructure
- Kubernetes
- Horizontal autoscaling
- Distributed ID generation
- ClickHouse
- CDN integration
- Fault tolerance and disaster recovery

## 20. Definition of Done

The project is ready for its initial production release when:

- Users can register and authenticate.
- Users can create unique short URLs.
- Short URLs redirect correctly.
- Custom aliases work.
- Expiration and disabling work.
- Redis caching works.
- Click events are processed asynchronously.
- Analytics are visible in the dashboard.
- APIs are documented.
- Security and rate limiting are implemented.
- Docker deployment works.
- Automated tests pass.
- Load testing demonstrates the defined performance targets.
- Monitoring and backups are configured.

My recommendation: Treat this as a distributed systems/backend engineering project, not just a CRUD application.

The most technically valuable parts will be the redirect service, distributed short-code generation, caching strategy, asynchronous analytics pipeline, and handling high read traffic.

These are the areas that will give you substantial material for system design discussions and backend developer interviews.
