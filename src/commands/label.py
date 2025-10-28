"""CLI commands for label management."""

import click
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from tabulate import tabulate

from src.services.label_service import LabelService
from src.models import VirtualMachine


def get_label_service(db_url: str) -> LabelService:
    """Create and return a LabelService instance."""
    engine = create_engine(db_url, echo=False)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    return LabelService(session)


@click.group()
def label():
    """Manage VM and folder labels."""
    pass


# ============================================================================
# Label Definition Commands
# ============================================================================

@label.command('create')
@click.argument('key')
@click.argument('value')
@click.option('--description', help='Label description')
@click.option('--color', help='Hex color code (e.g., #FF0000)')
@click.option('--db-url', default='sqlite:///data/vmware_inventory.db', 
              help='Database URL', show_default=True)
def create_label(key: str, value: str, description: str, color: str, db_url: str):
    """Create a new label definition."""
    try:
        service = get_label_service(db_url)
        label = service.create_label(key, value, description, color)
        
        click.echo(f"✅ Label created: {label.key}={label.value}")
        if description:
            click.echo(f"   Description: {description}")
        if color:
            click.echo(f"   Color: {color}")
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()


@label.command('list')
@click.option('--key', help='Filter by label key')
@click.option('--db-url', default='sqlite:///data/vmware_inventory.db',
              help='Database URL', show_default=True)
def list_labels(key: str, db_url: str):
    """List all label definitions."""
    try:
        service = get_label_service(db_url)
        labels = service.list_labels(key)
        
        if not labels:
            click.echo("No labels found.")
            return
        
        # Prepare table data
        table_data = []
        for lbl in labels:
            table_data.append([
                lbl.id,
                lbl.key,
                lbl.value,
                lbl.description or '',
                lbl.color or ''
            ])
        
        # Display table
        headers = ['ID', 'Key', 'Value', 'Description', 'Color']
        click.echo(f"\n📋 Labels ({len(labels)} total):\n")
        click.echo(tabulate(table_data, headers=headers, tablefmt='simple'))
        click.echo()
        
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()


@label.command('delete')
@click.argument('label_id', type=int)
@click.option('--db-url', default='sqlite:///data/vmware_inventory.db',
              help='Database URL', show_default=True)
@click.confirmation_option(prompt='Are you sure you want to delete this label?')
def delete_label(label_id: int, db_url: str):
    """Delete a label definition (cascades to assignments)."""
    try:
        service = get_label_service(db_url)
        success = service.delete_label(label_id)
        
        if success:
            click.echo(f"✅ Label {label_id} deleted")
        else:
            click.echo(f"❌ Label {label_id} not found", err=True)
            
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()


@label.command('keys')
@click.option('--db-url', default='sqlite:///data/vmware_inventory.db',
              help='Database URL', show_default=True)
def list_keys(db_url: str):
    """List all label keys."""
    try:
        service = get_label_service(db_url)
        keys = service.get_label_keys()
        
        if not keys:
            click.echo("No label keys found.")
            return
        
        click.echo(f"\n🏷️  Label Keys ({len(keys)}):\n")
        for key in keys:
            values = service.get_label_values(key)
            click.echo(f"  • {key} ({len(values)} values)")
        click.echo()
        
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()


# ============================================================================
# VM Label Commands
# ============================================================================

@label.command('assign-vm')
@click.argument('vm_name')
@click.argument('key')
@click.argument('value')
@click.option('--by', help='Assigned by (user name)')
@click.option('--db-url', default='sqlite:///data/vmware_inventory.db',
              help='Database URL', show_default=True)
def assign_vm_label(vm_name: str, key: str, value: str, by: str, db_url: str):
    """Assign a label to a VM."""
    try:
        service = get_label_service(db_url)
        
        # Find VM
        vm = service.session.query(VirtualMachine).filter(
            VirtualMachine.vm == vm_name
        ).first()
        
        if not vm:
            click.echo(f"❌ VM not found: {vm_name}", err=True)
            raise click.Abort()
        
        # Get or create label
        label = service.get_label_by_key_value(key, value)
        if not label:
            label = service.create_label(key, value)
            click.echo(f"ℹ️  Created new label: {key}={value}")
        
        # Assign to VM
        service.assign_vm_label(vm.id, label.id, assigned_by=by)
        click.echo(f"✅ Label assigned: {vm_name} → {key}={value}")
        
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()


@label.command('remove-vm')
@click.argument('vm_name')
@click.argument('key')
@click.argument('value')
@click.option('--db-url', default='sqlite:///data/vmware_inventory.db',
              help='Database URL', show_default=True)
