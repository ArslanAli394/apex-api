# Operational Runbook

## Quick Reference

| Task | Command |
|------|---------|
| Start Application | `docker-compose up -d` |
| Stop Application | `docker-compose down` |
| View Logs | `docker-compose logs -f api` |
| Run Tests | `docker-compose exec api pytest tests/ -v` |
| Rollback | `./scripts/rollback.sh <version>` |
| Health Check | `./scripts/health-check.sh` |
| Database Init | `docker-compose exec api bash scripts/init-db.sh` |

---

## 1. Deployment Procedures

### Initial Deployment

```bash
# Step 1: Clone repository
git clone <repo-url>
cd apex-api

# Step 2: Copy environment file
cp .env.example .env
# Edit .env with your configuration

# Step 3: Build and start services
docker-compose build
docker-compose up -d

# Step 4: Verify deployment
docker-compose ps
curl http://localhost:8000/health/live

# Step 5: Seed initial data
docker-compose exec api bash scripts/init-db.sh

# Step 6: Run tests
docker-compose exec api pytest tests/ -v --cov=app
```

### Expected Output

```bash
$ docker-compose up -d
Creating apex-postgres ... done
Creating apex-api ... done

$ curl http://localhost:8000/health/live
{
  "status": "healthy",
  "timestamp": "2026-10-29T19:09:15Z",
  "version": "1.0.0",
  "checks": {"service": "running"}
}

$ docker-compose ps
NAME                COMMAND                  STATUS
apex-postgres       "docker-entrypoint..."   Up (healthy)
apex-api           "uvicorn app.main:..."   Up (healthy)
```

### Deploy to New Environment

```bash
# Step 1: Setup infrastructure (AWS example)
aws ecs create-cluster --cluster-name apex-prod

# Step 2: Create task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json

# Step 3: Create service
aws ecs create-service \
  --cluster apex-prod \
  --service-name apex-api \
  --task-definition apex-api:1 \
  --desired-count 3

# Step 4: Verify deployment
aws ecs describe-services \
  --cluster apex-prod \
  --services apex-api
```

---

## 2. Rollback Procedures

### Quick Rollback

```bash
# Rollback to previous version
./scripts/rollback.sh 1.0.0

# Example output:
# ✅ Rollback successful
#    Running version: 1.0.0
```

### Manual Rollback

```bash
# Step 1: Stop current version
docker-compose down

# Step 2: Update docker-compose.yml
# Change image tag from 1.0.1 to 1.0.0
nano docker-compose.yml

# Step 3: Start previous version
docker-compose up -d

# Step 4: Verify
curl http://localhost:8000/health/ready

# Step 5: Verify data integrity
docker-compose exec api curl http://localhost:8000/api/v1/items/stats/overview
```

### AWS Rollback

```bash
# Step 1: Get current task definition
CURRENT_REVISION=$(aws ecs describe-services \
  --cluster apex-prod \
  --services apex-api \
  | jq '.services[0].taskDefinition')

# Step 2: Get previous revision
PREVIOUS_REVISION=$(expr $CURRENT_REVISION - 1)

# Step 3: Update service to previous version
aws ecs update-service \
  --cluster apex-prod \
  --service apex-api \
  --task-definition apex-api:$PREVIOUS_REVISION \
  --force-new-deployment

# Step 4: Wait for deployment
aws ecs wait services-stable \
  --cluster apex-prod \
  --services apex-api

# Step 5: Verify
aws ecs describe-services \
  --cluster apex-prod \
  --services apex-api | jq '.services[0].runningCount'
```

---

## 3. Incident Response

### Database Connection Failure

**Symptoms:**
- API returns 503 on `/health/ready`
- Error: `could not connect to database`

**Investigation:**
```bash
# Check database status
docker-compose ps postgres

# Check database logs
docker-compose logs postgres | tail -50

# Test connection manually
docker-compose exec postgres \
  psql -U apex_user -d apex_db -c "SELECT 1"

# Check connection string
docker-compose exec api env | grep DATABASE_URL
```

