"""CLI for VMware inventory management."""

import click
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


if __name__ == "__main__":
    cli()
