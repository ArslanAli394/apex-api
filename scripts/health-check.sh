#!/bin/bash

# Health check script for Apex API
# Validates all health endpoints and dependencies

set -e

echo "🏥 Apex API Health Check"
echo "======================="

API_HOST=${API_HOST:-localhost}
API_PORT=${API_PORT:-8000}
API_URL="http://$API_HOST:$API_PORT"

CHECKS_PASSED=0
CHECKS_FAILED=0

check_endpoint() {
    local name=$1
    local endpoint=$2
    local expected_status=${3:-200}

    echo ""
    echo "Checking: $name"

    response=$(curl -s -w "\n%{http_code}" "$API_URL$endpoint")
    http_code=$(echo "$response" | tail -n 1)
    body=$(echo "$response" | head -n -1)

    if [ "$http_code" = "$expected_status" ]; then
        echo "  ✅ Status: $http_code"
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
    else
        echo "  ❌ Status: $http_code (expected $expected_status)"
        CHECKS_FAILED=$((CHECKS_FAILED + 1))
    fi

    if [ ! -z "$body" ]; then
        echo "  Response: $(echo $body | head -c 100)"
    fi
}

# Run health checks
echo ""
echo "Service Endpoints:"
check_endpoint "Service Info" "/" 200
check_endpoint "Liveness Probe" "/health/live" 200
check_endpoint "Readiness Probe" "/health/ready" 200
check_endpoint "Ping" "/ping" 200

echo ""
echo "API Endpoints:"
check_endpoint "List Items" "/api/v1/items" 200
check_endpoint "Get Metrics" "/metrics" 200
check_endpoint "Get Docs" "/docs" 200

# Summary
echo ""
echo "Health Check Summary"
echo "==================="
echo "✅ Passed: $CHECKS_PASSED"
echo "❌ Failed: $CHECKS_FAILED"

if [ $CHECKS_FAILED -eq 0 ]; then
    echo ""
    echo "✅ All health checks passed!"
    exit 0
else
    echo ""
    echo "❌ Some health checks failed"
    exit 1
fi
