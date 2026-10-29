-- Initial database schema for Apex API
-- This script is automatically run when PostgreSQL container starts

-- Create extension for JSONB support
CREATE EXTENSION IF NOT EXISTS hstore;

-- Create items table
CREATE TABLE IF NOT EXISTS items (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'active' NOT NULL,
    created_by VARCHAR(100),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_items_category ON items(category);
CREATE INDEX IF NOT EXISTS idx_items_status ON items(status);
CREATE INDEX IF NOT EXISTS idx_items_created_at ON items(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_items_category_status ON items(category, status);
CREATE INDEX IF NOT EXISTS idx_items_name ON items(name);

-- Insert sample data for testing
INSERT INTO items (name, description, category, status, created_by, metadata) VALUES
    ('Sample Item 1', 'First sample item for testing', 'sample', 'active', 'system', '{"version": "1.0"}'),
    ('Sample Item 2', 'Second sample item for testing', 'demo', 'active', 'system', '{"version": "1.0"}'),
    ('Sample Item 3', 'Third sample item for testing', 'test', 'inactive', 'system', '{"priority": "high"}')
ON CONFLICT DO NOTHING;

-- Create audit log table (optional, for tracking changes)
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    entity_type VARCHAR(50),
    entity_id INTEGER,
    action VARCHAR(20),
    old_values JSONB,
    new_values JSONB,
    performed_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Grant appropriate permissions
GRANT CONNECT ON DATABASE apex_db TO apex_user;
GRANT USAGE ON SCHEMA public TO apex_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO apex_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO apex_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO apex_user;

-- Create test database if it doesn't exist
CREATE DATABASE apex_test_db OWNER apex_user;
