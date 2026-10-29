# AWS Cloud Cost Analysis & Strategy

## Executive Summary

This document provides a comprehensive cost analysis for deploying the Apex Operations API on AWS, with strategies to optimize spending and inform stakeholder decisions.

---

## 1. Cost Model Overview

### Three-Tier Pricing Strategy

| Environment | Use Case | Target Cost | Year 1 |
|-------------|----------|------------|--------|
| **Development** | Development & Testing | ~$0-50/month | $0 (Free Tier) |
| **Staging** | Pre-production validation | ~$50-100/month | $600-1,200 |
| **Production** | Live service | ~$200-500/month | $2,400-6,000 |

**Total Year 1 Estimated:** $3,000-7,200 (with free tier benefits)

---

## 2. Component-Level Cost Breakdown

### 2.1 Compute: AWS ECS Fargate

**What It Is:**
- Serverless container orchestration
- Pay per vCPU-second + memory-second
- No server management required
- Auto-scaling based on load

**Pricing Structure:**

| vCPU | Memory | Hourly Cost | Monthly (24/7) | 30% Utilization |
|------|--------|------------|-----------------|-----------------|
| 0.256 | 512 MB | $0.011 | $8 | $2.50 |
| 0.5 | 1 GB | $0.022 | $16 | $5 |
| 1 | 2 GB | $0.044 | $32 | $10 |
| 2 | 4 GB | $0.088 | $64 | $19 |

**Deployment Example (Small Production):**

```
Desired Count: 3 tasks (high availability)
Task Size: 0.256 vCPU + 512 MB RAM

Per Task: 0.256 vCPU-hours × $0.0000343/vCPU-second × 730 hours
         + 512 MB-hours × $0.00000476/MB-second × 730 hours
         = $7.25 + $0.90 = $8.15/month

Total: 3 × $8.15 = $24.45/month
Plus data transfer: ~$1-2/month
**ECS Fargate Total: ~$26/month**
```

**Cost Optimization:**

```
Scenario A: Full 24/7 Production
- 3 tasks × $8.15 = $24.45/month

Scenario B: Scale down off-peak (50% savings)
- Business hours (10h/day): 3 tasks = $24.45
- Off-peak (14h/day): 1 task = $8.15
- Average: (10 × 3 + 14 × 1) / 24 = $14.54/month → 40% savings

Scenario C: Spot Instances (70% discount)
- 3 tasks × $8.15 × 0.30 = $7.34/month
- Risk: Can be interrupted, but good for non-critical workloads
```

### 2.2 Database: AWS RDS Aurora

**Option A: Aurora PostgreSQL Serverless v2** (RECOMMENDED)

```
Pricing Model:
- $0.06 per ACU-hour (Aurora Capacity Unit)
- Minimum: 0.5 ACU when idle
- Scales automatically: 0.5 to 16+ ACUs

Cost Calculation:
- 2 ACUs average during business hours = 2 × $0.06 × 730 = $87.60/month
- Idle off-peak: 0.5 × $0.06 × 730 = $21.90/month
- Average: (10 × 2 + 14 × 0.5) / 24 = 1.29 ACUs = $56.50/month

Storage:
- ~10GB data = 10 × $0.10/GB = $1/month
- Backups (7 days retention) = ~$2/month

**Aurora Serverless v2 Total: ~$60/month**
```

**Option B: RDS PostgreSQL (Traditional)**

```
db.t3.micro (Free Tier Year 1):
- Free tier: 750 hours/month
- After free tier: $0.018/hour = $13/month

db.t3.small:
- $0.032/hour = $23/month

Storage:
- 20GB SSD = $2/month
- Backup storage = $2/month

Snapshots & Restores = $0.021 per GB = ~$1/month

**RDS PostgreSQL Traditional: ~$28-40/month**
```

**Recommendation:**
- **Year 1:** Use db.t3.micro (Free Tier)
- **Year 2+:** Upgrade to Aurora Serverless v2 for auto-scaling

### 2.3 Load Balancing: Application Load Balancer (ALB)

**Pricing:**

```
ALB Costs:
- ALB hourly charge: $0.0243/hour = $17.73/month (24/7)
- LCU (Load Capacity Units): $0.006/LCU-hour

Calculation for Small Production:
- ALB base: $17.73/month
- 50 new connections/second: ~1 LCU
- 1 LCU × 730 hours × $0.006 = $4.38/month

**ALB Total: ~$22/month**
```

**Cost Optimization:**

```
Option A: Classic Load Balancer (Legacy, cheaper)
- $0.0243/hour = $17.73/month
- BUT: Limited features, being phased out

Option B: Network Load Balancer (Higher performance)
- $0.006/hour = $4.38/month (base)
- Similar LCU pricing

Option C: No ALB (for single region, single AZ dev)
- Save $22/month but lose high availability
- NOT recommended for production
```

