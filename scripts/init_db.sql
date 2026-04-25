-- SAP MM/SD AI Copilot — PostgreSQL initialisation script
-- Run automatically by the postgres container on first start.
-- Tables are created by Alembic (alembic upgrade head) at application boot.

CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
