-- Migration: Add Label Source Tracking
-- Version: 004
-- Description: Add source tracking columns to vm_labels and enhance labels table
-- Created: 2025-12-05

-- ========================================
-- Table: labels - Add new columns
-- ========================================
-- Add columns to support better label organization and display
ALTER TABLE labels ADD COLUMN name VARCHAR(255);
ALTER TABLE labels ADD COLUMN category VARCHAR(100);

-- Populate name column with key-value combination for existing labels
UPDATE labels SET name = key || ' = ' || value WHERE name IS NULL;

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_labels_name ON labels(name);
CREATE INDEX IF NOT EXISTS idx_labels_category ON labels(category);

-- ========================================
-- Table: vm_labels - Add source tracking columns
-- ========================================
-- Add columns to track where labels came from (naming conventions, manual, etc.)
ALTER TABLE vm_labels ADD COLUMN label_source VARCHAR(50);
ALTER TABLE vm_labels ADD COLUMN source_convention_id INTEGER;
ALTER TABLE vm_labels ADD COLUMN source_field_name VARCHAR(100);
ALTER TABLE vm_labels ADD COLUMN auto_created BOOLEAN DEFAULT 0;

-- Add foreign key constraint for source_convention_id
-- Note: SQLite doesn't support adding FK after table creation,
-- so this will be enforced at application level

-- Create indexes for source tracking queries
CREATE INDEX IF NOT EXISTS idx_vm_labels_label_source ON vm_labels(label_source);
CREATE INDEX IF NOT EXISTS idx_vm_labels_source_convention_id ON vm_labels(source_convention_id);
CREATE INDEX IF NOT EXISTS idx_vm_labels_auto_created ON vm_labels(auto_created);

-- ========================================
-- Populate source data for existing naming convention labels
-- ========================================
-- Mark existing labels that were created from naming conventions
UPDATE vm_labels
SET
    label_source = 'naming_convention',
    auto_created = 1
WHERE label_id IN (
    SELECT l.id
    FROM labels l
    WHERE l.key LIKE 'nc:%' OR l.name LIKE 'nc:%'
);

-- ========================================
-- Update schema_versions table
-- ========================================
-- Record this migration
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
    '004',
    'Add label source tracking and enhanced label columns',
    CURRENT_TIMESTAMP,
    'migration_script',
    '004_add_label_source_tracking.sql',
    NULL,
    'labels, vm_labels',
    1,
    1,
    'Adds source tracking to vm_labels for tracing label origin (naming conventions, manual, folder inheritance). Adds name and category columns to labels for better organization.'
);

-- ========================================
-- Rollback Script
-- ========================================
-- To rollback this migration, run:
--
-- For SQLite, column removal requires table recreation:
/*
-- Backup tables
CREATE TABLE labels_backup AS SELECT id, key, value, description, color, created_at, updated_at FROM labels;
CREATE TABLE vm_labels_backup AS SELECT id, vm_id, label_id, assigned_at, assigned_by, inherited_from_folder, source_folder_path FROM vm_labels;

-- Drop and recreate tables
DROP TABLE vm_labels;
DROP TABLE labels;

-- Recreate original labels table
CREATE TABLE labels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key VARCHAR(100) NOT NULL,
    value VARCHAR(255) NOT NULL,
    description VARCHAR(500),
    color VARCHAR(7),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT _label_key_value_uc UNIQUE (key, value)
);
CREATE INDEX idx_labels_key ON labels(key);
CREATE INDEX idx_labels_value ON labels(value);

-- Recreate original vm_labels table
CREATE TABLE vm_labels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vm_id INTEGER NOT NULL,
    label_id INTEGER NOT NULL,
    assigned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    assigned_by VARCHAR(100),
    inherited_from_folder BOOLEAN DEFAULT 0,
    source_folder_path VARCHAR(500),
    CONSTRAINT _vm_label_uc UNIQUE (vm_id, label_id),
    FOREIGN KEY (vm_id) REFERENCES virtual_machines(id) ON DELETE CASCADE,
    FOREIGN KEY (label_id) REFERENCES labels(id) ON DELETE CASCADE
);
CREATE INDEX idx_vm_labels_vm_id ON vm_labels(vm_id);
CREATE INDEX idx_vm_labels_label_id ON vm_labels(label_id);
CREATE INDEX idx_vm_labels_inherited ON vm_labels(inherited_from_folder);

-- Restore data
INSERT INTO labels SELECT * FROM labels_backup;
INSERT INTO vm_labels SELECT * FROM vm_labels_backup;

-- Drop backup tables
DROP TABLE labels_backup;
DROP TABLE vm_labels_backup;

-- Remove from schema_versions
DELETE FROM schema_versions WHERE version = '004';
*/
