"""CLI commands for VM naming convention management."""

import click
import json
from pathlib import Path
from typing import Optional
from tabulate import tabulate
import pandas as pd


@click.group(name="naming-convention")
def naming_convention():
    """Manage VM naming conventions and analyze VM inventory."""
    pass


@naming_convention.command(name="list")
@click.option(
    "--db-url",
    default="sqlite:///data/vmware_inventory.db",
    help="Database URL",
    show_default=True,
)
@click.option(
    "--active-only",
    is_flag=True,
    help="Show only active conventions",
)
@click.option(
    "--format",
    type=click.Choice(["table", "json"], case_sensitive=False),
    default="table",
    help="Output format",
)
def list_conventions(db_url: str, active_only: bool, format: str):
    """List all naming conventions."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from src.services.naming_convention_service import NamingConventionService

    engine = create_engine(db_url, echo=False)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    try:
        service = NamingConventionService(session)
        conventions = service.list_conventions(active_only=active_only)

        if not conventions:
            click.echo("No naming conventions found.")
            return

        if format == "json":
            data = []
            for convention in conventions:
                data.append(
                    {
                        "id": convention.id,
                        "name": convention.name,
                        "pattern": convention.pattern,
                        "total_length": convention.total_length,
                        "is_active": convention.is_active,
                        "field_count": len(convention.fields),
                        "created_at": convention.created_at.isoformat() if convention.created_at else None,
                    }
                )
            click.echo(json.dumps(data, indent=2))
        else:
            # Table format
            table_data = []
            for convention in conventions:
                table_data.append(
                    [
                        convention.id,
                        convention.name,
                        convention.pattern,
                        convention.total_length,
                        len(convention.fields),
                        "✓" if convention.is_active else "✗",
                    ]
                )

            headers = ["ID", "Name", "Pattern", "Length", "Fields", "Active"]
            click.echo("\n" + tabulate(table_data, headers=headers, tablefmt="grid"))
            click.echo()

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()
    finally:
        session.close()


@naming_convention.command(name="show")
@click.argument("convention_id", type=int)
@click.option(
    "--db-url",
    default="sqlite:///data/vmware_inventory.db",
    help="Database URL",
    show_default=True,
)
def show_convention(convention_id: int, db_url: str):
    """Show detailed information about a naming convention."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from src.services.naming_convention_service import NamingConventionService

    engine = create_engine(db_url, echo=False)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    try:
        service = NamingConventionService(session)
        convention = service.get_convention(convention_id)

        if not convention:
            click.echo(f"❌ Convention with ID {convention_id} not found.")
            raise click.Abort()

        click.echo(f"\n{'='*60}")
        click.echo(f"Naming Convention: {convention.name}")
        click.echo(f"{'='*60}")
        click.echo(f"ID:          {convention.id}")
        click.echo(f"Pattern:     {convention.pattern}")
        click.echo(f"Length:      {convention.total_length} characters")
        click.echo(f"Active:      {'Yes' if convention.is_active else 'No'}")
        click.echo(f"Created:     {convention.created_at}")

        if convention.description:
            click.echo(f"Description: {convention.description}")

        click.echo(f"\n{'Field Definitions:'}")
        click.echo(f"{'-'*60}")

        if convention.fields:
            # Display summary table
            field_data = []
            for field in sorted(convention.fields, key=lambda f: f.position):
                possible_values = field.possible_values if isinstance(field.possible_values, list) else []
                values_preview = (
                    ", ".join(possible_values[:3]) + ("..." if len(possible_values) > 3 else "")
                    if possible_values
                    else "-"
                )
                field_data.append(
                    [
                        field.position,
                        field.field_name,
                        field.length,
                        "✓" if field.is_required else "✗",
                        values_preview,
                    ]
                )

            headers = ["Pos", "Field Name", "Length", "Required", "Sample Values"]
            click.echo(tabulate(field_data, headers=headers, tablefmt="grid"))

            # Display detailed field information
            click.echo(f"\n{'Detailed Field Information:'}")
            click.echo(f"{'-'*60}")

            for field in sorted(convention.fields, key=lambda f: f.position):
                click.echo(f"\n📍 Position {field.position}: {field.field_name} (ID: {field.id})")
                click.echo(f"   Convention: {field.convention_id}")
                click.echo(f"   Length:     {field.length} character(s)")
                click.echo(f"   Required:   {'Yes' if field.is_required else 'No'}")

                if field.description:
                    click.echo(f"   Description: {field.description}")

                if field.validation_regex:
                    click.echo(f"   Validation:  {field.validation_regex}")

                if field.possible_values:
                    possible_values = field.possible_values if isinstance(field.possible_values, list) else []
                    if possible_values:
                        if len(possible_values) <= 10:
                            click.echo(f"   Values:      {', '.join(possible_values)}")
                        else:
                            click.echo(f"   Values:      {', '.join(possible_values[:10])}")
                            click.echo(f"                ... and {len(possible_values) - 10} more")

                click.echo(f"   Created:     {field.created_at}")
        else:
            click.echo("No fields defined.")

        click.echo()

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()
    finally:
        session.close()


