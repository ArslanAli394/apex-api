# Security Documentation

## Security Overview

This document outlines security practices, policies, and procedures for the Apex Operations API.

---

## 1. Secrets Management

### Development Environment

**File-Based Secrets:**
```bash
# .env file (NEVER commit to git)
DATABASE_PASSWORD=dev_password_123
API_KEY=dev_key_456
```

**.gitignore Protection:**
```
.env
.env.local
.env.*.local
*.key
*.pem
secrets/
```

**Verification:**
```bash
# Check for secrets in git history
git log -p -- '*.env' | head -20

# Check for exposed secrets
truffleHog scan --regex --entropy=False .
```

### Production Environment (AWS)

**AWS Secrets Manager:**
```bash
# Store secret
aws secretsmanager create-secret \
  --name apex/prod/db-password \
  --secret-string "$(openssl rand -base64 32)"

# Retrieve secret
aws secretsmanager get-secret-value \
  --secret-id apex/prod/db-password \
  --query SecretString --output text

# Rotate secret (automatic)
aws secretsmanager rotate-secret \
  --secret-id apex/prod/db-password \
  --rotation-rules AutomaticallyAfterDays=30
```

**IAM Role-Based Access:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "secretsmanager:GetSecretValue",
      "Resource": "arn:aws:secretsmanager:us-east-1:123456789:secret:apex/*"
    },
    {
      "Effect": "Allow",
      "Action": "kms:Decrypt",
      "Resource": "arn:aws:kms:us-east-1:123456789:key/*"
    }
  ]
}
```

**Injection at Runtime:**
```bash
# No secrets in environment variables or code
# IAM role provides temporary credentials
# Application assumes role automatically
```

### Secret Rotation Schedule

| Secret | Rotation Frequency | Last Rotated | Next Rotation |
|--------|-------------------|--------------|---------------|
| DB Password | 90 days | 2026-10-01 | 2026-12-29 |
| API Keys | 60 days | 2026-09-01 | 2026-10-31 |
| TLS Certificates | 30 days | 2026-10-15 | 2026-11-14 |

---

## 2. Least Privilege Access

### Container User

**Non-Root Execution:**
```dockerfile
# Create dedicated user
RUN groupadd -r apex && useradd -r -g apex apex

# Switch to non-root
USER apex

# Verify (UID should not be 0)
docker run apex-api:1.0.0 id
# uid=1000(apex) gid=1000(apex) groups=1000(apex)
```

**Benefits:**
- Prevents privilege escalation
- Limits damage if container compromised
- Container security best practice
- Required for Kubernetes Pod Security Policies

### Database User

**Restricted Permissions:**
```sql
-- Create non-superuser account
CREATE ROLE apex_user WITH LOGIN PASSWORD 'secure_password';

-- Grant specific privileges only
GRANT CONNECT ON DATABASE apex_db TO apex_user;
GRANT USAGE ON SCHEMA public TO apex_user;

-- Only SELECT, INSERT, UPDATE, DELETE (not CREATE, DROP)
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO apex_user;

-- Grant sequence permissions for auto-increment
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO apex_user;

-- Restrict function execution
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO apex_user;

-- Verify permissions
\du apex_user
\dp public.items
```

**Verification:**
```sql
-- User cannot drop table
apex_user=> DROP TABLE items;
ERROR: permission denied for schema public

-- User cannot create superuser
apex_user=> ALTER ROLE test WITH SUPERUSER;
ERROR: permission denied to alter role
```

### IAM Roles (AWS)

**ECS Task Role:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue",
        "kms:Decrypt"
      ],
      "Resource": [
        "arn:aws:secretsmanager:*:*:secret:apex/*",
        "arn:aws:kms:*:*:key/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:PutLogEvents",
        "logs:CreateLogStream"
      ],
      "Resource": "arn:aws:logs:*:*:log-group:/ecs/apex-api/*"
    }
  ]
}
```

---

## 3. Input Validation & Sanitization

### Pydantic Validation

**Schema-Level Validation:**
```python
class ItemCreate(BaseModel):
    # Length constraints
    name: str = Field(..., min_length=1, max_length=255)
    
    # Pattern matching (enum-like)
    status: str = Field(
        default="active",
        pattern="^(active|inactive|archived)$"
    )
    
    # Email validation
    created_by: EmailStr = Field(...)
    
    # Numeric constraints
    priority: int = Field(..., ge=1, le=10)
```

