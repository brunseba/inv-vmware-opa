-- Migration: Add VM and Folder Labelling Tables
-- Version: 0.5.0
-- Date: 2025-10-28
-- Description: Adds Label, VMLabel, and FolderLabel tables for tagging VMs and folders

-- ============================================================================
-- 1. CREATE LABELS TABLE (Master label definitions)
-- ============================================================================

CREATE TABLE IF NOT EXISTS labels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key VARCHAR(100) NOT NULL,
    value VARCHAR(255) NOT NULL,
    description VARCHAR(500),
    color VARCHAR(7),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT _label_key_value_uc UNIQUE (key, value)
);

CREATE INDEX IF NOT EXISTS idx_labels_key ON labels(key);
CREATE INDEX IF NOT EXISTS idx_labels_value ON labels(value);

-- ============================================================================
-- 2. CREATE VM_LABELS TABLE (VM-to-Label assignments)
-- ============================================================================

CREATE TABLE IF NOT EXISTS vm_labels (
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

CREATE INDEX IF NOT EXISTS idx_vm_labels_vm_id ON vm_labels(vm_id);
CREATE INDEX IF NOT EXISTS idx_vm_labels_label_id ON vm_labels(label_id);
CREATE INDEX IF NOT EXISTS idx_vm_labels_inherited ON vm_labels(inherited_from_folder);

-- ============================================================================
-- 3. CREATE FOLDER_LABELS TABLE (Folder-to-Label assignments)
-- ============================================================================

CREATE TABLE IF NOT EXISTS folder_labels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    folder_path VARCHAR(500) NOT NULL,
    label_id INTEGER NOT NULL,
    assigned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    assigned_by VARCHAR(100),
    inherit_to_vms BOOLEAN DEFAULT 1,
    inherit_to_subfolders BOOLEAN DEFAULT 0,
    CONSTRAINT _folder_label_uc UNIQUE (folder_path, label_id),
    FOREIGN KEY (label_id) REFERENCES labels(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_folder_labels_folder_path ON folder_labels(folder_path);
CREATE INDEX IF NOT EXISTS idx_folder_labels_label_id ON folder_labels(label_id);

-- ============================================================================
-- 4. INSERT DEFAULT LABELS (Optional - examples)
-- ============================================================================

-- Uncomment to add default labels
/*
INSERT OR IGNORE INTO labels (key, value, description, color) VALUES
    ('environment', 'production', 'Production environment', '#FF0000'),
    ('environment', 'development', 'Development environment', '#00FF00'),
    ('environment', 'testing', 'Testing environment', '#0000FF'),
    ('environment', 'staging', 'Staging environment', '#FFA500'),
    ('project', 'ProjectX', 'Main project', '#4169E1'),
    ('project', 'ProjectY', 'Secondary project', '#9370DB'),
    ('application', 'web-server', 'Web server application', '#20B2AA'),
    ('application', 'database', 'Database application', '#8B4513'),
    ('application', 'api', 'API service', '#FF69B4'),
    ('owner', 'team-a', 'Team A ownership', '#32CD32'),
    ('owner', 'team-b', 'Team B ownership', '#FFD700');
*/

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================
