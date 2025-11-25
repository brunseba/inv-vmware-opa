-- Migration: Add Naming Convention Tables
-- Version: 003
-- Description: Add tables for VM naming convention management and analysis
-- Created: 2025-11-25

-- ========================================
-- Table: naming_conventions
-- ========================================
-- Stores VM naming convention definitions
CREATE TABLE IF NOT EXISTS naming_conventions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    pattern VARCHAR(500) NOT NULL,
    total_length INTEGER,
    is_active BOOLEAN DEFAULT 1 NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by VARCHAR(100)
);

CREATE INDEX IF NOT EXISTS idx_naming_conventions_name ON naming_conventions(name);
CREATE INDEX IF NOT EXISTS idx_naming_conventions_is_active ON naming_conventions(is_active);

-- ========================================
-- Table: naming_convention_fields
-- ========================================
-- Stores field definitions for naming conventions
CREATE TABLE IF NOT EXISTS naming_convention_fields (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    convention_id INTEGER NOT NULL,
    field_name VARCHAR(100) NOT NULL,
    position INTEGER NOT NULL,
    length INTEGER NOT NULL,
    description TEXT,
    possible_values JSON,
    is_required BOOLEAN DEFAULT 1 NOT NULL,
    validation_regex VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (convention_id) REFERENCES naming_conventions(id) ON DELETE CASCADE,
    CONSTRAINT _convention_field_name_uc UNIQUE (convention_id, field_name),
    CONSTRAINT _convention_field_position_uc UNIQUE (convention_id, position)
);

CREATE INDEX IF NOT EXISTS idx_naming_convention_fields_convention_id ON naming_convention_fields(convention_id);

-- ========================================
-- Table: vm_naming_analysis
-- ========================================
-- Stores VM name parsing and analysis results
CREATE TABLE IF NOT EXISTS vm_naming_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vm_id INTEGER NOT NULL,
    convention_id INTEGER NOT NULL,
    vm_name VARCHAR(255) NOT NULL,
    field_values JSON NOT NULL,
    is_valid BOOLEAN DEFAULT 1 NOT NULL,
    validation_errors JSON,
    match_confidence INTEGER,
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (vm_id) REFERENCES virtual_machines(id) ON DELETE CASCADE,
    FOREIGN KEY (convention_id) REFERENCES naming_conventions(id) ON DELETE CASCADE,
    CONSTRAINT _vm_convention_analysis_uc UNIQUE (vm_id, convention_id)
);

CREATE INDEX IF NOT EXISTS idx_vm_naming_analysis_vm_id ON vm_naming_analysis(vm_id);
CREATE INDEX IF NOT EXISTS idx_vm_naming_analysis_convention_id ON vm_naming_analysis(convention_id);
CREATE INDEX IF NOT EXISTS idx_vm_naming_analysis_vm_name ON vm_naming_analysis(vm_name);
CREATE INDEX IF NOT EXISTS idx_vm_naming_analysis_is_valid ON vm_naming_analysis(is_valid);
CREATE INDEX IF NOT EXISTS idx_vm_naming_analysis_analyzed_at ON vm_naming_analysis(analyzed_at);

-- ========================================
-- Update schema_versions table
-- ========================================
-- Record this migration (if schema_versions table exists)
INSERT OR IGNORE INTO schema_versions (
    version,
    description,
    applied_at,
    applied_by,
    migration_script,
    tables_added,
    tables_modified,
    is_current,
    rollback_available,
    notes
) VALUES (
    '003',
    'Add naming convention management tables',
    CURRENT_TIMESTAMP,
    'migration_script',
    '003_add_naming_convention_tables.sql',
    'naming_conventions, naming_convention_fields, vm_naming_analysis',
    NULL,
    1,
    1,
    'Adds support for VM naming convention management and analysis'
);

-- ========================================
-- Rollback Script
-- ========================================
-- To rollback this migration, run:
-- DROP TABLE IF EXISTS vm_naming_analysis;
-- DROP TABLE IF EXISTS naming_convention_fields;
-- DROP TABLE IF EXISTS naming_conventions;
-- DELETE FROM schema_versions WHERE version = '003';