**SQL Injection Prevention:**
```python
# VULNERABLE (string interpolation)
query = f"SELECT * FROM items WHERE name = '{user_input}'"

# SAFE (parameterized query via SQLAlchemy)
items = db.query(Item).filter(Item.name == user_input).all()
```

**XSS Prevention:**
```python
# Store safely (will be escaped on output)
item.description = "<script>alert('xss')</script>"  # Stored as-is

# When returning to client, use:
ItemSchema(...).model_dump_json()  # Properly escaped
```

### Rate Limiting (Future)

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.get("/api/v1/items")
@limiter.limit("100/minute")
async def list_items():
    ...
```

---

## 4. Dependency Management

### Vulnerability Scanning

**Automated Checks (in CI/CD):**

```bash
# Safety check
safety check --json > safety-report.json

# pip-audit
pip-audit --desc --format json > pip-audit-report.json

# Bandit (code security)
bandit -r app/ -f json -o bandit-report.json
```

**Policy:**
- Fail CI/CD if critical vulnerabilities found
- Review and patch within 24 hours for high severity
- Weekly dependency updates

**Dependency Pinning:**
```
# requirements.txt (pinned versions)
fastapi==0.104.1
sqlalchemy==2.0.23
psycopg2-binary==2.9.9

# NOT version ranges
fastapi>=0.100.0  # ❌ Avoid - could pull malicious versions
sqlalchemy^2.0    # ❌ Avoid - too loose
```

### Supply Chain Security

**Checksum Verification:**
```bash
# Verify package integrity
pip install --require-hashes -r requirements.txt

# Generate hashes
pip freeze --all-hashes > requirements-hashes.txt
```

**Source Verification:**
```bash
# Use official PyPI only
pip install --index-url https://pypi.org/simple/ fastapi

# NOT unofficial mirrors
```

---

## 5. Container Security

### Image Scanning

**Trivy (Vulnerability Scanner):**
```bash
# Scan image
trivy image apex-api:1.0.0

# Output:
# HIGH: CVE-2026-1234 in openssl/1.1.1
# MEDIUM: CVE-2026-5678 in curl/7.68

# Scan with severity threshold
trivy image --severity HIGH,CRITICAL apex-api:1.0.0
```

**Dockerfile Linting (Hadolint):**
```bash
hadolint Dockerfile

# Output:
# DL3008: Pin versions in apt get install
# DL3009: Delete apt cache
```

### Image Hardening

**Minimal Base Image:**
```dockerfile
# ❌ Large base image (1.3GB)
FROM python:3.11

# ✅ Slim base image (200MB)
FROM python:3.11-slim

# ✅ Alpine base image (100MB)
FROM python:3.11-alpine
```

**Remove Unnecessary Tools:**
```dockerfile
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*  # Remove cache
```

**Read-Only Filesystem (K8s):**
```yaml
securityContext:
  readOnlyRootFilesystem: true
  runAsNonRoot: true
  runAsUser: 1000
```

---

## 6. Network Security

### Container Networking

**Docker Compose Isolation:**
```yaml
services:
  api:
    networks:
      - apex-network
  postgres:
    networks:
      - apex-network

networks:
  apex-network:
    driver: bridge
```

**Benefits:**
- Services communicate via network name, not IP
- External network isolated by default
- Services not exposed unless explicitly bound

### TLS/HTTPS

**Development:**
```bash
# Self-signed certificate (for testing)
openssl req -x509 -newkey rsa:4096 -nodes \
  -out cert.pem -keyout key.pem -days 365
```

**Production (AWS):**
```bash
# Use AWS Certificate Manager (free)
aws acm request-certificate \
  --domain-name api.apex.com \
  --validation-method DNS

# ALB terminates TLS, communication to ECS internal (HTTP)
```

**API Security Headers:**
```python
# Add to FastAPI middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response
```

---

## 7. API Security

### Authentication & Authorization

**JWT Tokens (Future Enhancement):**
```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthCredentials

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthCredentials = Depends(security)):
    token = credentials.credentials
    # Verify JWT signature
    # Check expiration
    # Return user info
```

**Current (Assessment):**
- No authentication (public API for assessment)
- Future: Add JWT or API key authentication

### CORS Configuration

**Restricted CORS (Production):**
```python
# ❌ Insecure (allow all)
CORSMiddleware(allow_origins=["*"])

