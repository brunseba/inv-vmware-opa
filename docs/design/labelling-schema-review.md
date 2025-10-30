# Database Schema Review: Labelling Feature

## Current Schema Analysis

### Existing VirtualMachine Model
- **Primary Key**: `id` (Integer, auto-increment)
- **Unique Identifiers**: `vm_uuid` (UUID, unique, indexed)
- **Folder Property**: `folder` (String(500), indexed) - **ALREADY EXISTS**
- **Indexes**: 
  - `vm`, `powerstate`, `template`, `creation_date`
  - `datacenter`, `cluster`, `host`, `resource_pool`, `folder`
  - `os_config`, `env`, `vm_id`, `vm_uuid`

### Key Observations
1. ✅ `folder` column exists with index - perfect for folder-based labelling
2. ✅ Existing indexes on frequently filtered columns
3. ✅ Uses modern SQLAlchemy 2.0 style (`Mapped`, `mapped_column`)
4. ⚠️ No existing relationship definitions (pure data model)

---

## Proposed New Schema

### 1. Label Table (Master Label Definitions)

```python
class Label(Base):
    """Label definitions - master list of available labels"""
    __tablename__ = "labels"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    value: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String(500))
    color: Mapped[str | None] = mapped_column(String(7))  # Hex color: #RRGGBB
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships (optional - can be omitted for pure data model)
    # vm_labels: Mapped[list["VMLabel"]] = relationship(back_populates="label", cascade="all, delete-orphan")
    # folder_labels: Mapped[list["FolderLabel"]] = relationship(back_populates="label", cascade="all, delete-orphan")
```

**Indexes**:
- PRIMARY KEY: `id`
- INDEX: `key`
- INDEX: `value`
- UNIQUE: `(key, value)` - composite unique constraint

**Rationale**:
- `key`: Label category (project, environment, application, owner, etc.)
- `value`: Specific value for that category
- `color`: For UI badges/tags visualization
- Composite unique on (key, value) prevents duplicate labels

---

### 2. VMLabel Table (VM-to-Label Assignment)

```python
class VMLabel(Base):
    """VM to Label assignment (many-to-many relationship)"""
    __tablename__ = "vm_labels"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vm_id: Mapped[int] = mapped_column(Integer, ForeignKey('virtual_machines.id', ondelete='CASCADE'), nullable=False, index=True)
    label_id: Mapped[int] = mapped_column(Integer, ForeignKey('labels.id', ondelete='CASCADE'), nullable=False, index=True)
    assigned_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    assigned_by: Mapped[str | None] = mapped_column(String(100))
    inherited_from_folder: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    source_folder_path: Mapped[str | None] = mapped_column(String(500))
    
    # Relationships (optional)
    # virtual_machine: Mapped["VirtualMachine"] = relationship(back_populates="vm_labels")
    # label: Mapped["Label"] = relationship(back_populates="vm_labels")
```

**Indexes**:
- PRIMARY KEY: `id`
- INDEX: `vm_id` (for fast VM label lookup)
- INDEX: `label_id` (for fast label usage lookup)
- INDEX: `inherited_from_folder` (for filtering direct vs inherited)
- UNIQUE: `(vm_id, label_id)` - one label per VM

**Rationale**:
- `inherited_from_folder`: Track if label came from folder (vs. directly assigned)
- `source_folder_path`: Track which folder the label was inherited from
- `assigned_by`: Audit trail (user/system)
- Composite unique on (vm_id, label_id) prevents duplicate assignments

---

### 3. FolderLabel Table (Folder-to-Label Assignment)

```python
class FolderLabel(Base):
    """Folder path to Label assignment"""
    __tablename__ = "folder_labels"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    folder_path: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    label_id: Mapped[int] = mapped_column(Integer, ForeignKey('labels.id', ondelete='CASCADE'), nullable=False, index=True)
    assigned_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    assigned_by: Mapped[str | None] = mapped_column(String(100))
    inherit_to_vms: Mapped[bool] = mapped_column(Boolean, default=True)
    inherit_to_subfolders: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Relationships (optional)
    # label: Mapped["Label"] = relationship(back_populates="folder_labels")
```

**Indexes**:
- PRIMARY KEY: `id`
- INDEX: `folder_path` (for fast folder label lookup)
- INDEX: `label_id` (for fast label usage lookup)
- UNIQUE: `(folder_path, label_id)` - one label per folder

**Rationale**:
- `folder_path`: References existing `VirtualMachine.folder` values (no FK needed)
- `inherit_to_vms`: Auto-apply label to VMs in this folder
- `inherit_to_subfolders`: Auto-apply to child folders (recursive)
- No FK on folder_path (since no Folder table)

---

## Schema Validation Rules

### Constraints
1. **Label uniqueness**: `UNIQUE(key, value)` on `labels` table
2. **VM label uniqueness**: `UNIQUE(vm_id, label_id)` on `vm_labels` table
3. **Folder label uniqueness**: `UNIQUE(folder_path, label_id)` on `folder_labels` table
4. **Cascade deletes**: When Label deleted, cascade to vm_labels and folder_labels

