"""CLI for VMware inventory management."""

import click
import subprocess
import sys
from pathlib import Path
from .loader import load_excel_to_db


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """VMware inventory management CLI."""
    pass


@cli.command()
@click.argument("excel_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--db-url",
    default="sqlite:///vmware_inventory.db",
    help="Database URL (default: sqlite:///vmware_inventory.db)",
    show_default=True,
)
@click.option(
    "--clear",
    is_flag=True,
    help="Clear existing data before loading",
)
def load(excel_file: Path, db_url: str, clear: bool):
    """Load VMware inventory from Excel file into database."""
    click.echo(f"Loading data from {excel_file}...")
    
    try:
        records = load_excel_to_db(excel_file, db_url, clear_existing=clear)
        click.echo(f"✓ Successfully loaded {records} records into database")
        click.echo(f"Database: {db_url}")
    except Exception as e:
        click.echo(f"✗ Error loading data: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.option(
    "--db-url",
    default="sqlite:///vmware_inventory.db",
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


@cli.command()
@click.option(
    "--db-url",
    default="sqlite:///vmware_inventory.db",
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
def list(db_url: str, datacenter: str, cluster: str, limit: int):
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


@cli.command()
@click.option(
    "--db-url",
    default="sqlite:///vmware_inventory.db",
    help="Database URL",
    show_default=True,
)
@click.option(
    "--filter",
    "filters",
    multiple=True,
    help="Filter columns by category (basic, resources, network, storage, hardware, infrastructure, os, custom)",
)
@click.option(
    "--group-by",
    type=click.Choice(["category", "type", "nullable", "indexed"], case_sensitive=False),
    help="Group columns by attribute",
)
def schema(db_url: str, filters: tuple, group_by: str):
    """View the datamodel schema with filtering and grouping options."""
    from sqlalchemy import create_engine, inspect
    from .models import VirtualMachine
    
    engine = create_engine(db_url, echo=False)
    inspector = inspect(engine)
    
    # Define column categories
    categories = {
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
    
    # Get column information
    try:
        columns = inspector.get_columns("virtual_machines")
    except Exception:
        click.echo("⚠ Database table does not exist. Load data first.", err=True)
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
        indexes = inspector.get_indexes("virtual_machines")
        is_indexed = any(col["name"] in idx["column_names"] for idx in indexes)
        
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
    click.echo(f"\n=== VirtualMachine Schema ({len(column_info)} columns) ===")
    
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
    default="sqlite:///vmware_inventory.db",
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
    default="sqlite:///vmware_inventory.db",
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


if __name__ == "__main__":
    cli()