### 2.4 Storage: Amazon S3 (for backups/logs)

```
Pricing Model:
- Storage: $0.023 per GB/month
- Requests: $0.0004 per GET, $0.005 per PUT
- Data transfer: $0.02/GB (out), free (in)

Example Workload:
- Application logs: 1GB/month = $0.023
- Database backups: 5GB monthly = $0.115
- Total storage: 6GB = $0.138/month

Cost: ~$1-2/month for small workload
```

### 2.5 Networking & Data Transfer

**Data Transfer Costs:**

```
Outbound Data Transfer Pricing:
- First 1GB/month: FREE
- Next 9.999TB: $0.02/GB
- Bulk discounts available

Example Workload:
- 1000 users × 100KB responses/day × 30 days = 3GB
- 3GB exceeds 1GB free tier = 2GB × $0.02 = $0.04/month

Cost: ~$0-5/month (minimal for typical API usage)
```

**NAT Gateway (for private subnets):**

```
NAT Gateway Pricing:
- $0.045/hour = $32.85/month
- $0.045/GB processed
- Only needed if using private subnets

For Assessment: NOT required (use public subnets)
```

### 2.6 Monitoring: AWS CloudWatch

**Pricing Structure:**

```
CloudWatch Logs:
- Log ingestion: First 5GB free, then $0.50/GB
- Log storage: $0.03/GB/month
- Typical API: 100MB logs/day = 3GB/month

Example:
- Ingestion: 3GB × $0.50 = $1.50 (after free tier)
- Storage: 90GB (30 days) × $0.03 = $2.70
- Total: ~$4/month

Custom Metrics:
- First 10 free, then $0.10/metric/month
- Dashboards: First 3 free, then $3/dashboard

Cost: ~$5-10/month
```

### 2.7 DNS: Route 53

**Pricing:**

```
Hosted Zone: $0.50/month
Queries: $0.40 per million queries
- 1000 queries/second = 2.59 billion queries/month
- Cost: 2.59 × $0.40 = $1.04/month

Total: ~$1.50/month
```

---

## 3. Total Cost Estimation

### Scenario A: Small Production (Recommended for Assessment)

**Architecture:**
- 3 × ECS Fargate tasks (0.256 vCPU, 512MB)
- RDS Aurora Serverless v2 (2 ACUs average)
- Application Load Balancer
- CloudWatch monitoring

**Monthly Breakdown:**

| Component | Cost |
|-----------|------|
| ECS Fargate (3×) | $26 |
| RDS Aurora | $60 |
| ALB | $22 |
| CloudWatch | $5 |
| S3 Backups | $2 |
| Route 53 | $1.50 |
| Data Transfer | $2 |
| **Monthly Total** | **~$118.50** |
| **Annual Total** | **~$1,422** |

### Scenario B: High Availability Production

**Architecture:**
- 6 × ECS Fargate tasks (0.5 vCPU, 1GB) - 2 per AZ
- RDS Aurora Multi-AZ (4 ACUs average)
- ALB with cross-AZ
- Enhanced monitoring & logging

**Monthly Breakdown:**

| Component | Cost |
|-----------|------|
| ECS Fargate (6×) | $84 |
| RDS Aurora Multi-AZ | $120 |
| ALB | $30 |
| NAT Gateway (2×) | $66 |
| CloudWatch | $15 |
| S3 Backups | $5 |
| Route 53 | $2 |
| Data Transfer | $10 |
| **Monthly Total** | **~$332** |
| **Annual Total** | **~$3,984** |

### Scenario C: Development/Testing (Free Tier)

**Architecture:**
- Single ECS task (0.256 vCPU, 512MB)
- RDS db.t3.micro (Free Tier)
- No ALB (direct port exposure)
- Basic monitoring

**Monthly Cost:**
- Year 1: **$0** (all within free tier)
- Year 2+: ~$35/month (after free tier expires)

---

## 4. Cost Optimization Strategies

### Strategy 1: Auto-Scaling Based on Time

```
Definition:
- Scale up during business hours
- Scale down during off-peak/weekends
- Estimated savings: 30-50%

Implementation:
- Set scaling policy: 
  - 08:00-18:00 UTC: 3 tasks
  - 18:00-08:00 UTC: 1 task
- Estimated monthly savings: $3-5/month
```

### Strategy 2: Spot Instances

```
Definition:
- Use AWS Spot Instances (70% discount)
- For non-critical workloads
- Can be interrupted with 2-minute notice

Implementation:
- Fargate Spot: 3 × $8.15 × 0.30 = $7.34/month
- Run critical traffic on on-demand
- Run batch jobs on spot

Risk Assessment:
- Low risk: Stateless API with auto-recovery
- Mitigation: Health checks + auto-restart
- Savings: ~$18/month
```

