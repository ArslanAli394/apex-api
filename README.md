# Apex Operations API - README

## Overview

Generic Python-based REST API for the Junior DevOps Engineer Assessment. Demonstrates production-ready containerization, CI/CD, security, observability, and cloud deployment practices.

**Status:** ✅ Production Ready  
**Version:** 1.0.0  
**Language:** Python 3.11 | **Framework:** FastAPI  
**Database:** PostgreSQL 15 | **Container:** Docker  
**CI/CD:** GitHub Actions | **Cloud:** AWS-ready

---

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for local development)
- PostgreSQL 15 (or use Docker)
- Git

### 1. Clone & Setup

```bash
git clone <repository>
cd apex-api

# Copy environment file
cp .env.example .env
```

### 2. Local Development (Docker Compose)

```bash
# Start all services (API + PostgreSQL)
docker-compose up -d

# Initialize database
docker-compose exec api bash scripts/init-db.sh

# Run tests
docker-compose exec api pytest tests/ -v

# Stop services
docker-compose down
```

### 3. Access the Application

- **API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **Metrics:** http://localhost:8000/metrics
- **Health:** http://localhost:8000/health/live
- **Database:** localhost:5432 (pgAdmin at http://localhost:5050 in dev mode)

---

## API Endpoints

### Health & Monitoring

```bash
GET  /health/live        # Liveness probe (always responds if app running)
GET  /health/ready       # Readiness probe (includes DB check)
GET  /ping               # Simple health ping
GET  /metrics            # Prometheus metrics
GET  /metrics/json       # JSON metrics
```

### Items API (CRUD)

```bash
GET    /api/v1/items                    # List items (paginated)
POST   /api/v1/items                    # Create item
GET    /api/v1/items/{id}               # Get specific item
PUT    /api/v1/items/{id}               # Update item
DELETE /api/v1/items/{id}               # Delete item
GET    /api/v1/items/search/query       # Search items
POST   /api/v1/items/batch              # Batch create items
GET    /api/v1/items/stats/overview     # Get statistics
```

### Example Requests

```bash
# Create an item
curl -X POST http://localhost:8000/api/v1/items \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Sample Item",
    "description": "This is a sample item",
    "category": "demo",
    "status": "active",
    "created_by": "developer"
  }'

# List items with pagination
curl http://localhost:8000/api/v1/items?page=1&page_size=20

# Search items
curl "http://localhost:8000/api/v1/items/search/query?q=sample"

# Get health status
curl http://localhost:8000/health/live | jq
```

---

## Project Structure

```
apex-api/
├── app/                          # Application code
│   ├── main.py                  # FastAPI application entry point
│   ├── config.py                # Configuration management
│   ├── database.py              # SQLAlchemy setup
│   ├── models.py                # ORM models
│   ├── schemas.py               # Pydantic schemas
│   ├── routes/                  # API endpoints
│   │   ├── health.py            # Health checks
│   │   ├── metrics.py           # Prometheus metrics
│   │   └── items.py             # CRUD endpoints
│   ├── services/                # Business logic
│   │   └── item_service.py      # Item operations
│   ├── middleware/              # Custom middleware
│   │   └── logging.py           # Request/response logging
│   └── utils/                   # Utilities
│       └── logger.py            # Logging setup
│
├── tests/                       # Test suite
│   ├── conftest.py              # Pytest fixtures
│   ├── test_health.py           # Health check tests
│   ├── test_items.py            # API endpoint tests
│   ├── test_database.py         # Database tests
│   └── test_integration.py      # Integration tests
│
├── migrations/                  # Database schema
│   └── init.sql                 # Initial schema
│
├── scripts/                     # Operational scripts
│   ├── init-db.sh               # Database initialization
│   ├── rollback.sh              # Rollback procedure
│   ├── health-check.sh          # Health verification
│   └── cleanup.sh               # Cleanup utility
│
├── docs/                        # Documentation
│   ├── ARCHITECTURE.md          # Architecture decisions
│   ├── RUNBOOK.md               # Operational runbook
│   ├── ROLLBACK.md              # Rollback procedures
│   ├── TROUBLESHOOTING.md       # Debugging guide
│   ├── SECURITY.md              # Security practices
│   ├── COST_ANALYSIS.md         # AWS cost analysis
│   └── API.md                   # API reference
│
├── .github/workflows/           # CI/CD
│   └── ci-cd.yml                # GitHub Actions pipeline
│
├── Dockerfile                   # Multi-stage Docker build
├── docker-compose.yml           # Local development stack
├── requirements.txt             # Python dependencies
├── requirements-dev.txt         # Development dependencies
├── .env.example                 # Example environment file
├── .gitignore                   # Git ignore rules
└── README.md                    # This file
```

---

## Development

### Local Setup (Without Docker)

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt -r requirements-dev.txt

# Configure environment
cp .env.example .env
# Edit .env to point to your PostgreSQL instance

# Run application
python -m app.main

# Run tests
pytest tests/ -v --cov=app

# Code quality checks
black app/ tests/
pylint app/ --disable=all --enable=E,F
flake8 app/ tests/
bandit -r app/
```

### Environment Variables

Key configuration via `.env`:

```bash
ENVIRONMENT=development          # development, testing, production
DEBUG=true                        # Enable debug mode
DATABASE_URL=postgresql://...    # Database connection string
LOG_LEVEL=INFO                   # Logging level
API_PREFIX=/api/v1              # API prefix for routes
ENABLE_DOCS=true                # Enable Swagger/ReDoc docs
```

See `.env.example` for complete list.

---

## Docker & Containerization

### Build Image

```bash
# Build image
docker build -t apex-api:1.0.0 .

# Run container
docker run -d \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql://apex_user:password@postgres:5432/apex_db \
  --name apex-api \
  apex-api:1.0.0

# Check logs
docker logs apex-api
```

### Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down

# Remove volumes (cleans database)
docker-compose down -v

# Run with development profile (includes pgAdmin)
docker-compose --profile dev up -d
```

---

## CI/CD Pipeline

### GitHub Actions Workflow

The `.github/workflows/ci-cd.yml` implements 6+ automated checks:

1. **Lint** - Black, Pylint, Flake8
2. **Security** - Bandit, Safety, pip-audit
3. **Tests** - Pytest with coverage
4. **Build** - Docker image build with Hadolint
5. **Failure Test** - Intentional failure to demonstrate blocking
6. **Integration** - Docker Compose integration test

**Pipeline Triggers:**
- Push to `main` or `develop` branches
- Pull requests
- Manual trigger via workflow_dispatch

**Status Check:**
All 6 checks must pass for deployment approval. Any failure blocks merge.

### Running Locally

```bash
# Run linting
black --check app/ tests/
pylint app/ --disable=all --enable=E,F
flake8 app/ tests/

# Run tests with coverage
pytest tests/ -v --cov=app --cov-report=html

# Run security scans
bandit -r app/
safety check
pip-audit --desc

# Run Docker build
docker build -t apex-api:test .
```

---

## Testing

### Test Coverage

- **Unit Tests:** API endpoints, business logic, database operations
- **Integration Tests:** End-to-end workflows, Docker Compose
- **Database Tests:** Model operations, migrations

### Run Tests

```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/test_items.py -v

# With coverage report
pytest tests/ --cov=app --cov-report=html

# Watch mode (requires pytest-watch)
ptw tests/

# Run only integration tests
pytest tests/test_integration.py -v -m integration
```

### Test Database

Tests use separate test database (`apex_test_db`). Database is isolated per test via fixtures in `tests/conftest.py`.

---

## Security

### Security Practices

1. **Non-Root Container** - App runs as `apex` user (UID: not 0)
2. **Secrets Management** - Never hardcode; use environment variables
3. **Dependency Scanning** - Safety, pip-audit, Bandit in CI/CD
4. **Dockerfile Security** - Multi-stage build, minimal base image
5. **Database Security** - Non-superuser account, proper permissions
6. **Input Validation** - Pydantic schemas validate all inputs
7. **HTTPS Ready** - Use reverse proxy (Nginx/ALB) for TLS in production

### Secrets Handling

**Development:**
- Use `.env` file (never commit)
- Example: `.env.example` for reference

**Production:**
- AWS Secrets Manager for sensitive data
- IAM roles instead of access keys
- Environment variables injected at runtime
- Rotate credentials regularly

### Scanning

```bash
# Dockerfile linting
hadolint Dockerfile

# Dependency vulnerabilities
pip-audit --desc
safety check --json

# Python code security
bandit -r app/ -f json

# Container image scanning (requires docker)
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image apex-api:latest
```

---

## Monitoring & Observability

### Health Checks

```bash
# Liveness - is service running?
curl http://localhost:8000/health/live

# Readiness - can service handle traffic?
curl http://localhost:8000/health/ready

# Both include database connectivity check
```

### Metrics

Prometheus-compatible metrics at `/metrics`:

```bash
# View metrics
curl http://localhost:8000/metrics

# Key metrics:
# - apex_requests_total
# - apex_requests_errors_total
# - apex_request_duration_seconds
# - apex_db_connections_active
# - apex_db_queries_total
```

### Structured Logging

JSON logs (production) include:
- Timestamp
- Log level
- Service name
- Request ID
- Environment
- Message

View logs:
```bash
docker-compose logs api | jq .
```

### Failure Investigation

Example: Database connection failure

```bash
# Check logs
docker-compose logs postgres

# Check health
curl http://localhost:8000/health/ready

# Verify database
docker-compose exec postgres pg_isready -U apex_user

# Check connection string
docker-compose exec api env | grep DATABASE_URL
```

---

## Deployment

### Deployment Strategy

1. **Local Testing:** Docker Compose
2. **Staging:** ECS/Kubernetes on staging cluster
3. **Production:** ECS Fargate on production cluster with ALB

### Versioning

Semantic versioning: `MAJOR.MINOR.PATCH`

```bash
# Docker image tags:
- apex-api:1.0.0           # Specific version
- apex-api:1.0             # Minor version
- apex-api:latest          # Latest
- apex-api:main-abc123def  # Git SHA
```

### Rollback

```bash
# View available versions
docker images apex-api

# Execute rollback
./scripts/rollback.sh 1.0.0

# Verify
curl http://localhost:8000/
```

See `docs/ROLLBACK.md` for detailed procedures.

---

## Cloud Deployment (AWS)

### Target Architecture

```
Client
  ↓
Route 53 (DNS)
  ↓
Application Load Balancer (ALB)
  ↓
ECS Cluster (Fargate)
  ├── Task 1 (Apex API)
  ├── Task 2 (Apex API)
  └── Task 3 (Apex API)
  ↓
RDS PostgreSQL (Aurora)
  ↓
CloudWatch (Logs & Metrics)
```

### Cost Estimation

| Component | Instance | Monthly Cost |
|-----------|----------|--------------|
| ECS Fargate | 0.256vCPU, 512MB (3x) | ~$66 |
| RDS Aurora | Serverless v2 | ~$40-80 |
| ALB | Standard | ~$20 |
| CloudWatch | Logs + Metrics | ~$5 |
| Data Transfer | Within region | ~$1 |
| **Total** | | **~$130-172** |

Cost optimization strategies:
- Use spot instances for non-critical workloads
- Scale down during off-peak hours
- Use Aurora Serverless for variable load
- Implement lifecycle policies for logs

See `docs/COST_ANALYSIS.md` for detailed AWS cost breakdown.

---

## Production Checklist

- [ ] All tests passing
- [ ] Code reviewed and approved
- [ ] Security scan passed (no critical vulnerabilities)
- [ ] Docker image built and scanned
- [ ] Environment variables configured
- [ ] Database migrations tested
- [ ] Health checks verified
- [ ] Monitoring/logging enabled
- [ ] Rollback procedure tested
- [ ] Documentation updated
- [ ] Secrets stored securely (no hardcoded values)

---

## Troubleshooting

### Common Issues

**1. Database Connection Failed**
```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Verify connection string
echo $DATABASE_URL

# Test connection
psql $DATABASE_URL -c "SELECT 1"
```

**2. Port Already in Use**
```bash
# Find process using port 8000
lsof -i :8000

# Change port in .env
PORT=8001
```

**3. Container Won't Start**
```bash
# Check logs
docker-compose logs api

# Rebuild image
docker-compose build --no-cache api
```

See `docs/TROUBLESHOOTING.md` for more solutions.

---

## Contributing

1. Create feature branch: `git checkout -b feature/my-feature`
2. Make changes and commit: `git commit -am 'Add feature'`
3. Push to branch: `git push origin feature/my-feature`
4. Create pull request
5. Ensure all CI checks pass
6. Get code review approval
7. Merge to main

---

## License

This project is part of the Apex DevOps Assessment. All code is provided for educational purposes.

---

## Support

For issues or questions:
1. Check `docs/TROUBLESHOOTING.md`
2. Review GitHub Issues
3. Check application logs: `docker-compose logs api`
4. Contact DevOps team

---

**Last Updated:** 2026-10-29  
**Version:** 1.0.0  
**Maintained By:** DevOps Assessment Team
