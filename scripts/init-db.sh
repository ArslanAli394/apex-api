#!/bin/bash

# Database initialization script
# Initializes PostgreSQL and runs migrations

set -e

echo "🗄️  Initializing Apex API Database"
echo "=================================="

# Load environment variables
if [ -f ".env" ]; then
    export $(cat .env | grep -v '#' | xargs)
else
    export $(cat .env.example | grep -v '#' | xargs)
fi

DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-5432}
DB_USER=${DB_USER:-apex_user}
DB_PASSWORD=${DB_PASSWORD:-apex_password}
DB_NAME=${DB_NAME:-apex_db}

echo "Database Configuration:"
echo "  Host: $DB_HOST"
echo "  Port: $DB_PORT"
echo "  User: $DB_USER"
echo "  Database: $DB_NAME"

# Wait for database to be ready
echo ""
echo "Waiting for database to be ready..."
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d postgres -c "SELECT 1" > /dev/null 2>&1; then
        echo "✅ Database is ready"
        break
    fi
    attempt=$((attempt + 1))
    echo "  Attempt $attempt/$max_attempts: Waiting..."
    sleep 1
done

if [ $attempt -eq $max_attempts ]; then
    echo "❌ Database connection failed after $max_attempts attempts"
    exit 1
fi

# Create database if it doesn't exist
echo ""
echo "Creating database schema..."
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d postgres -c "CREATE DATABASE $DB_NAME;" 2>/dev/null || true

# Run migrations
echo "Running migrations..."
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d $DB_NAME -f migrations/init.sql

echo ""
echo "✅ Database initialization complete"
echo ""
echo "Database ready at: postgresql://$DB_USER:***@$DB_HOST:$DB_PORT/$DB_NAME"