**Resolution:**
```bash
# Restart database
docker-compose restart postgres

# Wait for recovery
sleep 10

# Verify
curl http://localhost:8000/health/ready

# If still failing, reinitialize
docker-compose down -v
docker-compose up -d
docker-compose exec api bash scripts/init-db.sh
```

### High Error Rate (>5% failures)

**Symptoms:**
- Metrics show increased `apex_requests_errors_total`
- Logs contain stack traces

**Investigation:**
```bash
# Get error rate
curl http://localhost:8000/metrics/json | jq '.requests_error, .requests_total'

# Check recent logs
docker-compose logs api --tail 100 | grep ERROR

# Check resource usage
docker-compose stats apex-api

# Check database performance
docker-compose exec postgres \
  psql -U apex_user -d apex_db -c "SELECT count(*) FROM pg_stat_statements WHERE query LIKE '%SELECT%';"
```

**Resolution Options:**

Option 1: Scale up
```bash
# Increase memory limit
docker-compose down
# Edit docker-compose.yml: deploy.resources.limits.memory
docker-compose up -d
```

Option 2: Optimize queries
```bash
# Analyze slow queries
docker-compose exec api pytest tests/ -v

# Check database indexes
docker-compose exec postgres \
  psql -U apex_user -d apex_db -c "\d+ items"
```

Option 3: Temporary traffic reduction
```bash
# Reduce desired count temporarily
aws ecs update-service \
  --cluster apex-prod \
  --service apex-api \
  --desired-count 1
```

### Memory Leak

**Symptoms:**
- Container memory usage constantly increasing
- Eventually killed by OOM

**Investigation:**
```bash
# Monitor memory over time
watch -n 2 'docker-compose stats apex-api --no-stream'

# Check for unclosed connections
docker-compose exec api python -c "import gc; gc.get_count()"

# Check database connections
docker-compose exec postgres \
  psql -U apex_user -d apex_db -c "SELECT count(*) FROM pg_stat_activity;"
```

**Resolution:**
```bash
# Restart container (temporary)
docker-compose restart api

# Permanent fix: update code, redeploy
git pull
docker-compose build --no-cache api
docker-compose up -d api
```

### Slow Requests

**Symptoms:**
- P95/P99 latency high (>1000ms)
- Metrics show high `apex_request_duration_seconds`

**Investigation:**
```bash
# Check slow endpoints in logs
docker-compose logs api | grep "duration_ms" | sort -t= -k4 -rn | head -10

# Analyze database queries
docker-compose exec postgres \
  psql -U apex_user -d apex_db -c "SELECT query, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 5;"

# Check connection pool
docker-compose exec api curl http://localhost:8000/metrics/json | jq '.db_connection_active'
```

**Resolution:**
```bash
# Add index for slow query
docker-compose exec postgres \
  psql -U apex_user -d apex_db -c "CREATE INDEX idx_items_status_created ON items(status, created_at DESC);"

# Increase connection pool
# Edit .env: DB_POOL_SIZE=20
docker-compose restart api

# Cache frequently accessed data (future enhancement)
```

---

## 4. Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs api

# Common issues:
# 1. Port already in use
netstat -tlnp | grep 8000

# Solution: Change PORT in .env

# 2. Database not ready
docker-compose logs postgres

# Solution: Restart postgres
docker-compose restart postgres

# 3. Image build failed
docker-compose build --no-cache api
```

### Tests Failing

```bash
# Run tests with verbose output
docker-compose exec api pytest tests/ -vv

# Run specific test
docker-compose exec api pytest tests/test_items.py::TestItemEndpoints::test_create_item -vv

# Run with debugging
docker-compose exec api pytest tests/ -vv --pdb

# Check database state
docker-compose exec postgres \
  psql -U apex_user -d apex_test_db -c "SELECT count(*) FROM items;"
```

### Health Check Failing

```bash
# Check liveness
curl -v http://localhost:8000/health/live

# Check readiness
curl -v http://localhost:8000/health/ready

# Check database connectivity from container
docker-compose exec api \
  python -c "from app.database import check_db_connection; import asyncio; print(asyncio.run(check_db_connection()))"

