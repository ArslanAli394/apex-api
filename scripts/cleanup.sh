#!/bin/bash

# Cleanup script for Apex API
# Removes containers, volumes, and temporary files

set -e

echo "🧹 Apex API Cleanup"
echo "=================="

FORCE_CLEAN=${1:-false}

if [ "$FORCE_CLEAN" != "--force" ]; then
    echo ""
    echo "⚠️  WARNING: This will remove all Docker containers and volumes"
    read -p "Continue? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cleanup cancelled"
        exit 0
    fi
fi

echo ""
echo "Stopping and removing containers..."
docker-compose down -v 2>/dev/null || true

echo "Removing test coverage files..."
rm -rf htmlcov/ coverage.xml .coverage 2>/dev/null || true

echo "Removing build artifacts..."
rm -rf build/ dist/ *.egg-info 2>/dev/null || true

echo "Removing Python cache..."
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true

echo "Removing temporary files..."
rm -rf .pytest_cache/ .pylint.d/ 2>/dev/null || true

echo ""
echo "✅ Cleanup complete"