### Validation Logic (Application Level)
1. **Folder path validation**: Must match existing `VirtualMachine.folder` values
2. **Label key naming**: Alphanumeric + underscore/hyphen only
3. **Color format**: Valid hex color (#RRGGBB) or null
4. **Inheritance conflicts**: Direct VM label overrides inherited folder label (same key)

---

## Query Patterns

### Common Queries

**1. Get all labels for a VM (including inherited)**
```sql
-- Direct labels
SELECT l.* FROM labels l
JOIN vm_labels vl ON l.id = vl.label_id
WHERE vl.vm_id = ? AND vl.inherited_from_folder = false

-- Inherited labels (from folder hierarchy)
SELECT l.*, fl.folder_path FROM labels l
JOIN folder_labels fl ON l.id = fl.label_id
JOIN virtual_machines vm ON fl.folder_path = vm.folder OR vm.folder LIKE CONCAT(fl.folder_path, '/%')
WHERE vm.id = ? AND fl.inherit_to_vms = true
```

**2. Get all VMs with a specific label**
```sql
SELECT vm.* FROM virtual_machines vm
JOIN vm_labels vl ON vm.id = vl.vm_id
JOIN labels l ON vl.label_id = l.id
WHERE l.key = ? AND l.value = ?
```

**3. Get all folders with a specific label**
```sql
SELECT DISTINCT fl.folder_path FROM folder_labels fl
JOIN labels l ON fl.label_id = l.id
WHERE l.key = ? AND l.value = ?
```

**4. Get unique folder paths from VMs**
```sql
SELECT DISTINCT folder FROM virtual_machines
WHERE folder IS NOT NULL
ORDER BY folder
```

**5. Get VMs in a folder (with subfolders)**
```sql
-- Exact match
SELECT * FROM virtual_machines WHERE folder = ?

-- With subfolders
SELECT * FROM virtual_machines 
WHERE folder = ? OR folder LIKE CONCAT(?, '/%')
```

---

## Migration Strategy

### Phase 1: Create New Tables
```sql
CREATE TABLE labels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key VARCHAR(100) NOT NULL,
    value VARCHAR(255) NOT NULL,
    description VARCHAR(500),
    color VARCHAR(7),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(key, value)
);
CREATE INDEX idx_labels_key ON labels(key);
CREATE INDEX idx_labels_value ON labels(value);

CREATE TABLE vm_labels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vm_id INTEGER NOT NULL,
    label_id INTEGER NOT NULL,
    assigned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    assigned_by VARCHAR(100),
    inherited_from_folder BOOLEAN DEFAULT 0,
    source_folder_path VARCHAR(500),
    UNIQUE(vm_id, label_id),
    FOREIGN KEY (vm_id) REFERENCES virtual_machines(id) ON DELETE CASCADE,
    FOREIGN KEY (label_id) REFERENCES labels(id) ON DELETE CASCADE
);
CREATE INDEX idx_vm_labels_vm_id ON vm_labels(vm_id);
CREATE INDEX idx_vm_labels_label_id ON vm_labels(label_id);
CREATE INDEX idx_vm_labels_inherited ON vm_labels(inherited_from_folder);

CREATE TABLE folder_labels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    folder_path VARCHAR(500) NOT NULL,
    label_id INTEGER NOT NULL,
    assigned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    assigned_by VARCHAR(100),
    inherit_to_vms BOOLEAN DEFAULT 1,
    inherit_to_subfolders BOOLEAN DEFAULT 0,
    UNIQUE(folder_path, label_id),
    FOREIGN KEY (label_id) REFERENCES labels(id) ON DELETE CASCADE
);
CREATE INDEX idx_folder_labels_folder_path ON folder_labels(folder_path);
CREATE INDEX idx_folder_labels_label_id ON folder_labels(label_id);
```

### Phase 2: Backward Compatibility
- Existing queries continue to work (no changes to `virtual_machines` table)
- New tables are optional (empty by default)
- Application checks for table existence before using labels

---

## Performance Considerations

### Indexes
- ✅ All foreign keys indexed
- ✅ Frequently queried columns indexed
- ✅ Composite unique constraints for data integrity

### Query Optimization
- Use `EXISTS` for membership checks (faster than JOIN)
- Batch inserts for bulk label assignments
- Consider materialized view for "VM with all effective labels" if needed

### Storage Estimates
- **Labels**: ~100 bytes/row → 10K labels = ~1 MB
- **VMLabels**: ~50 bytes/row → 100K VMs × 5 labels = ~25 MB
- **FolderLabels**: ~70 bytes/row → 1K folders × 3 labels = ~210 KB
- **Total**: ~26 MB for typical deployment

---

## Design Review Checklist

### ✅ Schema Design
- [x] Proper normalization (3NF)
- [x] Appropriate indexes for query patterns
- [x] Cascade delete rules defined
- [x] Unique constraints prevent duplicates
- [x] Nullable fields properly marked
- [x] String lengths appropriate for use case

### ✅ Data Integrity
- [x] Foreign key constraints
- [x] Unique constraints on natural keys
- [x] Timestamp tracking (created/updated)
- [x] Audit trail (assigned_by)

### ✅ Compatibility
- [x] No changes to existing tables
- [x] Uses existing `folder` column
- [x] Optional feature (backward compatible)
- [x] Follows existing SQLAlchemy 2.0 patterns

### ✅ Performance
- [x] Appropriate indexes
- [x] Reasonable storage overhead
- [x] Efficient query patterns

---

## Next Steps

1. ✅ Create feature branch: `feature/vm-folder-labelling`
2. ✅ Update `src/models.py` with new tables
3. ✅ Create database migration script
4. ✅ Implement label service layer
5. ✅ Add CLI commands
6. ✅ Build UI components
7. ✅ Write tests
8. ✅ Update documentation

---

## Sign-off

**Schema Approved**: Ready for implementation
**Date**: 2025-10-28
**Version**: 0.5.0 (feature branch)
