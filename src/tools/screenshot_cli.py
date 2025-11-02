#!/usr/bin/env python3
"""
Screenshot CLI - Command-line interface for dashboard screenshot automation.

This provides a user-friendly Click-based CLI for capturing dashboard screenshots.

Usage:
    screenshot-cli capture --all
    screenshot-cli capture --page Overview --theme dark
    screenshot-cli serve --port 8501
"""

import sys
import time
import subprocess
from pathlib import Path
from typing import Optional, List

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.panel import Panel

# Import from same package
from .screenshot_dashboard import DashboardScreenshotter

console = Console()


@click.group()
@click.version_option(version="0.7.0", prog_name="screenshot-cli")
def cli():
    """VMware Dashboard Screenshot Automation CLI.
    
    Capture dashboard screenshots for documentation with ease.
    """
    pass


@cli.command()
@click.option(
    "--url",
    default="http://localhost:8501",
    help="Dashboard URL",
    show_default=True
)
@click.option(
    "--output",
    "-o",
    default="docs/images/screenshots",
    type=click.Path(),
    help="Output directory",
    show_default=True
)
@click.option(
    "--page",
    "-p",
    help="Specific page to capture (e.g., 'Overview', 'Data Explorer')"
)
@click.option(
    "--theme",
    "-t",
    type=click.Choice(["light", "dark", "both"]),
    default="both",
    help="Theme(s) to capture",
    show_default=True
)
@click.option(
    "--all",
    "-a",
    "capture_all",
    is_flag=True,
    help="Capture all pages (tour mode)"
)
@click.option(
    "--headless/--no-headless",
    default=True,
    help="Run browser in headless mode",
    show_default=True
)
@click.option(
    "--wait",
    "-w",
    default=2,
    type=int,
    help="Wait time after page load (seconds)",
    show_default=True
)
@click.option(
    "--use-uri/--use-ui",
    default=True,
    help="Use direct URI navigation (faster) or UI button clicks",
    show_default=True
)
def capture(
    url: str,
    output: str,
    page: Optional[str],
    theme: str,
    capture_all: bool,
    headless: bool,
    wait: int,
    use_uri: bool
):
    """Capture dashboard screenshots.
    
    Examples:
    
        # Capture all pages in both themes
        screenshot-cli capture --all
        
        # Capture specific page in dark mode
        screenshot-cli capture --page "Data Explorer" --theme dark
        
        # Capture to custom directory
        screenshot-cli capture --all --output docs/images/v0.7.0
    """
    console.print(Panel.fit(
        "[bold cyan]📸 VMware Dashboard Screenshot Tool[/bold cyan]\n"
        f"URL: {url}\n"
        f"Output: {output}\n"
        f"Theme: {theme}\n"
        f"Navigation: {'Direct URI' if use_uri else 'UI Buttons'}",
        border_style="cyan"
    ))
    
    # Validate options
    if not capture_all and not page:
        console.print("[red]❌ Error: Must specify --page or --all[/red]")
        raise click.Abort()
    
    output_path = Path(output)
    output_path.mkdir(parents=True, exist_ok=True)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        
        # Check if dashboard is running
        task = progress.add_task("[cyan]Checking dashboard...", total=None)
        import requests
        try:
            requests.get(url, timeout=5)
            progress.update(task, description="[green]✓ Dashboard is running")
            progress.stop_task(task)
        except requests.exceptions.RequestException:
            progress.stop()
            console.print(f"[red]❌ Dashboard not accessible at {url}[/red]")
            console.print("\n[yellow]Start the dashboard first:[/yellow]")
            console.print(f"  streamlit run src/dashboard/app.py --server.port {url.split(':')[-1]}")
            raise click.Abort()
        
        # Initialize screenshotter
        task = progress.add_task("[cyan]Starting browser...", total=None)
        screenshotter = DashboardScreenshotter(
            base_url=url,
            output_dir=output_path,
            headless=headless
        )
        
        try:
            screenshotter.start_browser()
            progress.update(task, description="[green]✓ Browser started")
            progress.stop_task(task)
            
            # Navigate to dashboard
            task = progress.add_task("[cyan]Loading dashboard...", total=None)
            screenshotter.driver.get(url)
            
            if not screenshotter.wait_for_streamlit(timeout=10):
                progress.stop()
                console.print("[red]❌ Failed to load dashboard[/red]")
                raise click.Abort()
            
            progress.update(task, description="[green]✓ Dashboard loaded")
            progress.stop_task(task)
            time.sleep(wait)
            
            # Capture screenshots
            if capture_all:
                # Get all 20 pages from API-ENDPOINTS.md
                pages = [name for name, _ in screenshotter.get_all_pages_from_api_endpoints()]
                
                total_screenshots = len(pages) * (2 if theme == "both" else 1)
                
                task = progress.add_task(
                    f"[cyan]Capturing {total_screenshots} screenshots...",
                    total=total_screenshots
                )
                
                for pg in pages:
                    if screenshotter.navigate_to_page(pg, use_uri=use_uri):
                        themes = ["light", "dark"] if theme == "both" else [theme]
                        
                        for t in themes:
                            if t == "dark" and theme == "both":
                                screenshotter.toggle_theme()
                                time.sleep(1)
                            
                            filename = f"{pg.lower().replace(' ', '_')}_{t}"
                            screenshotter.capture_screenshot(filename)
                            progress.advance(task)
                            
                            if t == "dark" and theme == "both":
                                screenshotter.toggle_theme()
                                time.sleep(1)
                
                progress.update(task, description="[green]✓ All screenshots captured")
            
            else:
                # Single page capture
                themes_list = ["light", "dark"] if theme == "both" else [theme]
                task = progress.add_task(
                    f"[cyan]Capturing {page}...",
                    total=len(themes_list)
                )
                
                if screenshotter.navigate_to_page(page, use_uri=use_uri):
                    for t in themes_list:
                        if t == "dark":
                            screenshotter.toggle_theme()
                            time.sleep(1)
                        
                        filename = f"{page.lower().replace(' ', '_')}_{t}"
                        screenshotter.capture_screenshot(filename)
                        progress.advance(task)
                        
                        if t == "dark" and theme == "both":
                            screenshotter.toggle_theme()
                            time.sleep(1)
                    
                    progress.update(task, description=f"[green]✓ {page} captured")
                else:
                    progress.stop()
                    console.print(f"[red]❌ Failed to navigate to {page}[/red]")
                    raise click.Abort()
        
        finally:
            screenshotter.stop_browser()
    
    # Show results
    console.print()
    console.print(Panel.fit(
        f"[bold green]✅ Screenshots saved to:[/bold green]\n{output_path.absolute()}",
        border_style="green"
    ))


