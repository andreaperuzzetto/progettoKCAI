-- Migration 002: Phase 5 — Organizations, Insights, Menu, Operations

-- organizations (new table)
CREATE TABLE IF NOT EXISTS organizations (
  id CHAR(32) PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT now()
);

-- users: add org fields
ALTER TABLE users
  ADD COLUMN IF NOT EXISTS organization_id CHAR(32) REFERENCES organizations(id),
  ADD COLUMN IF NOT EXISTS role VARCHAR(20) NOT NULL DEFAULT 'admin';

-- restaurants: add org + location fields
ALTER TABLE restaurants
  ADD COLUMN IF NOT EXISTS organization_id CHAR(32) REFERENCES organizations(id),
  ADD COLUMN IF NOT EXISTS city VARCHAR(100),
  ADD COLUMN IF NOT EXISTS category VARCHAR(100);

-- insights (new table)
CREATE TABLE IF NOT EXISTS insights (
  id CHAR(32) PRIMARY KEY,
  restaurant_id CHAR(32) NOT NULL REFERENCES restaurants(id),
  type VARCHAR(50) NOT NULL,
  message TEXT NOT NULL,
  confidence FLOAT NOT NULL DEFAULT 0.5,
  impact FLOAT NOT NULL DEFAULT 0.5,
  created_at TIMESTAMP NOT NULL DEFAULT now(),
  read_at TIMESTAMP
);

-- product_metrics (new table)
CREATE TABLE IF NOT EXISTS product_metrics (
  id CHAR(32) PRIMARY KEY,
  restaurant_id CHAR(32) NOT NULL REFERENCES restaurants(id),
  product_name VARCHAR(255) NOT NULL,
  total_quantity INTEGER NOT NULL DEFAULT 0,
  total_revenue NUMERIC(10,2) NOT NULL DEFAULT 0,
  avg_daily_qty FLOAT NOT NULL DEFAULT 0,
  trend_7d FLOAT NOT NULL DEFAULT 0,
  popularity_score FLOAT NOT NULL DEFAULT 0,
  computed_at TIMESTAMP NOT NULL DEFAULT now()
);

-- purchase_orders (new table)
CREATE TABLE IF NOT EXISTS purchase_orders (
  id CHAR(32) PRIMARY KEY,
  restaurant_id CHAR(32) NOT NULL REFERENCES restaurants(id),
  for_date DATE NOT NULL,
  items JSON NOT NULL DEFAULT '[]',
  status VARCHAR(20) NOT NULL DEFAULT 'draft',
  created_at TIMESTAMP NOT NULL DEFAULT now()
);

-- market_metrics (new table)
CREATE TABLE IF NOT EXISTS market_metrics (
  id CHAR(32) PRIMARY KEY,
  city VARCHAR(100) NOT NULL,
  category VARCHAR(100),
  avg_sentiment_positive FLOAT NOT NULL DEFAULT 0,
  avg_rating FLOAT NOT NULL DEFAULT 0,
  top_issues JSON NOT NULL DEFAULT '[]',
  restaurant_count INTEGER NOT NULL DEFAULT 0,
  computed_at TIMESTAMP NOT NULL DEFAULT now()
);