def remove_vm_label(vm_name: str, key: str, value: str, db_url: str):
    """Remove a label from a VM."""
    try:
        service = get_label_service(db_url)
        
        # Find VM
        vm = service.session.query(VirtualMachine).filter(
            VirtualMachine.vm == vm_name
        ).first()
        
        if not vm:
            click.echo(f"❌ VM not found: {vm_name}", err=True)
            raise click.Abort()
        
        # Get label
        label = service.get_label_by_key_value(key, value)
        if not label:
            click.echo(f"❌ Label not found: {key}={value}", err=True)
            raise click.Abort()
        
        # Remove from VM
        success = service.remove_vm_label(vm.id, label.id)
        if success:
            click.echo(f"✅ Label removed: {vm_name} → {key}={value}")
        else:
            click.echo(f"❌ Label was not assigned to VM", err=True)
            
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()


@label.command('list-vm')
@click.argument('vm_name')
@click.option('--inherited/--no-inherited', default=True,
              help='Include inherited labels')
@click.option('--db-url', default='sqlite:///data/vmware_inventory.db',
              help='Database URL', show_default=True)
def list_vm_labels(vm_name: str, inherited: bool, db_url: str):
    """List all labels for a VM."""
    try:
        service = get_label_service(db_url)
        
        # Find VM
        vm = service.session.query(VirtualMachine).filter(
            VirtualMachine.vm == vm_name
        ).first()
        
        if not vm:
            click.echo(f"❌ VM not found: {vm_name}", err=True)
            raise click.Abort()
        
        # Get labels
        labels = service.get_vm_labels(vm.id, include_inherited=inherited)
        
        if not labels:
            click.echo(f"No labels found for VM: {vm_name}")
            return
        
        # Prepare table
        table_data = []
        for lbl in labels:
            source = "Direct" if not lbl['inherited'] else f"Folder: {lbl['source_folder']}"
            table_data.append([
                lbl['key'],
                lbl['value'],
                source,
                lbl['assigned_by'] or ''
            ])
        
        click.echo(f"\n🏷️  Labels for VM: {vm_name}\n")
        click.echo(tabulate(table_data, headers=['Key', 'Value', 'Source', 'Assigned By'], tablefmt='simple'))
        click.echo()
        
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()


@label.command('find-vms')
@click.argument('key')
@click.argument('value')
@click.option('--db-url', default='sqlite:///data/vmware_inventory.db',
              help='Database URL', show_default=True)
def find_vms_with_label(key: str, value: str, db_url: str):
    """Find all VMs with a specific label."""
    try:
        service = get_label_service(db_url)
        vms = service.get_vms_with_label(key, value)
        
        if not vms:
            click.echo(f"No VMs found with label: {key}={value}")
            return
        
        click.echo(f"\n🖥️  VMs with label {key}={value} ({len(vms)} found):\n")
        for vm in vms:
            folder = vm.folder or '(no folder)'
            click.echo(f"  • {vm.vm:<40} {folder}")
        click.echo()
        
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()


# ============================================================================
# Folder Label Commands
# ============================================================================

@label.command('assign-folder')
@click.argument('folder_path')
@click.argument('key')
@click.argument('value')
@click.option('--inherit-vms/--no-inherit-vms', default=True,
              help='Apply label to VMs in folder')
@click.option('--inherit-subfolders/--no-inherit-subfolders', default=False,
              help='Apply to subfolders recursively')
@click.option('--by', help='Assigned by (user name)')
@click.option('--db-url', default='sqlite:///data/vmware_inventory.db',
              help='Database URL', show_default=True)
def assign_folder_label(folder_path: str, key: str, value: str, 
                       inherit_vms: bool, inherit_subfolders: bool,
                       by: str, db_url: str):
    """Assign a label to a folder."""
    try:
        service = get_label_service(db_url)
        
        # Get or create label
        label = service.get_label_by_key_value(key, value)
        if not label:
            label = service.create_label(key, value)
            click.echo(f"ℹ️  Created new label: {key}={value}")
        
        # Assign to folder
        service.assign_folder_label(
            folder_path, 
            label.id, 
            assigned_by=by,
            inherit_to_vms=inherit_vms,
            inherit_to_subfolders=inherit_subfolders
        )
        
        click.echo(f"✅ Label assigned to folder: {folder_path} → {key}={value}")
        if inherit_vms:
            click.echo(f"   ✓ Applied to VMs in folder")
        if inherit_subfolders:
            click.echo(f"   ✓ Applied to subfolders")
            
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()