@cli.command()
@click.option(
    "--port",
    "-p",
    default=8501,
    type=int,
    help="Port to run dashboard on",
    show_default=True
)
@click.option(
    "--wait",
    "-w",
    default=5,
    type=int,
    help="Seconds to wait before dashboard is ready",
    show_default=True
)
def serve(port: int, wait: int):
    """Start the dashboard server.
    
    Examples:
    
        # Start on default port
        screenshot-cli serve
        
        # Start on custom port
        screenshot-cli serve --port 8502
    """
    console.print(Panel.fit(
        f"[bold cyan]🚀 Starting Dashboard Server[/bold cyan]\n"
        f"Port: {port}",
        border_style="cyan"
    ))
    
    try:
        # Start Streamlit in background using python -m for pipx compatibility
        process = subprocess.Popen(
            [
                sys.executable, "-m", "streamlit", "run",
                "src/dashboard/app.py",
                f"--server.port={port}",
                "--server.headless=true"
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task(f"[cyan]Starting server on port {port}...", total=None)
            time.sleep(wait)
            progress.update(task, description=f"[green]✓ Server running on http://localhost:{port}")
        
        console.print()
        console.print("[green]✅ Dashboard is ready![/green]")
        console.print(f"[cyan]📍 URL: http://localhost:{port}[/cyan]")
        console.print("\n[yellow]Press Ctrl+C to stop the server[/yellow]")
        
        # Keep process running
        process.wait()
    
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠ Stopping server...[/yellow]")
        process.terminate()
        process.wait()
        console.print("[green]✓ Server stopped[/green]")
    
    except FileNotFoundError:
        console.print("[red]❌ Streamlit not found in PATH[/red]")
        console.print("\nInstall streamlit:")
        console.print("  pip install streamlit")
        console.print("  # OR install with dashboard dependencies:")
        console.print("  pipx install --force '.[dashboard]'")
        raise click.Abort()


@cli.command()
@click.option(
    "--output",
    "-o",
    default="docs/images/screenshots",
    type=click.Path(exists=True),
    help="Screenshots directory",
    show_default=True
)
def list(output: str):
    """List captured screenshots.
    
    Examples:
    
        screenshot-cli list
        screenshot-cli list --output docs/images/v0.7.0
    """
    output_path = Path(output)
    
    if not output_path.exists():
        console.print(f"[yellow]⚠ Directory not found: {output_path}[/yellow]")
        return
    
    screenshots = sorted(output_path.glob("*.png"))
    
    if not screenshots:
        console.print(f"[yellow]No screenshots found in {output_path}[/yellow]")
        return
    
    # Group by page and theme
    pages = {}
    for screenshot in screenshots:
        parts = screenshot.stem.rsplit("_", 1)
        if len(parts) == 2:
            page, theme = parts
            if page not in pages:
                pages[page] = {}
            pages[page][theme] = screenshot
    
    # Display table
    table = Table(title=f"Screenshots in {output_path}", show_header=True, header_style="bold cyan")
    table.add_column("Page", style="cyan", no_wrap=True)
    table.add_column("Light", style="white")
    table.add_column("Dark", style="white")
    table.add_column("Size", justify="right", style="yellow")
    
    for page, themes in sorted(pages.items()):
        light = "✓" if "light" in themes else "✗"
        dark = "✓" if "dark" in themes else "✗"
        
        # Get file size
        sizes = [f.stat().st_size for f in themes.values()]
        total_size = sum(sizes)
        size_str = f"{total_size / 1024:.1f} KB"
        
        table.add_row(
            page.replace("_", " ").title(),
            light,
            dark,
            size_str
        )
    
    console.print(table)
    console.print(f"\n[green]Total: {len(screenshots)} screenshots[/green]")


@cli.command()
@click.option(
    "--port",
    "-p",
    default=8501,
    type=int,
    help="Dashboard port",
    show_default=True
)
@click.option(
    "--output",
    "-o",
    default="docs/images/screenshots",
    type=click.Path(),
    help="Output directory",
    show_default=True
)
@click.option(
    "--theme",
    "-t",
    type=click.Choice(["light", "dark", "both"]),
    default="both",
    help="Theme(s) to capture",
    show_default=True
)
@click.option(
    "--wait-server",
    default=5,
    type=int,
    help="Seconds to wait for server to start",
    show_default=True
)
@click.option(
    "--wait-page",
    default=2,
    type=int,
    help="Seconds to wait after page load",
    show_default=True
)
def auto(port: int, output: str, theme: str, wait_server: int, wait_page: int):
    """Start server, capture screenshots, then stop.
    
    All-in-one command that handles everything automatically.
    
    Examples:
    
        # Complete automated run
        screenshot-cli auto
        
        # Custom output directory
        screenshot-cli auto --output docs/images/v0.7.0
    """
    console.print(Panel.fit(
        "[bold cyan]🤖 Automated Screenshot Capture[/bold cyan]\n"
        "Starting server → Capturing screenshots → Stopping server",
        border_style="cyan"
    ))
    
    process = None
    
    try:
        # Start server
        console.print("\n[cyan]1/3 Starting dashboard server...[/cyan]")
        
        # Check if streamlit is available
        try:
            import streamlit
        except ImportError:
            console.print("\n[red]❌ Streamlit not installed[/red]")
            console.print("\n[yellow]The 'auto' command requires streamlit to be available.[/yellow]")
            console.print("\nInstall options:")
            console.print("  1. Install with dashboard dependencies:")
            console.print("     pipx install --force '.[dashboard,screenshots]'")
            console.print("\n  2. Use 'capture' command with running server:")
            console.print("     # Terminal 1: streamlit run src/dashboard/app.py")
            console.print("     # Terminal 2: vmware-screenshot capture --all")
            raise click.Abort()
        
        # Use python -m streamlit to work within pipx venv
        process = subprocess.Popen(
            [
                sys.executable, "-m", "streamlit", "run",
                "src/dashboard/app.py",
                f"--server.port={port}",
                "--server.headless=true"
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        time.sleep(wait_server)
        console.print("[green]✓ Server started[/green]")
        
        # Load pages from API-ENDPOINTS.md
        console.print(f"\n[cyan]2/4 Loading page list from API-ENDPOINTS.md...[/cyan]")
        
        url = f"http://localhost:{port}"
        output_path = Path(output)
        output_path.mkdir(parents=True, exist_ok=True)
        
        screenshotter = DashboardScreenshotter(
            base_url=url,
            output_dir=output_path,
            headless=True
        )
        
        # Get all 20 pages from API-ENDPOINTS.md (same list as 'pages' command)
        pages_list = [name for name, _ in screenshotter.get_all_pages_from_api_endpoints()]
        console.print(f"[green]✓ Loaded {len(pages_list)} pages from API-ENDPOINTS.md[/green]")
        
        # Capture screenshots for all pages
        console.print(f"\n[cyan]3/4 Capturing screenshots for {len(pages_list)} pages...[/cyan]")
        
        total_screenshots = len(pages_list) * (2 if theme == "both" else 1)
        
        try:
            screenshotter.start_browser()
            screenshotter.driver.get(url)
            
            if not screenshotter.wait_for_streamlit(timeout=10):
                console.print("[red]❌ Failed to load dashboard[/red]")
                raise click.Abort()
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task(
                    f"[cyan]Capturing {total_screenshots} screenshots...",
                    total=total_screenshots
                )
                
                for pg in pages_list:
                    # Use URI navigation (default, fast)
                    if screenshotter.navigate_to_page(pg, use_uri=True):
                        themes_list = ["light", "dark"] if theme == "both" else [theme]
                        
                        for t in themes_list:
                            if t == "dark" and theme == "both":
                                screenshotter.toggle_theme()
                                time.sleep(1)
                            
                            filename = f"{pg.lower().replace(' ', '_')}_{t}"
                            screenshotter.capture_screenshot(filename)
                            progress.advance(task)
                            
                            if t == "dark" and theme == "both":
                                screenshotter.toggle_theme()
                                time.sleep(1)
                    else:
                        console.print(f"[yellow]⚠ Skipping '{pg}' - navigation failed[/yellow]")
                        # Advance progress for skipped pages
                        progress.advance(task, advance=2 if theme == "both" else 1)
                
                progress.update(task, description="[green]✓ All screenshots captured")
        
        finally:
            screenshotter.stop_browser()
        
        # Stop server
        console.print("\n[cyan]4/4 Stopping server...[/cyan]")
        process.terminate()
        process.wait(timeout=5)
        console.print("[green]✓ Server stopped[/green]")
        
        console.print()
        console.print(Panel.fit(
            "[bold green]✅ Automated capture complete![/bold green]",
            border_style="green"
        ))
    
    except Exception as e:
        console.print(f"\n[red]❌ Error: {e}[/red]")
        if process:
            process.terminate()
            process.wait()
        raise click.Abort()


@cli.command()
@click.option(
    "--url",
    default="http://localhost:8501",
    help="Dashboard URL to discover pages from",
    show_default=True
)
@click.option(
    "--live",
    is_flag=True,
    help="Discover pages from live dashboard (requires dashboard to be running)"
)
def pages(url: str, live: bool):
    """List all available dashboard pages.
    
    Shows which pages can be captured. Use --live to discover from running dashboard.
    
    Examples:
    
        # Show default pages list
        screenshot-cli pages
        
        # Discover pages from running dashboard (opens collapsed menus)
        screenshot-cli pages --live
    """
    if live:
        # Discover pages from live dashboard
        console.print(Panel.fit(
            f"[bold cyan]🔍 Discovering Pages from Dashboard[/bold cyan]\n"
            f"URL: {url}",
            border_style="cyan"
        ))
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("[cyan]Checking dashboard...", total=None)
            
            # Check if dashboard is running
            import requests
            try:
                requests.get(url, timeout=5)
                progress.update(task, description="[green]✓ Dashboard is running")
                progress.stop_task(task)
            except requests.exceptions.RequestException:
                progress.stop()
                console.print(f"[red]❌ Dashboard not accessible at {url}[/red]")
                console.print("\n[yellow]Start the dashboard first:[/yellow]")
                console.print("  streamlit run src/dashboard/app.py")
                raise click.Abort()
            
            # Start browser and discover pages
            task = progress.add_task("[cyan]Starting browser...", total=None)
            
            screenshotter = DashboardScreenshotter(
                base_url=url,
                output_dir=Path("/tmp"),
                headless=True
            )
            
            try:
                screenshotter.start_browser()
                progress.update(task, description="[green]✓ Browser started")
                progress.stop_task(task)
                
                # Load dashboard
                task = progress.add_task("[cyan]Loading dashboard...", total=None)
                screenshotter.driver.get(url)
                
                if not screenshotter.wait_for_streamlit(timeout=10):
                    progress.stop()
                    console.print("[red]❌ Failed to load dashboard[/red]")
                    raise click.Abort()
                
                progress.update(task, description="[green]✓ Dashboard loaded")
                progress.stop_task(task)
                
                # Expand all collapsed expanders
                task = progress.add_task("[cyan]Expanding menus...", total=None)
                expanders = screenshotter.driver.find_elements(By.CSS_SELECTOR, "[data-testid='stExpander']")
                for expander in expanders:
                    try:
                        summary = expander.find_element(By.TAG_NAME, "summary")
                        summary.click()
                        time.sleep(0.3)
                    except:
                        pass
                
                progress.update(task, description="[green]✓ Menus expanded")
                progress.stop_task(task)
                
                # Discover all navigation buttons
                task = progress.add_task("[cyan]Discovering pages...", total=None)
                buttons = screenshotter.driver.find_elements(By.CSS_SELECTOR, "button")
                
                discovered_pages = []
                for button in buttons:
                    text = button.text.strip()
                    # Filter out common UI buttons and empty text
                    if text and text not in ["🌙", "☀️", ""] and len(text) > 1:
                        # Check if it looks like a navigation button
                        if not text.startswith("▶") and not text.startswith("▼"):
                            discovered_pages.append(text)
                
                # Remove duplicates and sort
                discovered_pages = sorted(set(discovered_pages))
                
                progress.update(task, description=f"[green]✓ Found {len(discovered_pages)} pages")
                progress.stop_task(task)
                
            finally:
                screenshotter.stop_browser()
        
        # Display discovered pages
        console.print()
        table = Table(
            title=f"Discovered Dashboard Pages ({len(discovered_pages)} found)",
            show_header=True,
            header_style="bold cyan"
        )
        table.add_column("#", style="dim", width=4)
        table.add_column("Page Name", style="cyan")
        
        for i, page in enumerate(discovered_pages, 1):
            table.add_row(str(i), page)
        
        console.print(table)
        console.print("\n[green]✅ Discovery complete![/green]")
        console.print("\n[yellow]💡 Tip:[/yellow] Use the exact page name with --page option")
        console.print("   Example: screenshot-cli capture --page \"Data Explorer\"")
    
    else:
        # Show default/known pages from API-ENDPOINTS.md
        available_pages = [
            # Main Navigation (1 page)
            ("Overview", "Main dashboard with key metrics and visualizations", "http://localhost:8501/?page=Overview"),
            # Explore & Analyze (7 pages)
            ("Data Explorer", "PyGWalker-based interactive data exploration", "http://localhost:8501/?page=Data_Explorer"),
            ("Advanced Explorer", "SQL query interface with PyGWalker visualization", "http://localhost:8501/?page=Advanced_Explorer"),
            ("VM Explorer", "Detailed VM inspection and analysis", "http://localhost:8501/?page=VM_Explorer"),
            ("VM Search", "Advanced VM search and filtering", "http://localhost:8501/?page=VM_Search"),
            ("Analytics", "Resource allocation and OS analysis", "http://localhost:8501/?page=Analytics"),
            ("Comparison", "Side-by-side datacenter/cluster comparisons", "http://localhost:8501/?page=Comparison"),
            ("Data Quality", "Field completeness and data quality analysis", "http://localhost:8501/?page=Data_Quality"),
            # Infrastructure (4 pages)
            ("Resources", "Resource metrics and allocation", "http://localhost:8501/?page=Resources"),
            ("Infrastructure", "Infrastructure topology and details", "http://localhost:8501/?page=Infrastructure"),
            ("Folder Analysis", "Folder-level resource and storage analytics", "http://localhost:8501/?page=Folder_Analysis"),
            ("Folder Labelling", "Label management and assignment", "http://localhost:8501/?page=Folder_Labelling"),
            # Migration (4 pages)
            ("Migration Targets", "Define and manage migration targets", "http://localhost:8501/?page=Migration_Targets"),
            ("Strategy Configuration", "Configure migration strategies", "http://localhost:8501/?page=Strategy_Configuration"),
            ("Migration Planning", "Plan and schedule migrations", "http://localhost:8501/?page=Migration_Planning"),
            ("Migration Scenarios", "Create and analyze migration scenarios", "http://localhost:8501/?page=Migration_Scenarios"),
            # Management (2 pages)
            ("Data Import", "Import data from Excel files", "http://localhost:8501/?page=Data_Import"),
            ("Database Backup", "Backup and restore database", "http://localhost:8501/?page=Database_Backup"),
            # Export & Help (2 pages)
            ("PDF Export", "Generate PDF reports", "http://localhost:8501/?page=PDF_Export"),
            ("Help", "Built-in help and documentation", "http://localhost:8501/?page=Help"),
        ]
        
        table = Table(
            title=f"Dashboard Pages from API-ENDPOINTS.md ({len(available_pages)} total)",
            show_header=True,
            header_style="bold cyan"
        )
        table.add_column("Page Name", style="cyan", no_wrap=True)
        table.add_column("Description", style="white")
        table.add_column("URI", style="dim")
        
        for page, description, uri in available_pages:
            table.add_row(page, description, uri)
        
        console.print(table)
        console.print("\n[yellow]💡 Tip:[/yellow] Use --live to discover all pages from running dashboard")
        console.print("   Example: screenshot-cli pages --live")
        console.print("\n[yellow]Note:[/yellow] Some pages may be in collapsed menu sections")


if __name__ == "__main__":
    cli()