@naming_convention.command(name="create")
@click.option(
    "--db-url",
    default="sqlite:///data/vmware_inventory.db",
    help="Database URL",
    show_default=True,
)
@click.option(
    "--from-file",
    type=click.Path(exists=True, path_type=Path),
    help="Load convention definition from JSON file",
)
def create_convention(db_url: str, from_file: Optional[Path]):
    """Create a new naming convention interactively or from a file."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from src.services.naming_convention_service import NamingConventionService, PatternValidationError

    engine = create_engine(db_url, echo=False)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    try:
        service = NamingConventionService(session)

        if from_file:
            # Load from file
            with open(from_file, "r") as f:
                data = json.load(f)

            name = data["name"]
            pattern = data["pattern"]
            fields = data["fields"]
            description = data.get("description")
        else:
            # Interactive mode
            click.echo("\n📝 Create New Naming Convention\n")

            name = click.prompt("Convention name")
            pattern = click.prompt("Pattern (e.g., <D><Y><K><S><XXX><YYY>)")
            description = click.prompt("Description (optional)", default="", show_default=False)
            description = description if description else None

            click.echo("\n📊 Define fields (in order):")
            click.echo("Enter field details. Press Ctrl+C when done.\n")

            fields = []
            position = 0

            try:
                while True:
                    click.echo(f"--- Field {position + 1} ---")
                    field_name = click.prompt(f"  Field name")
                    length = click.prompt(f"  Length", type=int)
                    is_required = click.confirm(f"  Required?", default=True)
                    field_desc = click.prompt(f"  Description (optional)", default="", show_default=False)

                    # Optional: possible values
                    add_values = click.confirm(f"  Add possible values?", default=False)
                    possible_values = None
                    if add_values:
                        values_str = click.prompt(f"  Possible values (comma-separated)")
                        possible_values = [v.strip() for v in values_str.split(",")]

                    fields.append(
                        {
                            "field_name": field_name,
                            "position": position,
                            "length": length,
                            "is_required": is_required,
                            "description": field_desc if field_desc else None,
                            "possible_values": possible_values,
                        }
                    )

                    position += 1
                    click.echo()

                    if not click.confirm("Add another field?", default=True):
                        break

            except (KeyboardInterrupt, EOFError):
                if not fields:
                    click.echo("\n❌ No fields defined. Aborting.")
                    raise click.Abort()

        # Create convention
        click.echo("\n💾 Creating naming convention...")
        convention = service.create_convention(name=name, pattern=pattern, fields=fields, description=description)

        click.echo(f"\n✅ Created naming convention '{convention.name}' (ID: {convention.id})")
        click.echo(f"   Pattern: {convention.pattern}")
        click.echo(f"   Fields: {len(convention.fields)}")
        click.echo()

    except PatternValidationError as e:
        click.echo(f"\n❌ Validation Error: {e}", err=True)
        raise click.Abort()
    except Exception as e:
        click.echo(f"\n❌ Error: {e}", err=True)
        raise click.Abort()
    finally:
        session.close()


@naming_convention.command(name="delete")
@click.argument("convention_id", type=int)
@click.option(
    "--db-url",
    default="sqlite:///data/vmware_inventory.db",
    help="Database URL",
    show_default=True,
)
@click.confirmation_option(prompt="This will delete the convention and all analysis data. Continue?")
def delete_convention(convention_id: int, db_url: str):
    """Delete a naming convention."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from src.services.naming_convention_service import NamingConventionService

    engine = create_engine(db_url, echo=False)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    try:
        service = NamingConventionService(session)

        # Check if convention exists
        convention = service.get_convention(convention_id)
        if not convention:
            click.echo(f"❌ Convention with ID {convention_id} not found.")
            raise click.Abort()

        click.echo(f"Deleting convention '{convention.name}'...")
        service.delete_convention(convention_id)

        click.echo(f"✅ Convention deleted successfully.")

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()
    finally:
        session.close()


