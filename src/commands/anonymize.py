"""Anonymization CLI commands."""

import click
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table
from rich.panel import Panel

console = Console()


@click.group()
def anonymize():
    """[BETA] Anonymize sensitive data for demos and documentation.
    
    ⚠️  This is a beta feature. Please test thoroughly before use in production.
    """
    pass


@anonymize.command()
@click.option(
    "--db-url",
    default="sqlite:///data/vmware_inventory.db",
    help="Source database URL",
    show_default=True,
)
@click.option(
    "--output",
    "-o",
    required=True,
    type=click.Path(path_type=Path),
    help="Output database file or URL",
)
@click.option(
    "--mapping-file",
    "-m",
    type=click.Path(path_type=Path),
    help="Save anonymization mapping to file (for potential reversal)",
)
@click.option(
    "--keep-subnet/--anonymize-subnet",
    default=True,
    help="Keep IP subnet structure (e.g., 10.20.x.x)",
    show_default=True,
)
@click.option(
    "--redact-annotations/--sanitize-annotations",
    default=False,
    help="Fully redact annotations vs sanitize sensitive patterns",
    show_default=True,
)
@click.option(
    "--preserve-env/--no-preserve-env",
    default=True,
    help="Preserve environment prefixes (PROD, DEV, etc.) in VM names",
    show_default=True,
)
@click.option(
    "--seed",
    default="vmware-anon",
    help="Seed for consistent anonymization (same seed = same results)",
    show_default=True,
)
@click.confirmation_option(
    prompt="This will create an anonymized copy of the database. Continue?"
)
def database(
    db_url: str,
    output: Path,
    mapping_file: Path | None,
    keep_subnet: bool,
    redact_annotations: bool,
    preserve_env: bool,
    seed: str,
):
    """[BETA] Anonymize entire database for demos and documentation.
    
    Creates a new database with anonymized data while preserving:
    - Resource metrics (CPU, memory, storage)
    - Relationships (datacenter -> cluster -> host -> VM)
    - Power states, OS types, configurations
    - Timestamps and dates
    
    Anonymizes:
    - VM names (PROD-APP-01 -> PROD-VM-001)
    - DNS names and IP addresses
    - Infrastructure names (datacenters, clusters, hosts)
    - Folder paths
    - Network names
    - Annotations (redacted or sanitized)
    - File paths
    
    Examples:
    
        # Anonymize with default settings
        cli anonymize database --output data/demo.db
        
        # Save mapping for reversal
        cli anonymize database --output data/demo.db --mapping-file mapping.json
        
        # Full anonymization (no subnet preservation)
        cli anonymize database --output data/demo.db --anonymize-subnet
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from src.models.vmware import VirtualMachine
    from src.models.base import Base
    from src.services.anonymization_service import AnonymizationService
    
    console.print("[yellow]⚠️  BETA: Anonymization is in beta. Please validate results carefully.[/yellow]\n")
    
    console.print(Panel.fit(
        "[bold cyan]🔐 Database Anonymization[/bold cyan] [yellow]\[BETA][/yellow]\\n"
        f"Source: {db_url}\\n"
        f"Output: {output}",
        border_style="cyan"
    ))
    
    try:
        # Connect to source database
        source_engine = create_engine(db_url, echo=False)
        SourceSession = sessionmaker(bind=source_engine)
        source_session = SourceSession()
        
        # Create output database
        output_url = f"sqlite:///{output}" if not output.as_posix().startswith("sqlite") else str(output)
        output_engine = create_engine(output_url, echo=False)
        Base.metadata.create_all(output_engine)
        OutputSession = sessionmaker(bind=output_engine)
        output_session = OutputSession()
        
        # Initialize anonymization service
        anon_service = AnonymizationService(seed=seed)
        
        options = {
            'keep_subnet': keep_subnet,
            'redact_annotations': redact_annotations,
            'preserve_env': preserve_env,
            'anonymize_paths': True,
        }
        
        # Get total VMs
        total_vms = source_session.query(VirtualMachine).count()
        
        console.print(f"\\n[cyan]Processing {total_vms} VMs...[/cyan]\\n")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console
        ) as progress:
            task = progress.add_task("[cyan]Anonymizing VMs...", total=total_vms)
            
            # Process in batches
            batch_size = 100
            offset = 0
            
            while offset < total_vms:
                vms = source_session.query(VirtualMachine).offset(offset).limit(batch_size).all()
                
                for vm in vms:
                    # Convert to dict
                    vm_dict = {
                        c.name: getattr(vm, c.name)
                        for c in vm.__table__.columns
                        if c.name != 'id'
                    }
                    
                    # Anonymize
                    anon_dict = anon_service.anonymize_vm_record(vm_dict, options)
                    
                    # Create new VM record
                    new_vm = VirtualMachine(**anon_dict)
                    output_session.add(new_vm)
                    
                    progress.advance(task)
                
                # Commit batch
                output_session.commit()
                offset += batch_size
            
            progress.update(task, description="[green]✓ Anonymization complete")
        
        # Save mapping if requested
        if mapping_file:
            mapping_file.parent.mkdir(parents=True, exist_ok=True)
            anon_service.mapping.save(mapping_file)
            console.print(f"\\n[green]✓ Mapping saved to: {mapping_file}[/green]")
        
        # Show statistics
        console.print()
        table = Table(title="Anonymization Summary", show_header=True, header_style="bold cyan")
        table.add_column("Item", style="cyan")
        table.add_column("Count", justify="right", style="yellow")
        
        table.add_row("VMs", str(len(anon_service.mapping.vm_names)))
        table.add_row("Datacenters", str(len(anon_service.mapping.datacenters)))
        table.add_row("Clusters", str(len(anon_service.mapping.clusters)))
        table.add_row("Hosts", str(len(anon_service.mapping.hosts)))
        table.add_row("IP Addresses", str(len(anon_service.mapping.ip_addresses)))
        table.add_row("Networks", str(len(anon_service.mapping.networks)))
        table.add_row("Folders", str(len(anon_service.mapping.folders)))
        
        console.print(table)
        
        console.print()
        console.print(Panel.fit(
            "[bold green]✅ Database anonymization complete![/bold green]\\n"
            f"Anonymized database: {output}\\n"
            f"Total VMs processed: {total_vms}",
            border_style="green"
        ))
        
        source_session.close()
        output_session.close()
        
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        import traceback
        traceback.print_exc()
        raise click.Abort()


@anonymize.command()
@click.argument("excel_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--output",
    "-o",
    required=True,
    type=click.Path(path_type=Path),
    help="Output Excel file",
)
@click.option(
    "--mapping-file",
    "-m",
    type=click.Path(path_type=Path),
    help="Save anonymization mapping to file",
)
@click.option(
    "--sheet",
    default="Sheet1",
    help="Excel sheet name or index to anonymize",
    show_default=True,
)
@click.option(
    "--list-sheets",
    is_flag=True,
    help="List available sheets and exit",
)
@click.option(
    "--keep-subnet/--anonymize-subnet",
    default=True,
    help="Keep IP subnet structure",
    show_default=True,
)
@click.option(
    "--seed",
    default="vmware-anon",
    help="Seed for consistent anonymization",
    show_default=True,
)
@click.option(
    "--fields",
    "-f",
    multiple=True,
    help="Specific fields to anonymize (can be used multiple times). If not specified, anonymizes all sensitive fields.",
)
@click.option(
    "--show-fields",
    is_flag=True,
    help="Show available fields and their anonymization status, then exit",
)
@click.option(
    "--list-columns",
    is_flag=True,
    help="List all columns in the Excel file with sample data, then exit",
)
@click.option(
    "--mapping-config",
    "-c",
    type=click.Path(exists=True, path_type=Path),
    help="Custom column mapping configuration file (.yaml/.yml/.json)",
)
@click.option(
    "--generate-mapping-template",
    "-t",
    type=click.Path(path_type=Path),
    help="Generate template mapping configuration and exit",
)
def excel(
    excel_file: Path,
    output: Path,
    mapping_file: Path | None,
    sheet: str,
    list_sheets: bool,
    keep_subnet: bool,
    seed: str,
    fields: tuple,
    show_fields: bool,
    list_columns: bool,
    mapping_config: Path | None,
    generate_mapping_template: Path | None,
):
    """[BETA] Anonymize Excel file directly without database import.
    
    By default, anonymizes all sensitive fields. Use --fields to selectively anonymize.
    
    Examples:
    
        # List available sheets
        cli anonymize excel input.xlsx --list-sheets
        
        # Show available fields
        cli anonymize excel input.xlsx --show-fields
        
        # Anonymize all sensitive fields (default)
        cli anonymize excel input.xlsx --output anonymized.xlsx
        
        # Anonymize only VM names and IPs
        cli anonymize excel input.xlsx -o output.xlsx --fields vm --fields primary_ip_address
        
        # Anonymize infrastructure only
        cli anonymize excel input.xlsx -o output.xlsx -f datacenter -f cluster -f host
        
        # With mapping file
        cli anonymize excel input.xlsx -o output.xlsx -m mapping.json
    """
    import pandas as pd
    from src.services.anonymization_service import AnonymizationService
    from src.services.column_mapper import (
        ColumnMapper,
        ColumnMappingConfig,
        MappingResult,
    )
    
    console.print("[yellow]⚠️  BETA: Anonymization is in beta. Please validate results carefully.[/yellow]\n")
    
    # Generate mapping template if requested
    if generate_mapping_template:
        try:
            console.print(f"\n[cyan]Generating mapping template from {excel_file.name}...[/cyan]")
            ColumnMapper.generate_template(
                excel_file=excel_file,
                output_file=generate_mapping_template,
                sheet=sheet,
                include_samples=True
            )
            console.print(f"\n[green]✓ Template saved to: {generate_mapping_template}[/green]")
            console.print("\n[yellow]Next steps:[/yellow]")
            console.print(f"  1. Edit {generate_mapping_template.name} to customize column mappings")
            console.print(f"  2. Run anonymization with: --mapping-config {generate_mapping_template}")
            console.print()
            return
        except Exception as e:
            console.print(f"[red]❌ Error generating template: {e}[/red]")
            import traceback
            traceback.print_exc()
            raise click.Abort()
    
    # Define anonymizable fields (categorized for clarity)
    ANONYMIZABLE_FIELDS = {
        # === Identity & Naming ===
        'vm': 'VM Name',
        'dns_name': 'DNS Name',
        'vm_id': 'VM ID',
        'vm_uuid': 'VM UUID',
        
        # === Network ===
        'primary_ip_address': 'Primary IP Address',
        'network_1': 'Network 1',
        'network_2': 'Network 2',
        'network_3': 'Network 3',
        'network_4': 'Network 4',
        'network_5': 'Network 5',
        'network_6': 'Network 6',
        'network_7': 'Network 7',
        'network_8': 'Network 8',
        
        # === Infrastructure ===
        'datacenter': 'Datacenter',
        'cluster': 'Cluster',
        'host': 'ESXi Host',
        'folder': 'Folder Path',
        'resource_pool': 'Resource Pool',
        'vapp': 'vApp',
        
        # === Storage Paths ===
        'path': 'VM Path',
        'log_directory': 'Log Directory',
        'snapshot_directory': 'Snapshot Directory',
        'suspend_directory': 'Suspend Directory',
        
        # === Text/Notes ===
        'annotation': 'Annotation/Notes',
        'cluster_rules': 'Cluster Rules',
        'cluster_rule_names': 'Cluster Rule Names',
        
        # === Custom Fields ===
        'code_ccx': 'Custom Field: Code CCX',
        'vm_nbu': 'Custom Field: VM NBU (Backup)',
        'vm_orchid': 'Custom Field: VM Orchid',
        'licence_enforcement': 'Custom Field: Licence Enforcement',
        'env': 'Custom Field: Environment',
        
        # === SDK/Server Info ===
        'vi_sdk_server_type': 'vCenter Server Type',
        'vi_sdk_api_version': 'vCenter API Version',
    }
    
    # Mapping from common Excel headers to internal field names
    # This handles spaces, different casings, and common variations
    HEADER_MAPPINGS = {
        # VM/Name variations
        'vm': 'vm',
        'vm name': 'vm',
        'name': 'vm',
        'virtual machine': 'vm',
        
        # DNS variations
        'dns_name': 'dns_name',
        'dns name': 'dns_name',
        'dns': 'dns_name',
        'hostname': 'dns_name',
        'host name': 'dns_name',
        
        # IP variations
        'primary_ip_address': 'primary_ip_address',
        'primary ip address': 'primary_ip_address',
        'ip address': 'primary_ip_address',
        'ip': 'primary_ip_address',
        'primary ip': 'primary_ip_address',
        
        # VM ID/UUID
        'vm_id': 'vm_id',
        'vm id': 'vm_id',
        'vm_uuid': 'vm_uuid',
        'vm uuid': 'vm_uuid',
        'uuid': 'vm_uuid',
        
        # Infrastructure
        'datacenter': 'datacenter',
        'data center': 'datacenter',
        'dc': 'datacenter',
        'cluster': 'cluster',
        'host': 'host',
        'esxi host': 'host',
        'esx host': 'host',
        'folder': 'folder',
        'resource_pool': 'resource_pool',
        'resource pool': 'resource_pool',
        'vapp': 'vapp',
        'v app': 'vapp',
        
        # Networks
        'network_1': 'network_1',
        'network 1': 'network_1',
        'network_2': 'network_2',
        'network 2': 'network_2',
        'network_3': 'network_3',
        'network 3': 'network_3',
        'network_4': 'network_4',
        'network 4': 'network_4',
        'network_5': 'network_5',
        'network 5': 'network_5',
        'network_6': 'network_6',
        'network 6': 'network_6',
        'network_7': 'network_7',
        'network 7': 'network_7',
        'network_8': 'network_8',
        'network 8': 'network_8',
        
        # Paths
        'path': 'path',
        'vm path': 'path',
        'log_directory': 'log_directory',
        'log directory': 'log_directory',
        'snapshot_directory': 'snapshot_directory',
        'snapshot directory': 'snapshot_directory',
        'suspend_directory': 'suspend_directory',
        'suspend directory': 'suspend_directory',
        
        # Text/Notes
        'annotation': 'annotation',
        'annotations': 'annotation',
        'notes': 'annotation',
        'cluster_rules': 'cluster_rules',
        'cluster rules': 'cluster_rules',
        'cluster_rule_names': 'cluster_rule_names',
        'cluster rule names': 'cluster_rule_names',
        
        # Custom fields
        'code_ccx': 'code_ccx',
        'code ccx': 'code_ccx',
        'vm_nbu': 'vm_nbu',
        'vm nbu': 'vm_nbu',
        'vm_orchid': 'vm_orchid',
        'vm orchid': 'vm_orchid',
        'licence_enforcement': 'licence_enforcement',
        'licence enforcement': 'licence_enforcement',
        'license enforcement': 'licence_enforcement',
        'env': 'env',
        'environment': 'env',
        
        # SDK/Server
        'vi_sdk_server_type': 'vi_sdk_server_type',
        'vi sdk server type': 'vi_sdk_server_type',
        'sdk server type': 'vi_sdk_server_type',
        'vi_sdk_api_version': 'vi_sdk_api_version',
        'vi sdk api version': 'vi_sdk_api_version',
        'sdk api version': 'vi_sdk_api_version',
        
        # === Network ===
        'primary_ip_address': 'Primary IP Address',
        'network_1': 'Network 1',
        'network_2': 'Network 2',
        'network_3': 'Network 3',
        'network_4': 'Network 4',
        'network_5': 'Network 5',
        'network_6': 'Network 6',
        'network_7': 'Network 7',
        'network_8': 'Network 8',
        
        # === Infrastructure ===
        'datacenter': 'Datacenter',
        'cluster': 'Cluster',
        'host': 'ESXi Host',
        'folder': 'Folder Path',
        'resource_pool': 'Resource Pool',
        'vapp': 'vApp',
        
        # === Storage Paths ===
        'path': 'VM Path',
        'log_directory': 'Log Directory',
        'snapshot_directory': 'Snapshot Directory',
        'suspend_directory': 'Suspend Directory',
        
        # === Text/Notes ===
        'annotation': 'Annotation/Notes',
        'cluster_rules': 'Cluster Rules',
        'cluster_rule_names': 'Cluster Rule Names',
        
        # === Custom Fields ===
        'code_ccx': 'Custom Field: Code CCX',
        'vm_nbu': 'Custom Field: VM NBU (Backup)',
        'vm_orchid': 'Custom Field: VM Orchid',
        'licence_enforcement': 'Custom Field: Licence Enforcement',
        'env': 'Custom Field: Environment',
        
        # === SDK/Server Info ===
        'vi_sdk_server_type': 'vCenter Server Type',
        'vi_sdk_api_version': 'vCenter API Version',
    }
    
    # List sheets if requested
    if list_sheets:
        try:
            xl_file = pd.ExcelFile(excel_file)
            sheets = xl_file.sheet_names
            console.print(f"\\n[bold cyan]📊 Available sheets in {excel_file.name}:[/bold cyan]\\n")
            for idx, sheet_name in enumerate(sheets):
                console.print(f"  [cyan]{idx}:[/cyan] {sheet_name}")
            console.print()
            return
        except Exception as e:
            console.print(f"[red]❌ Error reading Excel file: {e}[/red]")
            raise click.Abort()
    
    # List all columns with sample data if requested
    if list_columns:
        try:
            df = pd.read_excel(excel_file, sheet_name=sheet, nrows=3)
            
            console.print(f"\\n[bold cyan]📊 Columns in {excel_file.name} (Sheet: {sheet}):[/bold cyan]\\n")
            console.print(f"[yellow]Total columns: {len(df.columns)}[/yellow]\\n")
            
            table = Table(show_header=True, header_style="bold cyan", show_lines=True)
            table.add_column("#", style="dim", width=4, justify="right")
            table.add_column("Column Name", style="cyan")
            table.add_column("Sample Values (first 3 rows)", style="white")
            table.add_column("Data?", style="yellow", justify="center")
            
            for idx, col in enumerate(df.columns, 1):
                # Get sample values (non-null)
                samples = df[col].dropna().head(3).tolist()
                sample_str = ', '.join([str(s)[:40] for s in samples]) if samples else "[dim](empty)[/dim]"
                
                # Check if has any data
                has_data = "✓" if df[col].notna().any() else "✗"
                
                table.add_row(str(idx), col, sample_str, has_data)
            
            console.print(table)
            
            console.print("\\n[yellow]💡 Next steps:[/yellow]")
            console.print("  1. Review the column names above")
            console.print("  2. Use --show-fields to see which columns will be anonymized")
            console.print("  3. Run anonymization with --fields to select specific columns")
            console.print()
            console.print(f"  Example: cli anonymize excel {excel_file.name} -o output.xlsx -f 'Column Name' -f 'Another Column'")
            console.print()
            return
        except Exception as e:
            console.print(f"[red]❌ Error reading Excel file: {e}[/red]")
            import traceback
            traceback.print_exc()
            raise click.Abort()
    
    # Show available fields if requested
    if show_fields:
        # Read sample rows to check which fields exist and have data
        try:
            df_sample = pd.read_excel(excel_file, sheet_name=sheet, nrows=10)
            original_columns = {col.lower().strip(): col for col in df_sample.columns}
            df_sample.columns = df_sample.columns.str.lower().str.strip()
            
            # Map columns
            column_mapping = {}
            for col in df_sample.columns:
                if col in HEADER_MAPPINGS:
                    column_mapping[col] = HEADER_MAPPINGS[col]
                else:
                    column_mapping[col] = col
            
            df_sample = df_sample.rename(columns=column_mapping)
            
            console.print(f"\\n[bold cyan]📋 Anonymizable Fields in {excel_file.name}:[/bold cyan]\\n")
            
            table = Table(show_header=True, header_style="bold cyan")
            table.add_column("Internal Field", style="cyan", no_wrap=True)
            table.add_column("Excel Column", style="magenta")
            table.add_column("Description", style="white")
            table.add_column("Status", style="yellow", justify="center")
            
            for field_name, description in ANONYMIZABLE_FIELDS.items():
                # Check if field exists after mapping
                if field_name in df_sample.columns:
                    # Find original Excel column name
                    for orig_lower, orig_name in original_columns.items():
                        if column_mapping.get(orig_lower) == field_name:
                            excel_col = orig_name
                            break
                    else:
                        excel_col = field_name
                    
                    # Check if has non-null data
                    non_null_count = df_sample[field_name].notna().sum()
                    total_count = len(df_sample)
                    
                    if non_null_count == 0:
                        status = "✓ Empty"
                        style = "yellow"
                    elif non_null_count < total_count:
                        status = f"✓ {non_null_count}/{total_count}"
                        style = "green"
                    else:
                        status = "✓ Full"
                        style = "green"
                    
                    table.add_row(field_name, excel_col, description, f"[{style}]{status}[/{style}]")
                else:
                    table.add_row(field_name, "-", description, "[dim]✗ Missing[/dim]")
            
            console.print(table)
            console.print("\\n[yellow]💡 Legend:[/yellow]")
            console.print("  ✓ Full    - Column exists with all values populated")
            console.print("  ✓ #/#     - Column exists with some values populated")
            console.print("  ✓ Empty   - Column exists but no values")
            console.print("  ✗ Missing - Column not found in file")
            console.print("\\n[yellow]💡 Usage:[/yellow]")
            console.print("  # Anonymize specific fields:")
            console.print(f"  cli anonymize excel {excel_file.name} -o output.xlsx -f vm -f datacenter -f cluster")
            console.print("\\n  # Anonymize all fields with data (default):")
            console.print(f"  cli anonymize excel {excel_file.name} -o output.xlsx")
            console.print()
            return
        except Exception as e:
            console.print(f"[red]❌ Error reading Excel file: {e}[/red]")
            import traceback
            traceback.print_exc()
            raise click.Abort()
    
    console.print(Panel.fit(
        "[bold cyan]📊 Excel Anonymization[/bold cyan] [yellow]\[BETA][/yellow]\\n"
        f"Input: {excel_file}\\n"
        f"Sheet: {sheet}\\n"
        f"Output: {output}",
        border_style="cyan"
    ))
    
    try:
        # Read Excel
        console.print("\\n[cyan]Reading Excel file...[/cyan]")
        
        # Try to parse sheet as integer index first
        try:
            sheet_name_or_idx = int(sheet)
            df = pd.read_excel(excel_file, sheet_name=sheet_name_or_idx)
            console.print(f"[green]✓ Loaded sheet at index {sheet_name_or_idx}[/green]")
        except ValueError:
            # Not an integer, treat as sheet name
            df = pd.read_excel(excel_file, sheet_name=sheet)
            console.print(f"[green]✓ Loaded sheet '{sheet}'[/green]")
        
        # Initialize anonymization
        anon_service = AnonymizationService(seed=seed)
        
        # Determine which fields to anonymize
        selected_fields = set(fields) if fields else set(ANONYMIZABLE_FIELDS.keys())
        
        # Validate selected fields
        invalid_fields = selected_fields - set(ANONYMIZABLE_FIELDS.keys())
        if invalid_fields:
            console.print(f"[red]❌ Invalid field(s): {', '.join(invalid_fields)}[/red]")
            console.print("\\n[yellow]Use --show-fields to see available fields[/yellow]")
            raise click.Abort()
        
        options = {
            'keep_subnet': keep_subnet,
            'redact_annotations': False,
            'anonymize_paths': True,
            'selected_fields': selected_fields,  # Pass selected fields
        }
        
        # Initialize column mapper
        custom_config = None
        if mapping_config:
            console.print(f"\n[cyan]Loading custom column mappings from {mapping_config}...[/cyan]")
            custom_config = ColumnMappingConfig.from_file(mapping_config)
            if custom_config.description:
                console.print(f"[dim]  {custom_config.description}[/dim]")
        
        column_mapper = ColumnMapper(custom_config=custom_config, use_defaults=True)
        
        # Map columns
        df, mapping_result = column_mapper.map_columns(
            df,
            expected_fields=set(ANONYMIZABLE_FIELDS.keys())
        )
        
        # Show mapping results
        if mapping_result.mapped:
            console.print(f"\n[green]✓ Mapped {len(mapping_result.mapped)} columns[/green]")
            if len(mapping_result.mapped) <= 10:
                for excel_col, internal_field in sorted(mapping_result.mapped.items()):
                    console.print(f"  {excel_col} → {internal_field}")
            else:
                console.print(f"  (showing first 10 of {len(mapping_result.mapped)})")
                for excel_col, internal_field in sorted(list(mapping_result.mapped.items())[:10]):
                    console.print(f"  {excel_col} → {internal_field}")
        
        if mapping_result.conflicts:
            console.print(f"\n[yellow]⚠ Conflicts detected ({len(mapping_result.conflicts)} fields):[/yellow]")
            for internal_field, excel_cols in mapping_result.conflicts.items():
                console.print(f"  {internal_field} ← {', '.join(excel_cols)}")
            console.print("  [dim](First occurrence will be used)[/dim]")
        
        if mapping_result.unmapped_excel:
            console.print(f"\n[yellow]Unmapped columns ({len(mapping_result.unmapped_excel)}):[/yellow]")
            if len(mapping_result.unmapped_excel) <= 5:
                for col in mapping_result.unmapped_excel:
                    console.print(f"  • {col}")
            else:
                for col in mapping_result.unmapped_excel[:5]:
                    console.print(f"  • {col}")
                console.print(f"  ... and {len(mapping_result.unmapped_excel) - 5} more")
        
        # Determine which fields are actually in the Excel file (after mapping)
        available_anonymizable_fields = set(ANONYMIZABLE_FIELDS.keys()) & set(df.columns)
        
        # If no fields specified, default to all available anonymizable fields in the file
        if not fields:
            selected_fields = available_anonymizable_fields
            console.print(f"\n[cyan]Default mode: Anonymizing all sensitive fields found in file[/cyan]")
        
        # Show which fields will be anonymized
        fields_to_anonymize = selected_fields & set(df.columns)
        
        if fields_to_anonymize:
            console.print(f"\n[cyan]Fields to anonymize: {len(fields_to_anonymize)}[/cyan]")
            for field in sorted(fields_to_anonymize):
                console.print(f"  • {field}")
            
            # Show which selected fields are NOT in the file
            missing_fields = selected_fields - set(df.columns)
            if missing_fields:
                console.print(f"\n[yellow]⚠ Selected fields not found in file: {len(missing_fields)}[/yellow]")
                for field in sorted(missing_fields):
                    console.print(f"  ✗ {field}")
        else:
            console.print("\n[yellow]⚠ No matching fields found to anonymize![/yellow]")
            console.print(f"\nSelected fields: {', '.join(sorted(selected_fields)[:5])}...")
            console.print(f"Available columns: {', '.join(sorted(df.columns)[:10])}...")
            console.print("\n[yellow]Tip: Use --show-fields to see available fields[/yellow]")
        
        console.print(f"\n[cyan]Processing {len(df)} rows...[/cyan]\n")
        
        # Anonymize each row
        anonymized_rows = []
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console
        ) as progress:
            task = progress.add_task("[cyan]Anonymizing rows...", total=len(df))
            
            for _, row in df.iterrows():
                anon_row = anon_service.anonymize_vm_record(row.to_dict(), options)
                anonymized_rows.append(anon_row)
                progress.advance(task)
        
        # Create output DataFrame
        anon_df = pd.DataFrame(anonymized_rows)
        
        # Save to Excel
        output.parent.mkdir(parents=True, exist_ok=True)
        anon_df.to_excel(output, index=False)
        
        # Save mapping with statistics
        if mapping_file:
            mapping_file.parent.mkdir(parents=True, exist_ok=True)
            anon_service.mapping.save(mapping_file)
            
            # Show mapping statistics
            console.print(f"\n[green]✓ Mapping saved to: {mapping_file}[/green]")
            console.print(f"\n[cyan]Mapping Statistics:[/cyan]")
            console.print(f"  • VM Names: {len(anon_service.mapping.vm_names)}")
            console.print(f"  • VM IDs: {len(anon_service.mapping.vm_ids)}")
            console.print(f"  • VM UUIDs: {len(anon_service.mapping.vm_uuids)}")
            console.print(f"  • DNS Names: {len(anon_service.mapping.dns_names)}")
            console.print(f"  • IP Addresses: {len(anon_service.mapping.ip_addresses)}")
            console.print(f"  • Datacenters: {len(anon_service.mapping.datacenters)}")
            console.print(f"  • Clusters: {len(anon_service.mapping.clusters)}")
            console.print(f"  • Hosts: {len(anon_service.mapping.hosts)}")
            console.print(f"  • Resource Pools: {len(anon_service.mapping.resource_pools)}")
            console.print(f"  • Networks: {len(anon_service.mapping.networks)}")
        
        console.print()
        console.print(Panel.fit(
            "[bold green]✅ Excel anonymization complete![/bold green]\\n"
            f"Anonymized file: {output}\\n"
            f"Rows processed: {len(df)}",
            border_style="green"
        ))
        
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        import traceback
        traceback.print_exc()
        raise click.Abort()


@anonymize.command()
@click.argument("mapping_file", type=click.Path(exists=True, path_type=Path))
def show_mapping(mapping_file: Path):
    """[BETA] Display anonymization mapping from file.
    
    Examples:
    
        cli anonymize show-mapping mapping.json
    """
    from src.services.anonymization_service import AnonymizationMapping
    
    console.print("[yellow]⚠️  BETA: Anonymization is in beta. Please validate results carefully.[/yellow]\n")
    
    try:
        mapping = AnonymizationMapping.load(mapping_file)
        
        console.print(f"\\n[bold cyan]Anonymization Mapping: {mapping_file}[/bold cyan]\\n")
        
        # VM Names
        if mapping.vm_names:
            table = Table(title="VM Names", show_header=True, header_style="bold cyan")
            table.add_column("Original", style="yellow")
            table.add_column("Anonymized", style="green")
            for orig, anon in list(mapping.vm_names.items())[:10]:
                table.add_row(orig, anon)
            if len(mapping.vm_names) > 10:
                table.add_row(f"... and {len(mapping.vm_names) - 10} more", "")
            console.print(table)
            console.print()
        
        # Infrastructure
        if mapping.datacenters or mapping.clusters or mapping.hosts:
            table = Table(title="Infrastructure", show_header=True, header_style="bold cyan")
            table.add_column("Type", style="cyan")
            table.add_column("Original", style="yellow")
            table.add_column("Anonymized", style="green")
            
            for dc_orig, dc_anon in mapping.datacenters.items():
                table.add_row("Datacenter", dc_orig, dc_anon)
            for cl_orig, cl_anon in mapping.clusters.items():
                table.add_row("Cluster", cl_orig, cl_anon)
            for h_orig, h_anon in list(mapping.hosts.items())[:5]:
                table.add_row("Host", h_orig, h_anon)
            
            console.print(table)
            console.print()
        
        # Summary
        summary = Table(title="Summary", show_header=True, header_style="bold cyan")
        summary.add_column("Category", style="cyan")
        summary.add_column("Count", justify="right", style="yellow")
        
        summary.add_row("VMs", str(len(mapping.vm_names)))
        summary.add_row("IP Addresses", str(len(mapping.ip_addresses)))
        summary.add_row("Datacenters", str(len(mapping.datacenters)))
        summary.add_row("Clusters", str(len(mapping.clusters)))
        summary.add_row("Hosts", str(len(mapping.hosts)))
        summary.add_row("Networks", str(len(mapping.networks)))
        summary.add_row("Folders", str(len(mapping.folders)))
        
        console.print(summary)
        
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        raise click.Abort()