# Manually verify database
docker-compose exec postgres \
  pg_isready -U apex_user -d apex_db
```

### API Endpoints Not Responding

```bash
# Test connectivity
curl -v http://localhost:8000/api/v1/items

# Check if API is running
docker-compose ps api

# Check API logs
docker-compose logs api --tail 50

# Restart API
docker-compose restart api

# Full reset if needed
docker-compose down -v
docker-compose up -d
```

---

## 5. Monitoring Tasks

### Daily Health Check

```bash
# Run automated health check
./scripts/health-check.sh

# Expected output:
# ✅ All health checks passed!
```

### Weekly Database Maintenance

```bash
# Analyze table
docker-compose exec postgres \
  psql -U apex_user -d apex_db -c "ANALYZE items;"

# Reindex if needed
docker-compose exec postgres \
  psql -U apex_user -d apex_db -c "REINDEX TABLE items;"

# Vacuum to reclaim space
docker-compose exec postgres \
  psql -U apex_user -d apex_db -c "VACUUM ANALYZE items;"
```

### Monthly Performance Review

```bash
# Get metrics
curl http://localhost:8000/metrics/json | jq '.[]'

# Analyze slow queries
docker-compose exec postgres \
  psql -U apex_user -d apex_db -c "SELECT * FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"

# Check error rate trend
docker-compose logs api --since 30d | grep ERROR | wc -l
```

### Monthly Backup Verification

```bash
# Create backup
docker-compose exec postgres \
  pg_dump -U apex_user apex_db | gzip > backup_$(date +%Y%m%d).sql.gz

# Verify backup
gunzip -t backup_$(date +%Y%m%d).sql.gz

# Test restore (to separate database)
docker-compose exec postgres \
  createdb -U apex_user apex_db_test
gunzip < backup_$(date +%Y%m%d).sql.gz | \
  docker-compose exec -T postgres \
    psql -U apex_user -d apex_db_test
```

---

## 6. Maintenance Windows

### Planned Maintenance

```bash
# 1. Announce maintenance
# Send notification: "Maintenance window: 02:00-03:00 UTC"

# 2. Drain connections
docker-compose exec api curl -X POST http://localhost:8000/drain

# 3. Stop services
docker-compose down

# 4. Perform maintenance (DB updates, patches, etc.)
# Example: Database migration
docker-compose up -d postgres
docker-compose exec postgres psql -U apex_user -d apex_db < migration.sql

# 5. Start services
docker-compose up -d

# 6. Verify
./scripts/health-check.sh

# 7. Announce completion
# Send notification: "Maintenance complete"
```

### Emergency Maintenance

```bash
# If system is critical (not recommended, but for emergencies):

# Step 1: Kill all connections gracefully
docker-compose exec postgres \
  psql -U apex_user -d apex_db -c \
  "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'apex_db' AND pid != pg_backend_pid();"

# Step 2: Perform maintenance
docker-compose down

# Step 3: Fix issue
# ... (make changes)

# Step 4: Restart
docker-compose up -d
```

---

## 7. Contacts & Escalation

| Issue | Contact | Response Time |
|-------|---------|----------------|
| App Failure | DevOps On-Call | 15 minutes |
| Database Failure | DBA Team | 10 minutes |
| Security Incident | Security Team | 5 minutes |
| Performance Degradation | Performance Team | 30 minutes |
| General Questions | DevOps Slack #apex-api | Next business day |

**Escalation Path:**
1. Try standard troubleshooting
2. Contact on-call engineer
3. Page team lead if no response in 15 min
4. Page director if still unresolved in 30 min

---

## 8. Key Metrics & Thresholds

| Metric | Warning | Critical |
|--------|---------|----------|
| API Response Time (p95) | >500ms | >2000ms |
| Error Rate | >1% | >5% |
| Database Connections | >80% pool | >95% pool |
| CPU Usage | >70% | >90% |
| Memory Usage | >70% | >85% |
| Disk Usage | >80% | >90% |

---

**Runbook Version:** 1.0.0  
**Last Updated:** 2026-10-29  
**Next Review:** 2026-11-29