# ✅ Secure (whitelist specific origins)
CORSMiddleware(
    allow_origins=[
        "https://app.apex.com",
        "https://dashboard.apex.com"
    ],
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
    allow_credentials=True,
    max_age=3600
)
```

---

## 8. Compliance & Audit

### Logging for Audit Trail

**What to Log:**
```json
{
  "timestamp": "2026-10-29T19:09:34Z",
  "action": "create_item",
  "user": "service-account",
  "resource": "items",
  "resource_id": 123,
  "status": "success",
  "changes": {
    "name": "New Item",
    "status": "active"
  }
}
```

**Immutable Logs:**
```bash
# Send logs to CloudWatch Logs (immutable)
# Enable CloudTrail for AWS API calls
# Archive logs to S3 for compliance
```

### Data Retention Policy

| Data Type | Retention | Storage |
|-----------|-----------|---------|
| Application Logs | 30 days | CloudWatch |
| Audit Logs | 1 year | S3 Glacier |
| Database Backups | 30 days rolling | AWS Backup |
| Sensitive Data | Encrypted | KMS |

---

## 9. Incident Response

### Security Incident Classification

| Severity | Impact | Response Time | Examples |
|----------|--------|----------------|----------|
| Critical | Full compromise | <5 minutes | RCE, data breach |
| High | Significant impact | <30 minutes | SQL injection, auth bypass |
| Medium | Limited impact | <4 hours | XSS, CSRF |
| Low | Minimal impact | <24 hours | Information disclosure |

### Incident Response Procedure

```bash
# 1. Detect & Alert
# Monitoring alerts on suspicious activity

# 2. Contain
docker-compose down               # Stop service
aws s3 sync ... backup/           # Backup data
git log --oneline | head -20      # Preserve logs

# 3. Investigate
docker-compose logs api > incident-logs.txt
grep ERROR incident-logs.txt
grep malicious app/main.py

# 4. Eradicate
# Remove malicious code
# Patch vulnerability
# Rebuild image

# 5. Recover
docker-compose build --no-cache api
docker-compose up -d
./scripts/health-check.sh

# 6. Post-Mortem
# Document root cause
# Create prevention procedures
# Update security controls
```

---

## 10. Security Checklist

### Pre-Deployment

- [ ] No hardcoded secrets in code
- [ ] All dependencies scanned for vulnerabilities
- [ ] Dockerfile security scan passed (Hadolint)
- [ ] Container image scanned (Trivy)
- [ ] Non-root user in Dockerfile
- [ ] Environment variables used for configuration
- [ ] TLS/HTTPS configured
- [ ] Security headers implemented
- [ ] Input validation on all endpoints
- [ ] Error messages don't leak sensitive info
- [ ] Logs don't contain secrets
- [ ] Database user has minimal privileges
- [ ] Backup strategy in place

### Post-Deployment

- [ ] Monitoring alerts configured
- [ ] Log aggregation enabled
- [ ] Audit logging working
- [ ] WAF rules configured (if using)
- [ ] DDoS protection enabled (if on AWS)
- [ ] Security scanning running on schedule
- [ ] Incident response team briefed
- [ ] Runbook reviewed and accessible

---

## 11. Security Updates

### Patching Policy

**Frequency:**
- Critical: Within 24 hours
- High: Within 1 week
- Medium: Within 2 weeks
- Low: Within 1 month

**Process:**
```bash
# 1. Test patch in dev
pip install --upgrade <package>

# 2. Run tests
pytest tests/ -v

# 3. Deploy to staging
docker-compose -f docker-compose.staging.yml up -d

# 4. Verify
./scripts/health-check.sh

# 5. Deploy to production
git commit -m "Security update: <package> <version>"
git push

# GitHub Actions automatically:
# - Runs tests
# - Scans image
# - Deploys if passed
```

---

## 12. Security Training

**Team Members Should Know:**
- Never commit secrets to git
- Always use parameterized queries
- Validate and sanitize user input
- Rotate credentials regularly
- Report security issues immediately
- Follow principle of least privilege

**Resources:**
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CWE/SANS Top 25](https://cwe.mitre.org/top25/)
- [AWS Security Best Practices](https://aws.amazon.com/security/best-practices/)

---

**Security Document Version:** 1.0.0  
**Last Reviewed:** 2026-10-29  
**Next Review:** 2026-11-29
