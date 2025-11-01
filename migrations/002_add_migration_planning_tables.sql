-- Migration: Add Migration Planning Tables
-- Version: 1.1.0
-- Date: 2025-10-30
-- Description: Adds MigrationTarget, MigrationScenario, and MigrationWave tables for multi-platform migration planning

-- ============================================================================
-- 1. CREATE MIGRATION_TARGETS TABLE (Migration destination platforms)
-- ============================================================================

CREATE TABLE IF NOT EXISTS migration_targets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL UNIQUE,
    platform_type VARCHAR(50) NOT NULL,
    region VARCHAR(100),
    
    -- Network configuration
    bandwidth_mbps INTEGER DEFAULT 1000,
    network_efficiency REAL DEFAULT 0.8,
    
    -- Cost factors (per hour)
    compute_cost_per_vcpu REAL DEFAULT 0.0,
    memory_cost_per_gb REAL DEFAULT 0.0,
    storage_cost_per_gb REAL DEFAULT 0.0,
    network_ingress_cost_per_gb REAL DEFAULT 0.0,
    network_egress_cost_per_gb REAL DEFAULT 0.0,
    
    -- Platform-specific attributes (JSON)
    platform_attributes TEXT,
    
    -- Constraints
    max_parallel_migrations INTEGER DEFAULT 10,
    min_required_bandwidth_mbps INTEGER DEFAULT 100,
    supports_live_migration BOOLEAN DEFAULT 0,
    
    -- Service level
    sla_uptime_percent REAL DEFAULT 99.9,
    support_level VARCHAR(50),
    
    -- Active/enabled
    is_active BOOLEAN DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_migration_targets_platform_type ON migration_targets(platform_type);
CREATE INDEX IF NOT EXISTS idx_migration_targets_is_active ON migration_targets(is_active);

-- ============================================================================
-- 2. CREATE MIGRATION_SCENARIOS TABLE (Migration plans)
-- ============================================================================

CREATE TABLE IF NOT EXISTS migration_scenarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    description VARCHAR(1000),
    
    -- Target
    target_id INTEGER NOT NULL,
    
    -- Strategy
    strategy VARCHAR(50) NOT NULL DEFAULT 'rehost',
    
    -- VM selection criteria (JSON)
    vm_selection_criteria TEXT,
    
    -- Timeline
    estimated_duration_days REAL,
    estimated_cost_total REAL,
    estimated_cost_breakdown TEXT,
    
    -- Risk assessment
    risk_level VARCHAR(20),
    risk_factors TEXT,
    
    -- Recommendations
    recommended BOOLEAN DEFAULT 0,
    recommendation_score REAL,
    recommendation_reasons TEXT,
    
    -- Metadata
    created_at VARCHAR(50),
    updated_at VARCHAR(50),
    created_by VARCHAR(100),
    
    FOREIGN KEY (target_id) REFERENCES migration_targets(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_migration_scenarios_target_id ON migration_scenarios(target_id);
CREATE INDEX IF NOT EXISTS idx_migration_scenarios_strategy ON migration_scenarios(strategy);
CREATE INDEX IF NOT EXISTS idx_migration_scenarios_recommended ON migration_scenarios(recommended);

-- ============================================================================
-- 3. CREATE MIGRATION_WAVES TABLE (Phased migration execution)
-- ============================================================================

CREATE TABLE IF NOT EXISTS migration_waves (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scenario_id INTEGER NOT NULL,
    
    wave_number INTEGER NOT NULL,
    wave_name VARCHAR(255),
    
    -- VM list (JSON array of VM IDs)
    vm_ids TEXT,
    
    -- Timeline
    start_date VARCHAR(50),
    end_date VARCHAR(50),
    duration_hours REAL,
    
    -- Status
    status VARCHAR(50) DEFAULT 'planned',
    
    -- Dependencies
    depends_on_wave_ids TEXT,
    
    FOREIGN KEY (scenario_id) REFERENCES migration_scenarios(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_migration_waves_scenario_id ON migration_waves(scenario_id);
CREATE INDEX IF NOT EXISTS idx_migration_waves_wave_number ON migration_waves(wave_number);
CREATE INDEX IF NOT EXISTS idx_migration_waves_status ON migration_waves(status);

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================