### Strategy 3: Reserved Instances (Commitment Discount)

```
Definition:
- Pre-commit to compute for 1-3 years
- Get 40-70% discount
- Trade flexibility for savings

Example (1-year commitment):
- RDS: $60 × 12 × 0.40 = $288/year savings
- ECS: $26 × 12 × 0.30 = $93.60/year savings
- Total: ~$380/year = $31/month savings

Trade-off:
- Locked in for 1 year
- Good if traffic predictable
```

### Strategy 4: Caching Layer (Redis)

```
AWS ElastiCache (Redis):
- Cache frequent queries
- Reduce database load
- Small cache cluster: $0.017/hour = $12.40/month

ROI:
- Reduces RDS ACUs: -1 ACU = -$44/month
- Net savings: $44 - $12 = $32/month
- Payback period: <1 month

Implementation Priority: Medium (Phase 2)
```

### Strategy 5: Multi-Region Disaster Recovery

```
Current (Single Region):
- ~$120/month
- RTO (Recovery Time Objective): Manual failover (1-2 hours)
- RPO (Recovery Point Objective): 15 minutes (automated backups)

With Multi-Region:
- Primary: $120
- Secondary (read-only): $120
- Total: $240/month
- RTO: <5 minutes (automatic failover)
- RPO: <1 minute (continuous replication)

When to implement: Post-production stability
```

---

## 5. Cost Comparison: On-Premises vs. AWS vs. GCP vs. Azure

| Factor | On-Prem | AWS | GCP | Azure |
|--------|---------|-----|-----|-------|
| **Compute** | $300/month | $26 | $20 | $22 |
| **Database** | $200/month | $60 | $50 | $65 |
| **Storage/Backup** | $100/month | $2 | $1.50 | $2 |
| **Networking** | $150/month | $22 | $18 | $20 |
| **Monitoring** | $50/month | $5 | $5 | $5 |
| **Operations Staff** | $8,000/month | $0 | $0 | $0 |
| **Rent/Facilities** | $2,000/month | $0 | $0 | $0 |
| **Total/Month** | **~$10,800** | **~$115** | **~$95** | **~$115** |
| **Year 1 Savings** | Baseline | **94%** | **95%** | **94%** |

**Recommendation:** AWS chosen for:
- Free tier benefits
- Largest market share → most documentation
- Deep integration with GitHub Actions
- Superior cost management tools

---

## 6. Stakeholder Communication Template

### Executive Summary Slide

```
APEX OPERATIONS API - CLOUD COST STRATEGY

Current State (On-Premises):
- Estimated monthly: $10,800
- Annual cost: $129,600

Proposed (AWS):
- Small Production: $120/month
- Annual cost: $1,440

SAVINGS: 98.9% reduction = $128,160/year

Additional Benefits:
✓ Automatic scaling (0-10x on demand)
✓ 99.99% availability SLA
✓ Zero server maintenance
✓ Global deployment capability
✓ Per-second billing (only pay for usage)
```

### Cost Trend Report

```
Monthly Cost Projection (Year 1):
Month 1-3: $0 (Free Tier)
Month 4-6: $30-50 (Phase in production)
Month 7-12: $120/month (Steady state)

Average Year 1: ~$70/month = $840 total

Year 2+: $120/month × 12 = $1,440/year (consistent)

Cost Drivers:
- Compute: 22% ($26)
- Database: 51% ($60)
- Load Balancing: 19% ($22)
- Monitoring: 4% ($5)
- Other: 4% ($5)

Opportunities:
- Auto-scaling: -30% = $36/month savings
- Spot instances: -$18/month
- Reserved instances: -$31/month
- Total optimized: $120 → $35/month
```

### Cost Allocation by Department

```
Finance Department Cost Attribution:
DevOps Team (33%):
- ECS management: $26 × 0.33 = $8.50

Data Team (51%):
- Database operations: $60 × 0.51 = $30.60

Platform Team (19%):
- Infrastructure: $22 × 0.19 = $4.18

Other (8%):
- Monitoring, storage: $5 × 0.08 = $0.40

Total: $43.68/month
```

---

## 7. Cost Monitoring & Alerts

### AWS Cost Explorer Setup

```bash
# Enable Cost Anomaly Detection
aws ce create-anomaly-monitor \
  --anomaly-monitor '{
    "MonitorName": "apex-api-monthly",
    "MonitorType": "DIMENSIONAL",
    "MonitorDimension": "SERVICE"
  }'

# Create alert for >20% variance
aws ce create-anomaly-detector \
  --anomaly-detector '{
    "AnomalyMonitorArn": "arn:aws:ce:...",
    "Frequency": "MONTHLY",
    "AnomalyDetectorFrequency": "DAILY"
  }'
```

### Monthly Cost Report Script

