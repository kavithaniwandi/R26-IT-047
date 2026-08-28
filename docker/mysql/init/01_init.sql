-- ============================================================
-- docker/mysql/init/01_init.sql
-- MySQL initialization script (runs once on first container start)
-- ============================================================

-- Ensure we're using the correct database
USE disaster_relief;

-- Set proper character set and collation
ALTER DATABASE disaster_relief
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

-- Grant full privileges to the app user
GRANT ALL PRIVILEGES ON disaster_relief.* TO 'relief_user'@'%';
FLUSH PRIVILEGES;

-- Note: SQLAlchemy will create all tables via init_db() on startup
-- This script only handles MySQL-specific initialization
