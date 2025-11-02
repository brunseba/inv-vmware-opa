"""CLI for VMware inventory management."""

import click
import subprocess
import sys
from pathlib import Path
from .loader import load_excel_to_db
from .commands.label import label
from .commands.anonymize import anonymize


@click.group()
@click.version_option(version="0.8.0")
def cli():
    """VMware inventory management CLI."""
    pass


# Register command groups
cli.add_command(label)
cli.add_command(anonymize)


@cli.command()
@click.argument("excel_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--db-url",
    default="sqlite:///data/vmware_inventory.db",
    help="Database URL (default: sqlite:///data/vmware_inventory.db)",
    show_default=True,
)
@click.option(
    "--clear",
    is_flag=True,
    help="Clear existing data before loading",
)
@click.option(
    "--sheet",
    default="Sheet1",
    help="Excel sheet name or index to load",
    show_default=True,
)
@click.option(
    "--list-sheets",
    is_flag=True,
    help="List available sheets and exit",
)
def load(excel_file: Path, db_url: str, clear: bool, sheet: str, list_sheets: bool):
    """Load VMware inventory from Excel file into database."""
    from .loader import get_sheet_names
    
    # List sheets if requested
    if list_sheets:
        try:
            sheets = get_sheet_names(excel_file)
            click.echo(f"\n📊 Available sheets in {excel_file.name}:\n")
            for idx, sheet_name in enumerate(sheets):
                click.echo(f"  {idx}: {sheet_name}")
            click.echo()
            return
        except Exception as e:
            click.echo(f"✗ Error reading Excel file: {e}", err=True)
            raise click.Abort()
    
    click.echo(f"Loading data from {excel_file}...")
    click.echo(f"Sheet: {sheet}")
    
    try:
        records = load_excel_to_db(excel_file, db_url, clear_existing=clear, sheet_name=sheet)
        click.echo(f"✓ Successfully loaded {records} records into database")
        click.echo(f"Database: {db_url}")
    except Exception as e:
        click.echo(f"✗ Error loading data: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.argument('output_file', type=click.Path(path_type=Path))
@click.option(
    "--db-url",
    default="sqlite:///data/vmware_inventory.db",
    help="Database URL",
    show_default=True,
)
def backup(output_file: Path, db_url: str):
    """Create a full database backup."""
    from datetime import datetime
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import create_engine
    from .services.backup_service import BackupService
    
    try:
        engine = create_engine(db_url, echo=False)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        backup_service = BackupService(session)
        
        click.echo(f"\n💾 Creating database backup...")
        stats = backup_service.backup_database(output_file, db_url)
        
        click.echo(f"\n✅ Database backup complete!")
        click.echo(f"   Source: {stats['source']}")
        click.echo(f"   Backup: {stats['backup_file']}")
        click.echo(f"   Size: {stats['size_bytes']:,} bytes")
        click.echo(f"   Tables: {stats['tables']}")
        click.echo()
        
        session.close()
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.argument('backup_file', type=click.Path(exists=True, path_type=Path))
@click.option(
    "--db-url",
    default="sqlite:///data/vmware_inventory.db",
    help="Database URL",
    show_default=True,
)
@click.confirmation_option(prompt='This will replace the current database. Continue?')
def restore(backup_file: Path, db_url: str):
    """Restore database from backup file."""
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import create_engine
    from .services.backup_service import BackupService
    
    try:
        engine = create_engine(db_url, echo=False)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        backup_service = BackupService(session)
        
        click.echo(f"\n🔄 Restoring database from backup...")
        click.echo("   ⚠️  Current database will be backed up before restore")
        
        stats = backup_service.restore_database(backup_file, db_url, confirm=True)
        
        click.echo(f"\n✅ Database restore complete!")
        click.echo(f"   Restored from: {stats['restored_from']}")
        click.echo(f"   Restored to: {stats['restored_to']}")
        click.echo(f"   Size: {stats['size_bytes']:,} bytes")
        click.echo()
        
        session.close()
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.option(
    "--db-url",
    default="sqlite:///data/vmware_inventory.db",
    help="Database URL",
    show_default=True,
)
def stats(db_url: str):
    """Show statistics about the inventory database."""
    from sqlalchemy import create_engine, func
    from sqlalchemy.orm import sessionmaker
    from .models import VirtualMachine
    
    engine = create_engine(db_url, echo=False)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    try:
        total_vms = session.query(func.count(VirtualMachine.id)).scalar()
        powered_on = session.query(func.count(VirtualMachine.id)).filter(
            VirtualMachine.powerstate == "poweredOn"
        ).scalar()
        powered_off = session.query(func.count(VirtualMachine.id)).filter(
            VirtualMachine.powerstate == "poweredOff"
        ).scalar()
        
        datacenters = session.query(func.count(func.distinct(VirtualMachine.datacenter))).scalar()
        clusters = session.query(func.count(func.distinct(VirtualMachine.cluster))).scalar()
        hosts = session.query(func.count(func.distinct(VirtualMachine.host))).scalar()
        
        click.echo("\n=== VMware Inventory Statistics ===")
        click.echo(f"\nTotal VMs: {total_vms}")
        click.echo(f"  - Powered On:  {powered_on}")
        click.echo(f"  - Powered Off: {powered_off}")
        click.echo(f"\nInfrastructure:")
        click.echo(f"  - Datacenters: {datacenters}")
        click.echo(f"  - Clusters:    {clusters}")
        click.echo(f"  - Hosts:       {hosts}")
        click.echo()
        
    except Exception as e:
        click.echo(f"✗ Error retrieving statistics: {e}", err=True)
        raise click.Abort()
    finally:
        session.close()


@click.group()
def vm():
    """Virtual machine operations."""
    pass


# Register vm command group
cli.add_command(vm)


@vm.command(name="list")
@click.option(
    "--db-url",
    default="sqlite:///data/vmware_inventory.db",
    help="Database URL",
    show_default=True,
)
@click.option(
    "--datacenter",
    help="Filter by datacenter",
)
@click.option(
    "--cluster",
    help="Filter by cluster",
)
@click.option(
    "--limit",
    type=int,
    default=10,
    help="Number of records to show",
    show_default=True,
)
def vm_list(db_url: str, datacenter: str, cluster: str, limit: int):
    """List virtual machines from the inventory."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from .models import VirtualMachine
    
    engine = create_engine(db_url, echo=False)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    try:
        query = session.query(VirtualMachine)
        
        if datacenter:
            query = query.filter(VirtualMachine.datacenter == datacenter)
        if cluster:
            query = query.filter(VirtualMachine.cluster == cluster)
        
        vms = query.limit(limit).all()
        
        if not vms:
            click.echo("No VMs found.")
            return
        
        click.echo("\n{:<40} {:<15} {:<20} {:<20}".format("VM Name", "Power State", "Datacenter", "Cluster"))
        click.echo("-" * 95)
        
        for vm in vms:
            click.echo("{:<40} {:<15} {:<20} {:<20}".format(
                vm.vm[:40],
                vm.powerstate or "N/A",
                vm.datacenter or "N/A",
                vm.cluster or "N/A"
            ))
        
        click.echo()
        
    except Exception as e:
        click.echo(f"✗ Error listing VMs: {e}", err=True)
        raise click.Abort()
    finally:
        session.close()


@vm.command(name="search")
@click.argument("pattern")
@click.option(
    "--db-url",
    default="sqlite:///data/vmware_inventory.db",
    help="Database URL",
    show_default=True,
)
@click.option(
    "--datacenter",
    help="Filter by datacenter",
)
@click.option(
    "--cluster",
    help="Filter by cluster",
)
@click.option(
    "--powerstate",
    type=click.Choice(["poweredOn", "poweredOff"], case_sensitive=False),
    help="Filter by power state",
)
@click.option(
    "--limit",
    type=int,
    default=50,
    help="Maximum number of results to return",
    show_default=True,
)
@click.option(
    "--case-sensitive",
    is_flag=True,
    help="Make regex search case-sensitive",
)
def vm_search(pattern: str, db_url: str, datacenter: str, cluster: str, powerstate: str, limit: int, case_sensitive: bool):
    """Search for VMs using regex pattern matching on VM names."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from .models import VirtualMachine
    from tabulate import tabulate
    import re
    
    engine = create_engine(db_url, echo=False)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    try:
        # Compile regex pattern
        try:
            flags = 0 if case_sensitive else re.IGNORECASE
            regex = re.compile(pattern, flags)
        except re.error as e:
            click.echo(f"✗ Invalid regex pattern: {e}", err=True)
            raise click.Abort()
        
        # Build base query
        query = session.query(VirtualMachine)
        
        # Apply filters
        if datacenter:
            query = query.filter(VirtualMachine.datacenter == datacenter)
        if cluster:
            query = query.filter(VirtualMachine.cluster == cluster)
        if powerstate:
            query = query.filter(VirtualMachine.powerstate == powerstate)
        
        # Get all matching VMs (we'll filter by regex in Python)
        all_vms = query.all()
        
        # Filter by regex
        matching_vms = [vm for vm in all_vms if vm.vm and regex.search(vm.vm)]
        
        if not matching_vms:
            click.echo(f"No VMs found matching pattern: {pattern}")
            return
        
        # Apply limit
        vms_to_show = matching_vms[:limit]
        
        # Prepare table data
        table_data = []
        for vm in vms_to_show:
            table_data.append([
                vm.vm[:45] if len(vm.vm) > 45 else vm.vm,
                vm.powerstate or "N/A",
                vm.datacenter or "N/A",
                vm.cluster or "N/A",
                f"{vm.cpus or 0}",
                f"{(vm.memory or 0) / 1024:.1f}" if vm.memory else "0.0"
            ])
        
        # Display results
        headers = ['VM Name', 'Power', 'Datacenter', 'Cluster', 'vCPUs', 'RAM (GiB)']
        title = f"\n🔍 Found {len(matching_vms)} VM(s) matching '{pattern}'"
        if len(matching_vms) > limit:
            title += f" (showing {limit})"
        click.echo(title + ":\n")
        click.echo(tabulate(table_data, headers=headers, tablefmt='simple'))
        click.echo()
        
    except Exception as e:
        click.echo(f"✗ Error searching VMs: {e}", err=True)
        raise click.Abort()
    finally:
        session.close()


@cli.command()
@click.option(
    "--db-url",
    default="sqlite:///data/vmware_inventory.db",
    help="Database URL",
    show_default=True,
)
def datacenters(db_url: str):
    """List all datacenters with VM counts and statistics."""
    from sqlalchemy import create_engine, func
    from sqlalchemy.orm import sessionmaker
    from .models import VirtualMachine
    from tabulate import tabulate
    
    engine = create_engine(db_url, echo=False)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    try:
        # Query datacenters with aggregated stats
        from sqlalchemy import case
        results = session.query(
            VirtualMachine.datacenter,
            func.count(VirtualMachine.id).label('vm_count'),
            func.sum(case((VirtualMachine.powerstate == 'poweredOn', 1), else_=0)).label('powered_on'),
            func.sum(case((VirtualMachine.powerstate == 'poweredOff', 1), else_=0)).label('powered_off'),
            func.count(func.distinct(VirtualMachine.cluster)).label('cluster_count'),
            func.count(func.distinct(VirtualMachine.host)).label('host_count'),
            func.sum(VirtualMachine.cpus).label('total_cpus'),
            func.sum(VirtualMachine.memory).label('total_memory_mib'),
            func.sum(VirtualMachine.provisioned_mib).label('total_storage_mib')
        ).filter(
            VirtualMachine.datacenter.isnot(None)
        ).group_by(
            VirtualMachine.datacenter
        ).order_by(
            func.count(VirtualMachine.id).desc()
        ).all()
        
        if not results:
            click.echo("No datacenters found.")
            return
        
        # Prepare table data
        table_data = []
        for row in results:
            memory_gib = (row.total_memory_mib or 0) / 1024
            storage_tib = (row.total_storage_mib or 0) / 1024 / 1024
            
            table_data.append([
                row.datacenter,
                row.vm_count,
                row.powered_on or 0,
                row.powered_off or 0,
                row.cluster_count,
                row.host_count,
                row.total_cpus or 0,
                f"{memory_gib:.1f}",
                f"{storage_tib:.2f}"
            ])
        
        # Display table
        headers = ['Datacenter', 'VMs', 'On', 'Off', 'Clusters', 'Hosts', 'vCPUs', 'RAM (GiB)', 'Storage (TiB)']
        click.echo(f"\n🏢 Datacenters ({len(results)}):\n")
        click.echo(tabulate(table_data, headers=headers, tablefmt='simple'))
        click.echo()
        
    except Exception as e:
        click.echo(f"✗ Error listing datacenters: {e}", err=True)
        raise click.Abort()
    finally:
        session.close()


@cli.command()
@click.option(
    "--db-url",
    default="sqlite:///data/vmware_inventory.db",
    help="Database URL",
    show_default=True,
)
@click.option(
    "--datacenter",
    help="Filter by datacenter",
)
@click.option(
    "--filter",
    "cluster_filter",
    help="Regex pattern to filter cluster names",
)
def clusters(db_url: str, datacenter: str, cluster_filter: str):
    """List all clusters with VM counts and statistics."""
    from sqlalchemy import create_engine, func
    from sqlalchemy.orm import sessionmaker
    from .models import VirtualMachine
    from tabulate import tabulate
    import re
    
    engine = create_engine(db_url, echo=False)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    try:
        # Build query
        from sqlalchemy import case
        query = session.query(
            VirtualMachine.datacenter,
            VirtualMachine.cluster,
            func.count(VirtualMachine.id).label('vm_count'),
            func.sum(case((VirtualMachine.powerstate == 'poweredOn', 1), else_=0)).label('powered_on'),
            func.sum(case((VirtualMachine.powerstate == 'poweredOff', 1), else_=0)).label('powered_off'),
            func.count(func.distinct(VirtualMachine.host)).label('host_count'),
            func.sum(VirtualMachine.cpus).label('total_cpus'),
            func.sum(VirtualMachine.memory).label('total_memory_mib'),
            func.sum(VirtualMachine.provisioned_mib).label('total_storage_mib')
        ).filter(
            VirtualMachine.cluster.isnot(None)
        )
        
        if datacenter:
            query = query.filter(VirtualMachine.datacenter == datacenter)
        
        results = query.group_by(
            VirtualMachine.datacenter,
            VirtualMachine.cluster
        ).order_by(
            VirtualMachine.datacenter,
            func.count(VirtualMachine.id).desc()
        ).all()
        
        if not results:
            if datacenter:
                click.echo(f"No clusters found in datacenter: {datacenter}")
            else:
                click.echo("No clusters found.")
            return
        
        # Apply regex filter if provided
        if cluster_filter:
            try:
                pattern = re.compile(cluster_filter)
                results = [row for row in results if pattern.search(row.cluster or '')]
            except re.error as e:
                click.echo(f"✗ Invalid regex pattern: {e}", err=True)
                raise click.Abort()
            
            if not results:
                click.echo(f"No clusters match the filter pattern: {cluster_filter}")
                return
        
        # Prepare table data
        table_data = []
        for row in results:
            memory_gib = (row.total_memory_mib or 0) / 1024
            storage_tib = (row.total_storage_mib or 0) / 1024 / 1024
            
            table_data.append([
                row.datacenter or 'N/A',
                row.cluster,
                row.vm_count,
                row.powered_on or 0,
                row.powered_off or 0,
                row.host_count,
                row.total_cpus or 0,
                f"{memory_gib:.1f}",
                f"{storage_tib:.2f}"
            ])
        
        # Display table
        headers = ['Datacenter', 'Cluster', 'VMs', 'On', 'Off', 'Hosts', 'vCPUs', 'RAM (GiB)', 'Storage (TiB)']
        title = f"🖥️  Clusters ({len(results)})"
        if datacenter:
            title += f" in {datacenter}"
        if cluster_filter:
            title += f" [filter: {cluster_filter}]"
        click.echo(f"\n{title}:\n")
        click.echo(tabulate(table_data, headers=headers, tablefmt='simple'))
        click.echo()
        
    except Exception as e:
        click.echo(f"✗ Error listing clusters: {e}", err=True)
        raise click.Abort()
    finally:
        session.close()


@cli.command()
@click.option(
    "--db-url",
    default="sqlite:///data/vmware_inventory.db",
    help="Database URL",
    show_default=True,
)
@click.option(
    "--table",
    type=click.Choice(["virtual_machines", "labels", "vm_labels", "folder_labels", "all"], case_sensitive=False),
    default="virtual_machines",
    help="Table to display schema for",
    show_default=True,
)
@click.option(
    "--filter",
    "filters",
    multiple=True,
    help="Filter columns by category (basic, resources, network, storage, hardware, infrastructure, os, custom, relationships)",
)
@click.option(
    "--group-by",
    type=click.Choice(["category", "type", "nullable", "indexed"], case_sensitive=False),
    help="Group columns by attribute",
)
def schema(db_url: str, table: str, filters: tuple, group_by: str):
    """View the datamodel schema with filtering and grouping options."""
    from sqlalchemy import create_engine, inspect
    from .models import VirtualMachine, Label, VMLabel, FolderLabel
    
    engine = create_engine(db_url, echo=False)
    inspector = inspect(engine)
    
    # Define column categories for each table
    vm_categories = {
        "basic": ["id", "vm", "powerstate", "template", "srm_placeholder", "config_status", 
                  "dns_name", "connection_state", "guest_state", "heartbeat", "consolidation_needed"],
        "timing": ["poweron", "suspend_time", "creation_date", "change_version"],
        "resources": ["cpus", "memory", "nics", "disks"],
        "configuration": ["min_required_evc_mode_key", "latency_sensitivity", "enable_uuid", "cbt"],
        "network": ["primary_ip_address", "network_1", "network_2", "network_3", "network_4", 
                    "network_5", "network_6", "network_7", "network_8"],
        "display": ["num_monitors", "video_ram_kib"],
        "organization": ["resource_pool", "folder", "vapp"],
        "ha_ft": ["das_protection", "ft_state", "ft_latency", "ft_bandwidth", "ft_sec_latency",
                  "ha_restart_priority", "ha_isolation_response", "ha_vm_monitoring", 
                  "cluster_rules", "cluster_rule_names"],
        "storage": ["provisioned_mib", "in_use_mib", "unshared_mib"],
        "boot": ["boot_required", "boot_delay", "boot_retry_delay", "boot_retry_enabled", "boot_bios_setup"],
        "hardware": ["firmware", "hw_version", "hw_upgrade_status", "hw_upgrade_policy", "hw_target"],
        "paths": ["path", "log_directory", "snapshot_directory", "suspend_directory"],
        "additional": ["annotation", "nb_last_backup"],
        "infrastructure": ["datacenter", "cluster", "host"],
        "os": ["os_config", "os_vmware_tools"],
        "identifiers": ["vm_id", "vm_uuid"],
        "sdk": ["vi_sdk_server_type", "vi_sdk_api_version"],
        "custom": ["code_ccx", "vm_nbu", "vm_orchid", "licence_enforcement", "env"],
        "metadata": ["imported_at"],
    }
    
    label_categories = {
        "basic": ["id", "key", "value"],
        "metadata": ["description", "color", "created_at", "updated_at"],
    }
    
    vm_label_categories = {
        "relationships": ["id", "vm_id", "label_id"],
        "metadata": ["assigned_at", "assigned_by"],
        "inheritance": ["inherited_from_folder", "source_folder_path"],
    }
    
    folder_label_categories = {
        "relationships": ["id", "folder_path", "label_id"],
        "metadata": ["assigned_at", "assigned_by"],
        "inheritance": ["inherit_to_vms", "inherit_to_subfolders"],
    }
    
    # Determine which tables to display
    tables_to_show = []
    if table == "all":
        tables_to_show = [("virtual_machines", vm_categories), ("labels", label_categories), 
                          ("vm_labels", vm_label_categories), ("folder_labels", folder_label_categories)]
    elif table == "virtual_machines":
        tables_to_show = [("virtual_machines", vm_categories)]
    elif table == "labels":
        tables_to_show = [("labels", label_categories)]
    elif table == "vm_labels":
        tables_to_show = [("vm_labels", vm_label_categories)]
    elif table == "folder_labels":
        tables_to_show = [("folder_labels", folder_label_categories)]
    
    # Process each table
    for table_name, categories in tables_to_show:
        _display_table_schema(inspector, table_name, categories, filters, group_by)


def _display_table_schema(inspector, table_name: str, categories: dict, filters: tuple, group_by: str):
    """Display schema for a specific table."""
    # Get column information
    try:
        columns = inspector.get_columns(table_name)
    except Exception:
        click.echo(f"⚠ Table '{table_name}' does not exist. Load data first.", err=True)
        return
    
    # Build column info with metadata
    column_info = []
    for col in columns:
        # Find category
        col_category = "unknown"
        for cat_name, cat_cols in categories.items():
            if col["name"] in cat_cols:
                col_category = cat_name
                break
        
        # Get indexes
        try:
            indexes = inspector.get_indexes(table_name)
            is_indexed = any(col["name"] in idx["column_names"] for idx in indexes)
        except Exception:
            is_indexed = False
        
        # Get type name
        type_name = str(col["type"])
        
        column_info.append({
            "name": col["name"],
            "type": type_name,
            "nullable": col["nullable"],
            "indexed": is_indexed,
            "category": col_category,
        })
    
    # Apply filters
    if filters:
        filter_set = set(filters)
        column_info = [c for c in column_info if c["category"] in filter_set]
    
    if not column_info:
        click.echo("No columns match the specified filters.")
        return
    
    # Display results
    click.echo(f"\n=== {table_name.replace('_', ' ').title()} Schema ({len(column_info)} columns) ===")
    
    if group_by:
        # Group and display
        from itertools import groupby
        
        column_info.sort(key=lambda x: x[group_by])
        
        for key, group in groupby(column_info, key=lambda x: x[group_by]):
            group_list = list(group)
            click.echo(f"\n[{group_by.upper()}: {key}] ({len(group_list)} columns)")
            click.echo("{:<30} {:<20} {:<10} {:<10} {:<15}".format(
                "Column", "Type", "Nullable", "Indexed", "Category"
            ))
            click.echo("-" * 85)
            
            for col in group_list:
                click.echo("{:<30} {:<20} {:<10} {:<10} {:<15}".format(
                    col["name"],
                    col["type"][:20],
                    "Yes" if col["nullable"] else "No",
                    "Yes" if col["indexed"] else "No",
                    col["category"],
                ))
    else:
        # Display flat list
        click.echo("\n{:<30} {:<20} {:<10} {:<10} {:<15}".format(
            "Column", "Type", "Nullable", "Indexed", "Category"
        ))
        click.echo("-" * 85)
        
        for col in column_info:
            click.echo("{:<30} {:<20} {:<10} {:<10} {:<15}".format(
                col["name"],
                col["type"][:20],
                "Yes" if col["nullable"] else "No",
                "Yes" if col["indexed"] else "No",
                col["category"],
            ))
    
    click.echo()
    
    # Show available categories if no filter applied
    if not filters:
        click.echo("Available categories for --filter:")
        click.echo(", ".join(sorted(set(c["category"] for c in column_info))))
        click.echo()


@cli.command()
@click.option(
    "--db-url",
    default="sqlite:///data/vmware_inventory.db",
    help="Database URL",
    show_default=True,
)
@click.option(
    "--force",
    is_flag=True,
    help="Skip confirmation prompt",
)
def clean(db_url: str, force: bool):
    """Remove all data from the database."""
    from sqlalchemy import create_engine, text
    from .models import Base
    
    click.echo(f"\n🗑️  Database Clean")
    click.echo(f"Database: {db_url}\n")
    
    try:
        engine = create_engine(db_url, echo=False)
        
        # Check if database exists and has data
        try:
            with engine.connect() as conn:
                result = conn.execute(text("SELECT COUNT(*) FROM virtual_machines"))
                count = result.scalar()
                
                if count == 0:
                    click.echo("ℹ️  Database is already empty.")
                    return
                
                click.echo(f"⚠️  This will delete {count:,} records from the database.")
        except Exception:
            click.echo("ℹ️  Database table does not exist or is empty.")
            return
        
        # Confirmation
        if not force:
            click.echo("\nThis action cannot be undone!")
            if not click.confirm("Are you sure you want to continue?"):
                click.echo("Aborted.")
                return
        
        # Delete all records
        click.echo("\n🗑️  Deleting all records...", nl=False)
        with engine.begin() as conn:
            conn.execute(text("DELETE FROM virtual_machines"))
        click.echo(" ✓")
        
        # Vacuum database to reclaim space
        if db_url.startswith('sqlite'):
            click.echo("📊 Optimizing database...", nl=False)
            with engine.connect() as conn:
                conn.execution_options(isolation_level="AUTOCOMMIT")
                conn.execute(text("VACUUM"))
            click.echo(" ✓")
        
        click.echo(f"\n✅ Database cleaned successfully!")
        click.echo("\n📊 Next steps:")
        click.echo("   - Load new data: vmware-inv load <excel_file>")
        click.echo("   - Check status: vmware-inv stats")
        
    except Exception as e:
        click.echo(f"\n✗ Error: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.option(
    "--db-url",
    default="sqlite:///data/vmware_inventory.db",
    help="Database URL",
    show_default=True,
)
def optimize(db_url: str):
    """Optimize database by adding performance indexes."""
    from sqlalchemy import create_engine, text, inspect
    
    click.echo("\n🛠️  Optimizing database performance...")
    click.echo(f"Database: {db_url}\n")
    
    try:
        engine = create_engine(db_url, echo=False)
        inspector = inspect(engine)
        
        # Get existing indexes
        existing_indexes = {idx['name'] for idx in inspector.get_indexes('virtual_machines')}
        click.echo(f"📊 Found {len(existing_indexes)} existing indexes")
        
        # Define indexes to create
        indexes_to_create = [
            ('powerstate', 'ix_virtual_machines_powerstate'),
            ('template', 'ix_virtual_machines_template'),
            ('creation_date', 'ix_virtual_machines_creation_date'),
            ('resource_pool', 'ix_virtual_machines_resource_pool'),
            ('folder', 'ix_virtual_machines_folder'),
            ('os_config', 'ix_virtual_machines_os_config'),
        ]
        
        created_count = 0
        skipped_count = 0
        
        with engine.begin() as conn:
            for column_name, index_name in indexes_to_create:
                if index_name in existing_indexes:
                    click.echo(f"⏭️  Index on '{column_name}' already exists")
                    skipped_count += 1
                    continue
                
                try:
                    click.echo(f"➡️  Creating index on '{column_name}'...", nl=False)
                    sql = text(f"CREATE INDEX {index_name} ON virtual_machines ({column_name})")
                    conn.execute(sql)
                    created_count += 1
                    click.echo(" ✓")
                except Exception as e:
                    click.echo(f" ✗ Failed: {e}")
        
        click.echo(f"\n📊 Summary:")
        click.echo(f"   Created: {created_count} indexes")
        click.echo(f"   Skipped: {skipped_count} indexes")
        
        # Show final index count
        inspector = inspect(engine)
        final_indexes = inspector.get_indexes('virtual_machines')
        click.echo(f"\n✅ Database now has {len(final_indexes)} indexes for optimal performance!")
        
    except Exception as e:
        click.echo(f"\n✗ Error: {e}", err=True)
        raise click.Abort()


@cli.command(name="schema-version")
@click.option(
    "--db-url",
    default="sqlite:///data/vmware_inventory.db",
    help="Database URL",
    show_default=True,
)
@click.option(
    "--history",
    is_flag=True,
    help="Show version history",
)
def schema_version(db_url: str, history: bool):
    """Show database schema version information."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from .services.schema_service import SchemaService, CURRENT_SCHEMA_VERSION
    from tabulate import tabulate
    
    try:
        engine = create_engine(db_url, echo=False)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        schema_service = SchemaService(session)
        
        # Get current version info
        current_version = schema_service.get_current_version()
        compatibility = schema_service.check_schema_compatibility()
        
        click.echo(f"\n📊 Schema Version Information")
        click.echo(f"Database: {db_url}\n")
        
        # Current status
        if current_version:
            click.echo(f"Current version:  {current_version.version}")
            click.echo(f"Applied at:       {current_version.applied_at.strftime('%Y-%m-%d %H:%M:%S')}")
            click.echo(f"Applied by:       {current_version.applied_by or 'N/A'}")
        else:
            click.echo(f"Current version:  None (uninitialized)")
        
        click.echo(f"Expected version: {CURRENT_SCHEMA_VERSION}")
        
        # Compatibility status
        if compatibility['compatible']:
            click.echo(f"\n✅ Status: Compatible")
        else:
            click.echo(f"\n⚠️  Status: {compatibility['message']}")
            click.echo(f"\n💡 Run 'vmware-inv schema-upgrade' to update the schema")
        
        # Show history if requested
        if history:
            versions = schema_service.get_all_versions()
            if versions:
                click.echo(f"\n📜 Version History ({len(versions)} versions):\n")
                
                table_data = []
                for v in versions:
                    status = "✓ Current" if v.is_current else ""
                    table_data.append([
                        v.version,
                        v.description[:60] + "..." if len(v.description) > 60 else v.description,
                        v.applied_at.strftime('%Y-%m-%d %H:%M'),
                        v.applied_by or "N/A",
                        status
                    ])
                
                headers = ['Version', 'Description', 'Applied', 'By', 'Status']
                click.echo(tabulate(table_data, headers=headers, tablefmt='simple'))
            else:
                click.echo("\n📜 No version history available")
        
        click.echo()
        session.close()
        
    except Exception as e:
        click.echo(f"\n✗ Error: {e}", err=True)
        import traceback
        traceback.print_exc()
        raise click.Abort()


@cli.command(name="schema-info")
@click.option(
    "--db-url",
    default="sqlite:///data/vmware_inventory.db",
    help="Database URL",
    show_default=True,
)
def schema_info(db_url: str):
    """Show detailed schema information including tables and compatibility."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from .services.schema_service import SchemaService
    from tabulate import tabulate
    
    try:
        engine = create_engine(db_url, echo=False)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        schema_service = SchemaService(session)
        
        # Get comprehensive schema info
        info = schema_service.get_schema_info()
        
        click.echo(f"\n📋 Database Schema Information")
        click.echo(f"Database: {db_url}\n")
        
        # Version info
        click.echo("Version:")
        click.echo(f"  Current:  {info['current_version'] or 'Not set'}")
        click.echo(f"  Expected: {info['expected_version']}")
        click.echo(f"  Status:   {'✅ Compatible' if info['compatible'] else '⚠️  Incompatible'}")
        
        # Tables
        click.echo(f"\nTables ({info['tables_count']}):")
        table_data = [[i+1, table] for i, table in enumerate(sorted(info['tables']))]
        click.echo(tabulate(table_data, headers=['#', 'Table Name'], tablefmt='simple'))
        
        # Metadata
        click.echo(f"\nMetadata:")
        click.echo(f"  Schema tracking: {'✅ Enabled' if info['schema_tracking_enabled'] else '❌ Disabled'}")
        click.echo(f"  Version history: {info['version_history_count']} record(s)")
        if info['last_update']:
            click.echo(f"  Last update:     {info['last_update'].strftime('%Y-%m-%d %H:%M:%S')}")
        
        click.echo()
        session.close()
        
    except Exception as e:
        click.echo(f"\n✗ Error: {e}", err=True)
        import traceback
        traceback.print_exc()
        raise click.Abort()


@cli.command(name="schema-upgrade")
@click.option(
    "--db-url",
    default="sqlite:///data/vmware_inventory.db",
    help="Database URL",
    show_default=True,
)
@click.option(
    "--force",
    is_flag=True,
    help="Skip confirmation prompt",
)
def schema_upgrade(db_url: str, force: bool):
    """Upgrade database schema to current version."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from .models import Base
    from .services.schema_service import SchemaService, CURRENT_SCHEMA_VERSION
    
    click.echo(f"\n📊 Database Schema Upgrade")
    click.echo(f"Database: {db_url}\n")
    
    try:
        engine = create_engine(db_url, echo=False)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        schema_service = SchemaService(session)
        
        # Check current version
        current_version = schema_service.get_current_version()
        
        if current_version:
            click.echo(f"Current version: {current_version.version}")
        else:
            click.echo("Current version: None (uninitialized)")
        
        click.echo(f"Target version:  {CURRENT_SCHEMA_VERSION}")
        
        if current_version and current_version.version == CURRENT_SCHEMA_VERSION:
            click.echo(f"\n✅ Database is already at the latest version!")
            return
        
        if not force:
            click.echo("\n⚠️  This will:")
            click.echo("   - Create any missing tables")
            click.echo("   - Update schema version tracking")
            click.echo(f"   - Upgrade from {current_version.version if current_version else 'uninitialized'} to {CURRENT_SCHEMA_VERSION}")
            click.echo()
            if not click.confirm("Proceed with upgrade?"):
                click.echo("Aborted.")
                return
        
        # Create all tables
        click.echo("\n📦 Creating/updating tables...", nl=False)
        Base.metadata.create_all(engine)
        click.echo(" ✓")
        
        # Record new schema version
        click.echo("📝 Recording schema version...", nl=False)
        if not current_version:
            # First time initialization
            schema_service.initialize_schema_tracking()
        else:
            # Upgrade
            schema_service.record_version(
                version=CURRENT_SCHEMA_VERSION,
                description="Add migration planning tables (MigrationTarget, MigrationScenario, MigrationWave)",
                applied_by="cli",
                migration_script="002_add_migration_planning_tables.sql",
                tables_added="migration_targets,migration_scenarios,migration_waves",
                notes="Adds multi-platform migration planning and scenario analysis capabilities"
            )
        click.echo(" ✓")
        
        session.close()
        
        click.echo(f"\n✅ Schema upgraded successfully to version {CURRENT_SCHEMA_VERSION}!")
        click.echo("\n📊 Next steps:")
        click.echo("   - Use 'vmware-inv stats' to verify database")
        click.echo("   - Access migration planning in the dashboard")
        
    except Exception as e:
        click.echo(f"\n✗ Error: {e}", err=True)
        import traceback
        traceback.print_exc()
        raise click.Abort()


@cli.command()
@click.option(
    "--port",
    type=int,
    default=8501,
    help="Port to run the dashboard on",
    show_default=True,
)
@click.option(
    "--host",
    default="localhost",
    help="Host to bind the dashboard to",
    show_default=True,
)
@click.option(
    "--db-url",
    default="sqlite:///data/vmware_inventory.db",
    help="Database URL (will be set as default in dashboard)",
    show_default=True,
)
@click.option(
    "--no-browser",
    is_flag=True,
    help="Don't automatically open browser",
)
def dashboard(port: int, host: str, db_url: str, no_browser: bool):
    """Launch the interactive web dashboard."""
    import os
    from .dashboard import APP_PATH
    
    if not APP_PATH.exists():
        click.echo(f"✗ Error: Dashboard app not found at {APP_PATH}", err=True)
        click.echo("\nPlease ensure the package is installed correctly.", err=True)
        raise click.Abort()
    
    click.echo(f"🚀 Starting VMware Inventory Dashboard...")
    click.echo(f"   Host: {host}")
    click.echo(f"   Port: {port}")
    click.echo(f"   Database: {db_url}")
    click.echo(f"\n   Access at: http://{host}:{port}")
    click.echo("\n   Press Ctrl+C to stop the dashboard\n")
    
    # Set environment variable for default database URL
    os.environ['VMWARE_INV_DB_URL'] = db_url
    
    # Build streamlit command
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(APP_PATH),
        f"--server.port={port}",
        f"--server.address={host}",
    ]
    
    if no_browser:
        cmd.append("--server.headless=true")
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        click.echo("\n\n✓ Dashboard stopped.")
    except subprocess.CalledProcessError as e:
        click.echo(f"\n✗ Error running dashboard: {e}", err=True)
        raise click.Abort()
    except FileNotFoundError:
        click.echo("\n✗ Error: Streamlit not found. Install it with: uv sync", err=True)
        raise click.Abort()


@cli.command()
@click.option(
    "--port",
    type=int,
    default=8501,
    help="Port to run the dashboard on",
    show_default=True,
)
@click.option(
    "--host",
    default="localhost",
    help="Host to bind the dashboard to",
    show_default=True,
)
@click.option(
    "--db-path",
    default="vmware_inventory.db",
    help="Path for new database file (will be created if doesn't exist)",
    show_default=True,
)
@click.option(
    "--no-browser",
    is_flag=True,
    help="Don't automatically open browser",
)
def fullweb(port: int, host: str, db_path: str, no_browser: bool):
    """Launch dashboard in full web mode - create database and load data from web UI.
    
    This mode starts the dashboard without requiring an existing database.
    You can create a new database and import data entirely through the web interface.
    Perfect for first-time users or standalone deployments.
    """
    import os
    from pathlib import Path
    from .dashboard import APP_PATH
    
    if not APP_PATH.exists():
        click.echo(f"✗ Error: Dashboard app not found at {APP_PATH}", err=True)
        click.echo("\nPlease ensure the package is installed correctly.", err=True)
        raise click.Abort()
    
    # Construct database URL
    db_file = Path(db_path)
    db_url = f"sqlite:///{db_file.absolute()}"
    
    click.echo(f"🌐 Starting VMware Inventory Dashboard (Full Web Mode)...")
    click.echo(f"\n📌 Configuration:")
    click.echo(f"   Host: {host}")
    click.echo(f"   Port: {port}")
    click.echo(f"   Database: {db_file.absolute()}")
    
    # Check if database exists
    if db_file.exists():
        click.echo(f"\n💾 Existing database found")
        click.echo(f"   You can load new data or work with existing data")
    else:
        click.echo(f"\n✨ New database will be created")
        click.echo(f"   Use 'Data Import' page to upload and load your Excel file")
    
    click.echo(f"\n🌍 Access at: http://{host}:{port}")
    click.echo(f"\n📥 To get started:")
    click.echo(f"   1. Navigate to Management > Data Import")
    click.echo(f"   2. Upload your Excel file (RVTools export)")
    click.echo(f"   3. Select sheet and import options")
    click.echo(f"   4. Click 'Import Data'")
    click.echo("\n   Press Ctrl+C to stop the dashboard\n")
    
    # Set environment variable for default database URL
    os.environ['VMWARE_INV_DB_URL'] = db_url
    
    # Build streamlit command
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(APP_PATH),
        f"--server.port={port}",
        f"--server.address={host}",
    ]
    
    if no_browser:
        cmd.append("--server.headless=true")
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        click.echo("\n\n✓ Dashboard stopped.")
        if db_file.exists():
            file_size = db_file.stat().st_size / (1024 * 1024)
            click.echo(f"\n💾 Database saved: {db_file.absolute()} ({file_size:.2f} MB)")
            click.echo("\n🔄 To restart with same database:")
            click.echo(f"   vmware-inv fullweb --db-path {db_path}")
    except subprocess.CalledProcessError as e:
        click.echo(f"\n✗ Error running dashboard: {e}", err=True)
        raise click.Abort()
    except FileNotFoundError:
        click.echo("\n✗ Error: Streamlit not found. Install it with: uv sync", err=True)
        raise click.Abort()


if __name__ == "__main__":
    cli()