@naming_convention.command(name="analyze")
@click.argument("convention_id", type=int)
@click.option(
    "--db-url",
    default="sqlite:///data/vmware_inventory.db",
    help="Database URL",
    show_default=True,
)
@click.option(
    "--datacenter",
    help="Filter VMs by datacenter",
)
@click.option(
    "--cluster",
    help="Filter VMs by cluster",
)
@click.option(
    "--batch-size",
    default=100,
    type=int,
    help="Number of VMs to process per batch",
)
def analyze_inventory(
    convention_id: int, db_url: str, datacenter: Optional[str], cluster: Optional[str], batch_size: int
):
    """Analyze VM inventory against a naming convention."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from src.services.naming_convention_service import NamingConventionService

    engine = create_engine(db_url, echo=False)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    try:
        service = NamingConventionService(session)

        # Check if convention exists
        convention = service.get_convention(convention_id)
        if not convention:
            click.echo(f"❌ Convention with ID {convention_id} not found.")
            raise click.Abort()

        click.echo(f"\n🔍 Analyzing VM inventory with convention '{convention.name}'")
        click.echo(f"   Pattern: {convention.pattern}\n")

        # Build filters
        vm_filter = {}
        if datacenter:
            vm_filter["datacenter"] = datacenter
            click.echo(f"   Filter: datacenter = {datacenter}")
        if cluster:
            vm_filter["cluster"] = cluster
            click.echo(f"   Filter: cluster = {cluster}")

        if vm_filter:
            click.echo()

        # Perform analysis
        with click.progressbar(length=100, label="Analyzing VMs") as bar:
            stats = service.analyze_vm_inventory(
                convention_id=convention_id, vm_filter=vm_filter if vm_filter else None, batch_size=batch_size
            )
            bar.update(100)

        click.echo(f"\n✅ Analysis complete!")
        click.echo(f"\n📊 Results:")
        click.echo(f"   Total VMs:     {stats['total']}")
        click.echo(
            f"   Valid:         {stats['valid']} ({stats['valid']/stats['total']*100:.1f}%)"
            if stats["total"] > 0
            else "   Valid:         0"
        )
        click.echo(
            f"   Invalid:       {stats['invalid']} ({stats['invalid']/stats['total']*100:.1f}%)"
            if stats["total"] > 0
            else "   Invalid:       0"
        )
        click.echo(f"   Created:       {stats['created']}")
        click.echo(f"   Updated:       {stats['updated']}")
        click.echo()

    except Exception as e:
        click.echo(f"\n❌ Error: {e}", err=True)
        raise click.Abort()
    finally:
        session.close()


@naming_convention.command(name="export")
@click.argument("convention_id", type=int)
@click.argument("output_file", type=click.Path(path_type=Path))
@click.option(
    "--db-url",
    default="sqlite:///data/vmware_inventory.db",
    help="Database URL",
    show_default=True,
)
@click.option(
    "--format",
    type=click.Choice(["csv", "excel", "json"], case_sensitive=False),
    default="csv",
    help="Export format",
)
@click.option(
    "--valid-only",
    is_flag=True,
    help="Export only valid analyses",
)
def export_analysis(convention_id: int, output_file: Path, db_url: str, format: str, valid_only: bool):
    """Export naming analysis results."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from src.services.naming_convention_service import NamingConventionService
    from src.models import VMNamingAnalysis, VirtualMachine

    engine = create_engine(db_url, echo=False)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    try:
        service = NamingConventionService(session)

        # Check if convention exists
        convention = service.get_convention(convention_id)
        if not convention:
            click.echo(f"❌ Convention with ID {convention_id} not found.")
            raise click.Abort()

        click.echo(f"\n📤 Exporting analysis for convention '{convention.name}'")

        # Query analyses
        query = (
            session.query(VMNamingAnalysis, VirtualMachine)
            .join(VirtualMachine, VMNamingAnalysis.vm_id == VirtualMachine.id)
            .filter(VMNamingAnalysis.convention_id == convention_id)
        )

        if valid_only:
            query = query.filter(VMNamingAnalysis.is_valid == True)

        analyses = query.all()

        if not analyses:
            click.echo("❌ No analysis data found.")
            raise click.Abort()

        # Build export data
        export_data = []
        for analysis, vm in analyses:
            row = {
                "vm_name": analysis.vm_name,
                "is_valid": analysis.is_valid,
                "datacenter": vm.datacenter,
                "cluster": vm.cluster,
                "powerstate": vm.powerstate,
            }

            # Add field values
            for field in sorted(convention.fields, key=lambda f: f.position):
                row[field.field_name] = analysis.field_values.get(field.field_name, "")

            export_data.append(row)

        # Export based on format
        df = pd.DataFrame(export_data)

        if format == "csv":
            df.to_csv(output_file, index=False)
        elif format == "excel":
            df.to_excel(output_file, index=False, sheet_name="Naming Analysis")
        elif format == "json":
            df.to_json(output_file, orient="records", indent=2)

        click.echo(f"✅ Exported {len(export_data)} records to {output_file}")
        click.echo()

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()
    finally:
        session.close()


