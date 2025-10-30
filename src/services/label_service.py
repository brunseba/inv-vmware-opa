"""Label service layer for managing VM and folder labels."""

from datetime import datetime
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from src.models import Label, VMLabel, FolderLabel, VirtualMachine


class LabelService:
    """Service for managing labels and their assignments."""
    
    def __init__(self, session: Session):
        self.session = session
    
    # ========================================================================
    # Label CRUD Operations
    # ========================================================================
    
    def create_label(self, key: str, value: str, description: str = None, 
                    color: str = None) -> Label:
        """Create a new label definition."""
        # Check if label already exists
        existing = self.session.query(Label).filter(
            Label.key == key,
            Label.value == value
        ).first()
        
        if existing:
            return existing
        
        label = Label(
            key=key,
            value=value,
            description=description,
            color=color
        )
        self.session.add(label)
        self.session.commit()
        return label
    
    def get_label(self, label_id: int) -> Optional[Label]:
        """Get a label by ID."""
        return self.session.query(Label).filter(Label.id == label_id).first()
    
    def get_label_by_key_value(self, key: str, value: str) -> Optional[Label]:
        """Get a label by key-value pair."""
        return self.session.query(Label).filter(
            Label.key == key,
            Label.value == value
        ).first()
    
    def list_labels(self, key: str = None) -> List[Label]:
        """List all labels, optionally filtered by key."""
        query = self.session.query(Label)
        if key:
            query = query.filter(Label.key == key)
        return query.order_by(Label.key, Label.value).all()
    
    def get_label_keys(self) -> List[str]:
        """Get all unique label keys."""
        result = self.session.query(Label.key).distinct().order_by(Label.key).all()
        return [r[0] for r in result]
    
    def get_label_values(self, key: str) -> List[str]:
        """Get all values for a specific label key."""
        result = self.session.query(Label.value).filter(
            Label.key == key
        ).distinct().order_by(Label.value).all()
        return [r[0] for r in result]
    
    def update_label(self, label_id: int, description: str = None, 
                    color: str = None) -> Optional[Label]:
        """Update label description and/or color."""
        label = self.get_label(label_id)
        if not label:
            return None
        
        if description is not None:
            label.description = description
        if color is not None:
            label.color = color
        label.updated_at = datetime.utcnow()
        
        self.session.commit()
        return label
    
    def delete_label(self, label_id: int) -> bool:
        """Delete a label (cascades to VM and folder assignments)."""
        label = self.get_label(label_id)
        if not label:
            return False
        
        self.session.delete(label)
        self.session.commit()
        return True
    
    # ========================================================================
    # VM Label Operations
    # ========================================================================
    
    def assign_vm_label(self, vm_id: int, label_id: int, assigned_by: str = None,
                       inherited: bool = False, source_folder: str = None) -> VMLabel:
        """Assign a label to a VM."""
        # Check if already assigned
        existing = self.session.query(VMLabel).filter(
            VMLabel.vm_id == vm_id,
            VMLabel.label_id == label_id
        ).first()
        
        if existing:
            return existing
        
        vm_label = VMLabel(
            vm_id=vm_id,
            label_id=label_id,
            assigned_by=assigned_by,
            inherited_from_folder=inherited,
            source_folder_path=source_folder
        )
        self.session.add(vm_label)
        self.session.commit()
        return vm_label
    
    def remove_vm_label(self, vm_id: int, label_id: int) -> bool:
        """Remove a label from a VM."""
        vm_label = self.session.query(VMLabel).filter(
            VMLabel.vm_id == vm_id,
            VMLabel.label_id == label_id
        ).first()
        
        if not vm_label:
            return False
        
        self.session.delete(vm_label)
        self.session.commit()
        return True
    
    def get_vm_labels(self, vm_id: int, include_inherited: bool = True) -> List[Dict]:
        """Get all labels for a VM with details."""
        query = self.session.query(Label, VMLabel).join(
            VMLabel, Label.id == VMLabel.label_id
        ).filter(VMLabel.vm_id == vm_id)
        
        if not include_inherited:
            query = query.filter(VMLabel.inherited_from_folder == False)
        
        results = query.all()
        
        labels = []
        for label, vm_label in results:
            labels.append({
                'label_id': label.id,
                'key': label.key,
                'value': label.value,
                'description': label.description,
                'color': label.color,
                'inherited': vm_label.inherited_from_folder,
                'source_folder': vm_label.source_folder_path,
                'assigned_at': vm_label.assigned_at,
                'assigned_by': vm_label.assigned_by
            })
        
        return labels
    
    def get_vms_with_label(self, key: str, value: str) -> List[VirtualMachine]:
        """Get all VMs that have a specific label."""
        label = self.get_label_by_key_value(key, value)
        if not label:
            return []
        
        return self.session.query(VirtualMachine).join(
            VMLabel, VirtualMachine.id == VMLabel.vm_id
        ).filter(VMLabel.label_id == label.id).all()
    
    # ========================================================================
    # Folder Label Operations
    # ========================================================================
    
    def assign_folder_label(self, folder_path: str, label_id: int,
                           assigned_by: str = None, inherit_to_vms: bool = True,
                           inherit_to_subfolders: bool = False) -> FolderLabel:
        """Assign a label to a folder."""
        # Check if already assigned
        existing = self.session.query(FolderLabel).filter(
            FolderLabel.folder_path == folder_path,
            FolderLabel.label_id == label_id
        ).first()
        
        if existing:
            # Update inheritance flags
            existing.inherit_to_vms = inherit_to_vms
            existing.inherit_to_subfolders = inherit_to_subfolders
            self.session.commit()
            
            # Apply inheritance
            if inherit_to_vms:
                self._apply_folder_label_to_vms(folder_path, label_id, inherit_to_subfolders)
            
            return existing
        
        folder_label = FolderLabel(
            folder_path=folder_path,
            label_id=label_id,
            assigned_by=assigned_by,
            inherit_to_vms=inherit_to_vms,
            inherit_to_subfolders=inherit_to_subfolders
        )
        self.session.add(folder_label)
        self.session.commit()
        
        # Apply inheritance if enabled
        if inherit_to_vms:
            self._apply_folder_label_to_vms(folder_path, label_id, inherit_to_subfolders)
        
        return folder_label
    
    def remove_folder_label(self, folder_path: str, label_id: int,
                           remove_inherited: bool = True) -> bool:
        """Remove a label from a folder."""
        folder_label = self.session.query(FolderLabel).filter(
            FolderLabel.folder_path == folder_path,
            FolderLabel.label_id == label_id
        ).first()
        
        if not folder_label:
            return False
        
        # Optionally remove inherited labels from VMs
        if remove_inherited:
            self._remove_inherited_labels_from_vms(folder_path, label_id, 
                                                   folder_label.inherit_to_subfolders)
        
        self.session.delete(folder_label)
        self.session.commit()
        return True
    
    def get_folder_labels(self, folder_path: str) -> List[Dict]:
        """Get all labels for a folder."""
        results = self.session.query(Label, FolderLabel).join(
            FolderLabel, Label.id == FolderLabel.label_id
        ).filter(FolderLabel.folder_path == folder_path).all()
        
        labels = []
        for label, folder_label in results:
            labels.append({
                'label_id': label.id,
                'key': label.key,
                'value': label.value,
                'description': label.description,
                'color': label.color,
                'inherit_to_vms': folder_label.inherit_to_vms,
                'inherit_to_subfolders': folder_label.inherit_to_subfolders,
                'assigned_at': folder_label.assigned_at,
                'assigned_by': folder_label.assigned_by
            })
        
        return labels
    
    def get_folders_with_label(self, key: str, value: str) -> List[str]:
        """Get all folder paths that have a specific label."""
        label = self.get_label_by_key_value(key, value)
        if not label:
            return []
        
        results = self.session.query(FolderLabel.folder_path).filter(
            FolderLabel.label_id == label.id
        ).all()
        
        return [r[0] for r in results]
    
    # ========================================================================
    # Folder Operations
    # ========================================================================
    
    def get_all_folders(self) -> List[str]:
        """Get all unique folder paths from VMs."""
        results = self.session.query(VirtualMachine.folder).filter(
            VirtualMachine.folder.isnot(None)
        ).distinct().order_by(VirtualMachine.folder).all()
        
        return [r[0] for r in results]
    
    def get_folder_stats(self, folder_path: str) -> Dict:
        """Get statistics for a folder."""
        # VM count (exact match)
        vm_count = self.session.query(func.count(VirtualMachine.id)).filter(
            VirtualMachine.folder == folder_path
        ).scalar() or 0
        
        # Storage sum
        storage_sum = self.session.query(
            func.sum(VirtualMachine.in_use_mib)
        ).filter(VirtualMachine.folder == folder_path).scalar() or 0
        
        # Labels
        labels = self.get_folder_labels(folder_path)
        
        return {
            'folder_path': folder_path,
            'vm_count': vm_count,
            'storage_gib': storage_sum / 1024,
            'label_count': len(labels),
            'labels': labels
        }
    
    # ========================================================================
    # Label Inheritance Logic
    # ========================================================================
    
    def _apply_folder_label_to_vms(self, folder_path: str, label_id: int,
                                   include_subfolders: bool):
        """Apply a folder label to all VMs in the folder."""
        # Build VM query
        if include_subfolders:
            # Match folder and all subfolders
            vms = self.session.query(VirtualMachine).filter(
                or_(
                    VirtualMachine.folder == folder_path,
                    VirtualMachine.folder.like(f"{folder_path}/%")
                )
            ).all()
        else:
            # Exact match only
            vms = self.session.query(VirtualMachine).filter(
                VirtualMachine.folder == folder_path
            ).all()
        
        # Assign label to each VM (if not already assigned)
        for vm in vms:
            try:
                self.assign_vm_label(
                    vm_id=vm.id,
                    label_id=label_id,
                    assigned_by='system',
                    inherited=True,
                    source_folder=folder_path
                )
            except Exception:
                # Skip if already assigned (UNIQUE constraint)
                self.session.rollback()
                continue
    
    def _remove_inherited_labels_from_vms(self, folder_path: str, label_id: int,
                                         include_subfolders: bool):
        """Remove inherited labels from VMs in a folder."""
        query = self.session.query(VMLabel).join(
            VirtualMachine, VMLabel.vm_id == VirtualMachine.id
        ).filter(
            VMLabel.label_id == label_id,
            VMLabel.inherited_from_folder == True,
            VMLabel.source_folder_path == folder_path
        )
        
        if include_subfolders:
            query = query.filter(
                or_(
                    VirtualMachine.folder == folder_path,
                    VirtualMachine.folder.like(f"{folder_path}/%")
                )
            )
        else:
            query = query.filter(VirtualMachine.folder == folder_path)
        
        query.delete(synchronize_session=False)
        self.session.commit()
    
    def sync_inherited_labels(self, folder_path: str = None):
        """Re-sync inherited labels from folders to VMs."""
        # Get all folder labels or just for one folder
        if folder_path:
            folder_labels = self.session.query(FolderLabel).filter(
                FolderLabel.folder_path == folder_path,
                FolderLabel.inherit_to_vms == True
            ).all()
        else:
            folder_labels = self.session.query(FolderLabel).filter(
                FolderLabel.inherit_to_vms == True
            ).all()
        
        # Reapply each folder label
        for fl in folder_labels:
            self._apply_folder_label_to_vms(
                fl.folder_path,
                fl.label_id,
                fl.inherit_to_subfolders
            )
        
        self.session.commit()
    
    # ========================================================================
    # Helper Methods
    # ========================================================================
    
    def get_folder_hierarchy(self, folder_path: str) -> List[str]:
        """Get folder hierarchy from path (parent to child)."""
        if not folder_path:
            return []
        
        parts = folder_path.strip('/').split('/')
        hierarchy = []
        for i in range(1, len(parts) + 1):
            hierarchy.append('/' + '/'.join(parts[:i]))
        return hierarchy
    
    def get_vm_effective_labels(self, vm_id: int) -> Dict[str, Dict]:
        """
        Get all effective labels for a VM including inherited ones.
        Direct labels override inherited ones with the same key.
        """
        # Get VM
        vm = self.session.query(VirtualMachine).filter(
            VirtualMachine.id == vm_id
        ).first()
        
        if not vm:
            return {}
        
        labels = {}
        
        # Get direct labels first (highest priority)
        direct_labels = self.get_vm_labels(vm_id, include_inherited=False)
        for label in direct_labels:
            labels[label['key']] = {
                'value': label['value'],
                'label_id': label['label_id'],
                'type': 'direct',
                'source': 'vm',
                'color': label['color']
            }
        
        # Get folder hierarchy labels (if VM has folder)
        if vm.folder:
            hierarchy = self.get_folder_hierarchy(vm.folder)
            # Reverse to go from most specific to least specific
            for folder_path in reversed(hierarchy):
                folder_labels = self.get_folder_labels(folder_path)
                for fl in folder_labels:
                    if fl['inherit_to_vms'] and fl['key'] not in labels:
                        labels[fl['key']] = {
                            'value': fl['value'],
                            'label_id': fl['label_id'],
                            'type': 'inherited',
                            'source': folder_path,
                            'color': fl['color']
                        }
        
        return labels
    
    # ========================================================================
    # VM Retrieval by Categories (OS and Resources)
    # ========================================================================
    
    def get_vms_by_os_category(self, os_pattern: str = None, 
                               os_family: str = None) -> List[VirtualMachine]:
        """Get VMs filtered by operating system.
        
        Args:
            os_pattern: SQL LIKE pattern for os_config (e.g., 'Windows%', '%Linux%')
            os_family: Predefined OS family ('windows', 'linux', 'unix', 'other')
            
        Returns:
            List of VirtualMachine objects matching criteria
            
        Example:
            # Get all Windows VMs
            windows_vms = service.get_vms_by_os_category(os_family='windows')
            
            # Get specific Linux distro
            ubuntu_vms = service.get_vms_by_os_category(os_pattern='%Ubuntu%')
        """
        query = self.session.query(VirtualMachine)
        
        if os_pattern:
            query = query.filter(VirtualMachine.os_config.like(os_pattern))
        elif os_family:
            # Predefined patterns for common OS families
            if os_family.lower() == 'windows':
                query = query.filter(
                    or_(
                        VirtualMachine.os_config.like('%Windows%'),
                        VirtualMachine.os_config.like('%Microsoft%')
                    )
                )
            elif os_family.lower() == 'linux':
                query = query.filter(
                    or_(
                        VirtualMachine.os_config.like('%Linux%'),
                        VirtualMachine.os_config.like('%Ubuntu%'),
                        VirtualMachine.os_config.like('%Red Hat%'),
                        VirtualMachine.os_config.like('%CentOS%'),
                        VirtualMachine.os_config.like('%Debian%'),
                        VirtualMachine.os_config.like('%SUSE%'),
                        VirtualMachine.os_config.like('%Fedora%')
                    )
                )
            elif os_family.lower() == 'unix':
                query = query.filter(
                    or_(
                        VirtualMachine.os_config.like('%Solaris%'),
                        VirtualMachine.os_config.like('%AIX%'),
                        VirtualMachine.os_config.like('%HP-UX%'),
                        VirtualMachine.os_config.like('%BSD%')
                    )
                )
            elif os_family.lower() == 'other':
                query = query.filter(
                    VirtualMachine.os_config.isnot(None),
                    ~VirtualMachine.os_config.like('%Windows%'),
                    ~VirtualMachine.os_config.like('%Linux%'),
                    ~VirtualMachine.os_config.like('%Solaris%')
                )
        
        return query.order_by(VirtualMachine.vm).all()
    
    def get_vms_by_resource_criteria(self,
                                     min_cpus: int = None,
                                     max_cpus: int = None,
                                     min_memory_gb: float = None,
                                     max_memory_gb: float = None,
                                     min_storage_gb: float = None,
                                     max_storage_gb: float = None,
                                     min_nics: int = None,
                                     max_nics: int = None,
                                     min_disks: int = None,
                                     max_disks: int = None) -> List[VirtualMachine]:
        """Get VMs filtered by resource specifications.
        
        Args:
            min_cpus: Minimum vCPUs (INTEGER)
            max_cpus: Maximum vCPUs (INTEGER)
            min_memory_gb: Minimum memory in GB (INTEGER in MB in DB)
            max_memory_gb: Maximum memory in GB (INTEGER in MB in DB)
            min_storage_gb: Minimum provisioned storage in GB
            max_storage_gb: Maximum provisioned storage in GB
            min_nics: Minimum number of NICs (INTEGER)
            max_nics: Maximum number of NICs (INTEGER)
            min_disks: Minimum number of disks (INTEGER)
            max_disks: Maximum number of disks (INTEGER)
            
        Returns:
            List of VirtualMachine objects matching criteria
            
        Example:
            # Get large VMs (8+ CPUs, 32+ GB RAM)
            large_vms = service.get_vms_by_resource_criteria(
                min_cpus=8,
                min_memory_gb=32
            )
            
            # Get VMs with multiple NICs and many disks
            complex_vms = service.get_vms_by_resource_criteria(
                min_nics=2,
                min_disks=3
            )
        """
        query = self.session.query(VirtualMachine)
        
        # CPU filters (INTEGER)
        if min_cpus is not None:
            query = query.filter(VirtualMachine.cpus >= min_cpus)
        if max_cpus is not None:
            query = query.filter(VirtualMachine.cpus <= max_cpus)
        
        # Memory filters (INTEGER in MB in database)
        if min_memory_gb is not None:
            query = query.filter(VirtualMachine.memory >= int(min_memory_gb * 1024))
        if max_memory_gb is not None:
            query = query.filter(VirtualMachine.memory <= int(max_memory_gb * 1024))
        
        # Storage filters (convert GB to MiB for database)
        if min_storage_gb is not None:
            query = query.filter(VirtualMachine.provisioned_mib >= min_storage_gb * 1024)
        if max_storage_gb is not None:
            query = query.filter(VirtualMachine.provisioned_mib <= max_storage_gb * 1024)
        
        # NICs filters (INTEGER)
        if min_nics is not None:
            query = query.filter(VirtualMachine.nics >= min_nics)
        if max_nics is not None:
            query = query.filter(VirtualMachine.nics <= max_nics)
        
        # Disks filters (INTEGER)
        if min_disks is not None:
            query = query.filter(VirtualMachine.disks >= min_disks)
        if max_disks is not None:
            query = query.filter(VirtualMachine.disks <= max_disks)
        
        return query.order_by(VirtualMachine.vm).all()
    
    def get_vms_by_resource_category(self, category: str) -> List[VirtualMachine]:
        """Get VMs by predefined resource size categories.
        
        Args:
            category: One of 'small', 'medium', 'large', 'xlarge'
            
        Returns:
            List of VirtualMachine objects
            
        Categories:
            - small: 1-2 vCPUs, up to 4 GB RAM
            - medium: 3-4 vCPUs, 4-16 GB RAM
            - large: 5-8 vCPUs, 16-32 GB RAM
            - xlarge: 9+ vCPUs, 32+ GB RAM
        """
        if category == 'small':
            return self.get_vms_by_resource_criteria(max_cpus=2, max_memory_gb=4)
        elif category == 'medium':
            return self.get_vms_by_resource_criteria(min_cpus=3, max_cpus=4, 
                                                    min_memory_gb=4, max_memory_gb=16)
        elif category == 'large':
            return self.get_vms_by_resource_criteria(min_cpus=5, max_cpus=8,
                                                    min_memory_gb=16, max_memory_gb=32)
        elif category == 'xlarge':
            return self.get_vms_by_resource_criteria(min_cpus=9, min_memory_gb=32)
        else:
            return []
    
    def batch_assign_label_to_vms(self, vm_ids: List[int], label_id: int,
                                  assigned_by: str = None) -> Tuple[int, int]:
        """Assign a label to multiple VMs in batch.
        
        Args:
            vm_ids: List of VM IDs
            label_id: Label ID to assign
            assigned_by: Who assigned the label
            
        Returns:
            Tuple of (successful_count, failed_count)
        """
        successful = 0
        failed = 0
        
        for vm_id in vm_ids:
            try:
                self.assign_vm_label(vm_id, label_id, assigned_by=assigned_by)
                successful += 1
            except Exception:
                self.session.rollback()
                failed += 1
        
        return successful, failed
    
    def get_vms_by_network_complexity(self, complexity: str) -> List[VirtualMachine]:
        """Get VMs by network complexity based on NIC count.
        
        Args:
            complexity: One of 'simple', 'standard', 'complex'
            
        Returns:
            List of VirtualMachine objects
            
        Categories:
            - simple: 1 NIC (single network)
            - standard: 2 NICs (typical dual-homed)
            - complex: 3+ NICs (multi-network)
        """
        if complexity == 'simple':
            return self.get_vms_by_resource_criteria(max_nics=1)
        elif complexity == 'standard':
            return self.get_vms_by_resource_criteria(min_nics=2, max_nics=2)
        elif complexity == 'complex':
            return self.get_vms_by_resource_criteria(min_nics=3)
        else:
            return []
    
    def get_vms_by_storage_complexity(self, complexity: str) -> List[VirtualMachine]:
        """Get VMs by storage complexity based on disk count.
        
        Args:
            complexity: One of 'simple', 'standard', 'complex'
            
        Returns:
            List of VirtualMachine objects
            
        Categories:
            - simple: 1 disk (single volume)
            - standard: 2-3 disks (OS + data)
            - complex: 4+ disks (multi-volume)
        """
        if complexity == 'simple':
            return self.get_vms_by_resource_criteria(max_disks=1)
        elif complexity == 'standard':
            return self.get_vms_by_resource_criteria(min_disks=2, max_disks=3)
        elif complexity == 'complex':
            return self.get_vms_by_resource_criteria(min_disks=4)
        else:
            return []
    
    def get_vm_counts_by_criteria(self, os_pattern: str = None, 
                                  resource_category: str = None) -> Dict:
        """Get count of VMs matching various criteria.
        
        Args:
            os_pattern: OS pattern to filter (not currently used, reserved for future)
            resource_category: Resource size category (not currently used, reserved for future)
            
        Returns:
            Dictionary with counts by criteria organized by category
        """
        counts = {
            'os_family': {},
            'resource_size': {},
            'network_complexity': {},
            'storage_complexity': {}
        }
        
        # OS family counts
        counts['os_family']['windows'] = len(self.get_vms_by_os_category(os_family='windows'))
        counts['os_family']['linux'] = len(self.get_vms_by_os_category(os_family='linux'))
        counts['os_family']['unix'] = len(self.get_vms_by_os_category(os_family='unix'))
        
        # Resource size counts (CPUs + Memory)
        counts['resource_size']['small'] = len(self.get_vms_by_resource_category('small'))
        counts['resource_size']['medium'] = len(self.get_vms_by_resource_category('medium'))
        counts['resource_size']['large'] = len(self.get_vms_by_resource_category('large'))
        counts['resource_size']['xlarge'] = len(self.get_vms_by_resource_category('xlarge'))
        
        # Network complexity counts (NICs)
        counts['network_complexity']['simple'] = len(self.get_vms_by_network_complexity('simple'))
        counts['network_complexity']['standard'] = len(self.get_vms_by_network_complexity('standard'))
        counts['network_complexity']['complex'] = len(self.get_vms_by_network_complexity('complex'))
        
        # Storage complexity counts (Disks)
        counts['storage_complexity']['simple'] = len(self.get_vms_by_storage_complexity('simple'))
        counts['storage_complexity']['standard'] = len(self.get_vms_by_storage_complexity('standard'))
        counts['storage_complexity']['complex'] = len(self.get_vms_by_storage_complexity('complex'))
        
        return counts
