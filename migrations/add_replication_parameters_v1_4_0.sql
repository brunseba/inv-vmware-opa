-- Migration: Add Replication Efficiency Parameters
-- Version: 1.4.0
-- Date: 2025-10-30
-- Description: Adds realistic replication parameters to migration_targets and migration_strategy_configs

-- ========================================
-- MIGRATION_TARGETS TABLE
-- ========================================

-- Add replication efficiency parameters
ALTER TABLE migration_targets ADD COLUMN compression_ratio REAL DEFAULT 0.6;
ALTER TABLE migration_targets ADD COLUMN dedup_ratio REAL DEFAULT 0.8;
ALTER TABLE migration_targets ADD COLUMN change_rate_percent REAL DEFAULT 0.10;
ALTER TABLE migration_targets ADD COLUMN network_protocol_overhead REAL DEFAULT 1.2;
ALTER TABLE migration_targets ADD COLUMN delta_sync_count INTEGER DEFAULT 2;

-- Update existing targets with default values
UPDATE migration_targets 
SET 
    compression_ratio = 0.6,
    dedup_ratio = 0.8,
    change_rate_percent = 0.10,
    network_protocol_overhead = 1.2,
    delta_sync_count = 2
WHERE compression_ratio IS NULL;

-- ========================================
-- MIGRATION_STRATEGY_CONFIGS TABLE
-- ========================================

-- Add replication parameters
ALTER TABLE migration_strategy_configs ADD COLUMN replication_efficiency REAL DEFAULT 1.0;
ALTER TABLE migration_strategy_configs ADD COLUMN parallel_replication_factor REAL DEFAULT 1.0;

-- Update existing strategy configs with strategy-specific values
-- REHOST: standard replication (1.0)
UPDATE migration_strategy_configs 
SET replication_efficiency = 1.0, parallel_replication_factor = 1.0 
WHERE strategy = 'rehost' AND replication_efficiency IS NULL;

-- REPLATFORM: slight overhead for conversion (1.2)
UPDATE migration_strategy_configs 
SET replication_efficiency = 1.2, parallel_replication_factor = 0.9 
WHERE strategy = 'replatform' AND replication_efficiency IS NULL;

-- REFACTOR: significant overhead for re-architecture (1.5)
UPDATE migration_strategy_configs 
SET replication_efficiency = 1.5, parallel_replication_factor = 0.7 
WHERE strategy = 'refactor' AND replication_efficiency IS NULL;

-- REPURCHASE: SaaS provider handles most (0.8)
UPDATE migration_strategy_configs 
SET replication_efficiency = 0.8, parallel_replication_factor = 1.2 
WHERE strategy = 'repurchase' AND replication_efficiency IS NULL;

-- RETIRE: minimal replication needed (0.5)
UPDATE migration_strategy_configs 
SET replication_efficiency = 0.5, parallel_replication_factor = 1.0 
WHERE strategy = 'retire' AND replication_efficiency IS NULL;

-- RETAIN: no replication (0.1)
UPDATE migration_strategy_configs 
SET replication_efficiency = 0.1, parallel_replication_factor = 1.0 
WHERE strategy = 'retain' AND replication_efficiency IS NULL;

-- ========================================
-- SCHEMA VERSION UPDATE
-- ========================================

INSERT INTO schema_versions (version, applied_at, description, migration_script)
VALUES (
    '1.4.0',
    datetime('now'),
    'Added replication efficiency parameters for realistic migration duration calculations',
    'add_replication_parameters_v1_4_0.sql'
);

-- Verification queries
SELECT 'Migration Targets with new parameters:' as info;
SELECT name, compression_ratio, dedup_ratio, change_rate_percent, delta_sync_count 
FROM migration_targets 
LIMIT 5;

SELECT 'Strategy Configs with replication efficiency:' as info;
SELECT strategy, replication_efficiency, parallel_replication_factor 
FROM migration_strategy_configs;

SELECT 'Current schema version:' as info;
SELECT version, applied_at, description 
FROM schema_versions 
ORDER BY applied_at DESC 
LIMIT 1;