@naming_convention.command(name="migration-groups")
@click.argument("convention_id", type=int)
@click.option(
    "--db-url",
    default="sqlite:///data/vmware_inventory.db",
    help="Database URL",
    show_default=True,
)
@click.option(
    "--group-by",
    multiple=True,
    help="Field names to group by (can specify multiple times)",
)
@click.option(
    "--format",
    type=click.Choice(["table", "json"], case_sensitive=False),
    default="table",
    help="Output format",
)
def migration_groups(convention_id: int, db_url: str, group_by: tuple, format: str):
    """Generate migration groups based on naming fields."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from src.services.naming_convention_service import NamingConventionService

    engine = create_engine(db_url, echo=False)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    try:
        service = NamingConventionService(session)

        # Check if convention exists
        convention = service.get_convention(convention_id)
        if not convention:
            click.echo(f"❌ Convention with ID {convention_id} not found.")
            raise click.Abort()

        if not group_by:
            click.echo("❌ Please specify at least one field to group by using --group-by")
            raise click.Abort()

        grouping_fields = list(group_by)

        click.echo(f"\n🔀 Generating migration groups for convention '{convention.name}'")
        click.echo(f"   Grouping by: {', '.join(grouping_fields)}\n")

        groups = service.generate_migration_groups(convention_id=convention_id, grouping_fields=grouping_fields)

        if not groups:
            click.echo("❌ No groups generated (no valid analyses found).")
            raise click.Abort()

        if format == "json":
            click.echo(json.dumps(groups, indent=2))
        else:
            # Table format
            table_data = []
            for idx, group in enumerate(groups, 1):
                group_key_str = ", ".join(f"{k}={v}" for k, v in group["group_key"].items())
                table_data.append(
                    [
                        idx,
                        group_key_str,
                        group["vm_count"],
                    ]
                )

            headers = ["#", "Group", "VM Count"]
            click.echo(tabulate(table_data, headers=headers, tablefmt="grid"))
            click.echo(f"\nTotal groups: {len(groups)}")
            click.echo()

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()
    finally:
        session.close()