@label.command('remove-folder')
@click.argument('folder_path')
@click.argument('key')
@click.argument('value')
@click.option('--keep-inherited/--remove-inherited', default=False,
              help='Keep inherited labels on VMs')
@click.option('--db-url', default='sqlite:///data/vmware_inventory.db',
              help='Database URL', show_default=True)
def remove_folder_label(folder_path: str, key: str, value: str, 
                       keep_inherited: bool, db_url: str):
    """Remove a label from a folder."""
    try:
        service = get_label_service(db_url)
        
        # Get label
        label = service.get_label_by_key_value(key, value)
        if not label:
            click.echo(f"❌ Label not found: {key}={value}", err=True)
            raise click.Abort()
        
        # Remove from folder
        success = service.remove_folder_label(
            folder_path, 
            label.id,
            remove_inherited=not keep_inherited
        )
        
        if success:
            click.echo(f"✅ Label removed from folder: {folder_path} → {key}={value}")
            if not keep_inherited:
                click.echo(f"   ✓ Removed inherited labels from VMs")
        else:
            click.echo(f"❌ Label was not assigned to folder", err=True)
            
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()


@label.command('list-folder')
@click.argument('folder_path')
@click.option('--db-url', default='sqlite:///data/vmware_inventory.db',
              help='Database URL', show_default=True)
def list_folder_labels(folder_path: str, db_url: str):
    """List all labels for a folder."""
    try:
        service = get_label_service(db_url)
        labels = service.get_folder_labels(folder_path)
        
        if not labels:
            click.echo(f"No labels found for folder: {folder_path}")
            return
        
        # Get folder stats
        stats = service.get_folder_stats(folder_path)
        
        click.echo(f"\n📁 Folder: {folder_path}")
        click.echo(f"   VMs: {stats['vm_count']}, Storage: {stats['storage_gib']:.1f} GiB\n")
        
        # Prepare table
        table_data = []
        for lbl in labels:
            inherit = "VMs" if lbl['inherit_to_vms'] else "-"
            if lbl['inherit_to_subfolders']:
                inherit += " + Subfolders"
            
            table_data.append([
                lbl['key'],
                lbl['value'],
                inherit,
                lbl['assigned_by'] or ''
            ])
        
        click.echo(tabulate(table_data, headers=['Key', 'Value', 'Inheritance', 'Assigned By'], tablefmt='simple'))
        click.echo()
        
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()


@label.command('find-folders')
@click.argument('key')
@click.argument('value')
@click.option('--db-url', default='sqlite:///data/vmware_inventory.db',
              help='Database URL', show_default=True)
def find_folders_with_label(key: str, value: str, db_url: str):
    """Find all folders with a specific label."""
    try:
        service = get_label_service(db_url)
        folders = service.get_folders_with_label(key, value)
        
        if not folders:
            click.echo(f"No folders found with label: {key}={value}")
            return
        
        click.echo(f"\n📁 Folders with label {key}={value} ({len(folders)} found):\n")
        for folder in folders:
            stats = service.get_folder_stats(folder)
            click.echo(f"  • {folder:<50} ({stats['vm_count']} VMs)")
        click.echo()
        
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()


# ============================================================================
# Folder Utility Commands
# ============================================================================

@label.command('list-folders')
@click.option('--db-url', default='sqlite:///data/vmware_inventory.db',
              help='Database URL', show_default=True)
def list_all_folders(db_url: str):
    """List all folders from VMs."""
    try:
        service = get_label_service(db_url)
        folders = service.get_all_folders()
        
        if not folders:
            click.echo("No folders found.")
            return
        
        click.echo(f"\n📁 All Folders ({len(folders)}):\n")
        for folder in folders:
            stats = service.get_folder_stats(folder)
            click.echo(f"  {folder:<60} ({stats['vm_count']} VMs, {stats['label_count']} labels)")
        click.echo()
        
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()


@label.command('sync-inherited')
@click.option('--folder', help='Sync only specific folder')
@click.option('--db-url', default='sqlite:///data/vmware_inventory.db',
              help='Database URL', show_default=True)
def sync_inherited_labels(folder: str, db_url: str):
    """Re-sync inherited labels from folders to VMs."""
    try:
        service = get_label_service(db_url)
        
        if folder:
            click.echo(f"🔄 Syncing inherited labels for folder: {folder}")
        else:
            click.echo(f"🔄 Syncing all inherited labels...")
        
        service.sync_inherited_labels(folder)
        
        click.echo(f"✅ Inherited labels synced successfully")
        
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()
