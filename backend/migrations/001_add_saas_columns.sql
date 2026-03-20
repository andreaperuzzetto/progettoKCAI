-- Migration 001: Add SaaS columns to match SQLAlchemy models
-- Run once against an existing database that was created before Phase 2+

-- users: add subscription/plan fields
ALTER TABLE users
  ADD COLUMN IF NOT EXISTS subscription_status VARCHAR(20) NOT NULL DEFAULT 'trial',
  ADD COLUMN IF NOT EXISTS plan VARCHAR(20) NOT NULL DEFAULT 'starter',
  ADD COLUMN IF NOT EXISTS trial_ends_at TIMESTAMP;

-- restaurants: add owner_user_id FK
ALTER TABLE restaurants
  ADD COLUMN IF NOT EXISTS owner_user_id CHAR(32) REFERENCES users(id);

-- reviews: add rating + created_at
ALTER TABLE reviews
  ADD COLUMN IF NOT EXISTS rating INTEGER,
  ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT now();

-- sales: rename product→product_name, add revenue + created_at
-- (skip rename if already done)
DO $$ BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.columns
             WHERE table_name='sales' AND column_name='product') THEN
    ALTER TABLE sales RENAME COLUMN product TO product_name;
  END IF;
END $$;
ALTER TABLE sales
  ADD COLUMN IF NOT EXISTS revenue NUMERIC(10,2),
  ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT now();

-- forecasts: incompatible schema — drop and recreate
DROP TABLE IF EXISTS forecasts CASCADE;
CREATE TABLE IF NOT EXISTS forecasts (
  id CHAR(32) PRIMARY KEY,
  restaurant_id CHAR(32) NOT NULL REFERENCES restaurants(id),
  date DATE NOT NULL,
  expected_covers INTEGER NOT NULL,
  product_predictions JSON NOT NULL DEFAULT '{}',
  created_at TIMESTAMP NOT NULL DEFAULT now()
);
