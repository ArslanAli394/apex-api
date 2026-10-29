#!/bin/bash

# Rollback script for Apex API
# Demonstrates safe rollback to previous version

set -e

echo "🔄 Apex API Rollback Procedure"
echo "=============================="

# Load environment
if [ -f ".env" ]; then
    export $(cat .env | grep -v '#' | xargs)
fi

CURRENT_VERSION=$(docker ps --filter "name=apex-api" --format "{{.Image}}" | head -n 1 | rev | cut -d: -f1 | rev)
echo "Current version: $CURRENT_VERSION"

# Get previous version
PREVIOUS_VERSION="${1:-latest}"

if [ "$PREVIOUS_VERSION" = "latest" ]; then
    echo "❌ Error: Previous version not specified"
    echo "Usage: ./rollback.sh <version>"
    echo "Example: ./rollback.sh 1.0.0"
    exit 1
fi

echo ""
echo "Rolling back to version: $PREVIOUS_VERSION"

# Stop current containers
echo ""
echo "Stopping current containers..."
docker-compose down

# Update docker-compose to use previous version
echo "Updating image reference..."
sed -i.bak "s/:$CURRENT_VERSION/:$PREVIOUS_VERSION/g" docker-compose.yml

# Start previous version
echo ""
echo "Starting previous version..."
docker-compose up -d

# Wait for services to be healthy
echo ""
echo "Waiting for services to be healthy..."
for i in {1..30}; do
    if docker-compose exec -T api curl -f http://localhost:8000/health/live > /dev/null 2>&1; then
        echo "✅ API is healthy"
        break
    fi
    echo "  Waiting... ($i/30)"
    sleep 2
done

# Verify rollback
echo ""
echo "Verifying rollback..."
VERSION_RESPONSE=$(docker-compose exec -T api curl -s http://localhost:8000/ | grep -o '"version":"[^"]*"' | cut -d'"' -f4)

if [ "$VERSION_RESPONSE" != "" ]; then
    echo "✅ Rollback successful"
    echo "   Running version: $VERSION_RESPONSE"
else
    echo "❌ Rollback verification failed"
    exit 1
fi

echo ""
echo "Rollback completed successfully!"
echo "To revert this rollback, use: ./rollback.sh $CURRENT_VERSION"

# Restore original compose file
mv docker-compose.yml.bak docker-compose.yml