```python
import boto3

ce = boto3.client('ce')

response = ce.get_cost_and_usage(
    TimePeriod={
        'Start': '2026-10-01',
        'End': '2026-10-31'
    },
    Granularity='DAILY',
    Metrics=['BlendedCost'],
    GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
)

# Generate report
for result in response['ResultsByTime']:
    print(f"Date: {result['TimePeriod']['Start']}")
    for group in result['Groups']:
        service = group['Keys'][0]
        cost = float(group['Metrics']['BlendedCost']['Amount'])
        if cost > 0:
            print(f"  {service}: ${cost:.2f}")
```

### Budget Alerts

```bash
# Create $150/month budget with alert at 80%
aws budgets create-budget \
  --account-id 123456789 \
  --budget '{
    "BudgetName": "apex-api-monthly",
    "BudgetLimit": {"Amount": "150", "Unit": "USD"},
    "TimeUnit": "MONTHLY",
    "BudgetType": "COST",
    "CostFilters": {"TagKeyValue": ["apex-api"]}
  }'
```

---

## 8. Cost Comparison Matrix

### When to Use Each Service

| Workload | Recommended | Reason |
|----------|------------|--------|
| Development | AWS Free Tier | $0 cost |
| Production ≤100K req/day | ECS Fargate | Simplest ops |
| Production >1M req/day | EKS + EC2 | Volume discounts |
| High availability | Multi-AZ | 99.99% SLA |
| Batch processing | Spot Instances | 70% savings |
| Cost-sensitive | GCP | Slightly cheaper |
| Enterprise features | Azure | Best integration |

---

## 9. ROI Analysis

### Investment vs. Return

```
Initial Setup (One-time):
- Architecture design: 16 hours × $100/hr = $1,600
- Implementation: 40 hours × $100/hr = $4,000
- Testing & optimization: 20 hours × $100/hr = $2,000
- Total: $7,600

Annual Operational Savings:
- On-premises vs. AWS: $128,160/year
- Maintenance staff reduction: $50,000/year
- Energy & facilities: $20,000/year
- Total: $198,160/year

ROI:
- Break-even: 7,600 / (198,160 / 12) = 0.46 months
- Year 1 savings: $198,160 - $7,600 = $190,560
- Year 3 savings: $190,560 × 3 = $571,680

ROI: 2507% in first 3 years
```

---

## 10. Governance & Controls

### Cost Management Best Practices

1. **Tag All Resources**
   ```bash
   aws ec2 create-tags --resources i-1234567890abcdef0 \
     --tags Key=CostCenter,Value=devops Key=Environment,Value=prod
   ```

2. **Use AWS Config for Compliance**
   - Prevent untagged resources
   - Enforce instance size limits
   - Require encryption

3. **Set Budget Alerts**
   - Monthly ceiling: $200
   - Alert at: 80% ($160)
   - Alert method: Email + Slack

4. **Monthly Review**
   - Compare actual vs. projected
   - Identify cost anomalies
   - Adjust resource allocation

---

## 11. Cloud Cost Awareness Quick Reference

### Formula for Estimating Any Workload

```
Total Monthly Cost = Compute + Database + Storage + Networking + Monitoring

Where:

Compute (CPU-based pricing):
  Cost = (# instances) × (vCPU price/hour) × 730 hours

Database (capacity-based pricing):
  Cost = (GB storage) × (monthly rate) + (IOPS × rate)

Storage (consumption-based pricing):
  Cost = (GB stored) × (per-GB rate)

Networking (transfer-based pricing):
  Cost = (GB transferred out) × (per-GB rate)

Monitoring (metric/log-based pricing):
  Cost = (# custom metrics × monthly rate) + (log ingestion × rate)
```

### Cost Per Unit Metrics (for comparison)

```
Cost per Request:
= Monthly Cost / Requests per Month
= $120 / (1000 req/sec × 86400 × 30)
= $120 / 2,592,000,000
= $0.000000046 per request
= $0.046 per million requests

Cost per GB Stored:
= $60 (database) / 10 GB
= $6 per GB per month
= $72 per GB per year

Cost per User:
= $120 / 1000 active users
= $0.12 per user per month
= $1.44 per user per year
```

---

## 12. Cloud Migration Checklist

- [ ] Forecast compute requirements (vCPU, memory)
- [ ] Estimate data volume (storage, throughput)
- [ ] Calculate monthly baseline cost
- [ ] Identify optimization opportunities
- [ ] Set up cost monitoring & alerts
- [ ] Establish budget limits
- [ ] Document assumptions & trade-offs
- [ ] Get stakeholder approval
- [ ] Review monthly for first 3 months
- [ ] Adjust reservations after stabilization

---

**Cost Analysis Version:** 1.0.0  
**Last Updated:** 2026-10-29  
**Prepared For:** Stakeholder Communication  
**Next Review Date:** 2026-12-29
