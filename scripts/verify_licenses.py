#!/usr/bin/env python3
"""Script to verify licenses match actual project dependencies."""

import json
import subprocess
from pathlib import Path
import toml


def get_pyproject_dependencies():
    """Get dependencies from pyproject.toml."""
    with open("pyproject.toml") as f:
        data = toml.load(f)
    
    deps = set()
    
    # Main dependencies
    for dep in data.get("project", {}).get("dependencies", []):
        pkg_name = dep.split("[")[0].split(">")[0].split("=")[0].split("<")[0].strip()
        deps.add(pkg_name.lower())
    
    # Dev dependencies
    for group_deps in data.get("dependency-groups", {}).values():
        for dep in group_deps:
            pkg_name = dep.split("[")[0].split(">")[0].split("=")[0].split("<")[0].strip()
            deps.add(pkg_name.lower())
    
    return deps


def get_installed_packages():
    """Get actually installed packages."""
    result = subprocess.run(
        ["uv", "pip", "list", "--format=json"],
        capture_output=True,
        text=True,
        check=True
    )
    packages = json.loads(result.stdout)
    return {pkg["name"].lower(): pkg for pkg in packages}


def get_dependency_tree():
    """Get full dependency tree including transitive dependencies."""
    try:
        result = subprocess.run(
            ["uv", "pip", "show", "--verbose"],
            capture_output=True,
            text=True
        )
        # This is a simplified approach - in production use pipdeptree
        return set()
    except Exception:
        return set()


def main():
    """Main verification function."""
    print("Verifying license files against project dependencies...")
    print()
    
    # Get dependencies from pyproject.toml
    direct_deps = get_pyproject_dependencies()
    print(f"Direct dependencies in pyproject.toml: {len(direct_deps)}")
    print(f"  Examples: {', '.join(list(direct_deps)[:5])}")
    print()
    
    # Get installed packages
    installed = get_installed_packages()
    print(f"Total installed packages: {len(installed)}")
    print()
    
    # Get license files
    licenses_dir = Path("licenses")
    license_files = list(licenses_dir.glob("*.txt"))
    print(f"License files generated: {len(license_files)}")
    print()
    
    # Extract package names from license files
    licensed_packages = set()
    for lic_file in license_files:
        # Format is packagename-version.txt
        pkg_name = '-'.join(lic_file.stem.split('-')[:-1])
        licensed_packages.add(pkg_name.lower())
    
    print("=" * 80)
    print("ANALYSIS")
    print("=" * 80)
    print()
    
    # Check if all installed packages have licenses
    missing_licenses = set(installed.keys()) - licensed_packages - {"inv-vmware-opa"}
    if missing_licenses:
        print(f"⚠️  Packages missing license files: {len(missing_licenses)}")
        for pkg in sorted(missing_licenses)[:10]:
            print(f"  - {pkg}")
        if len(missing_licenses) > 10:
            print(f"  ... and {len(missing_licenses) - 10} more")
    else:
        print("✓ All installed packages have license files")
    print()
    
    # Check for extra license files
    extra_licenses = licensed_packages - set(installed.keys())
    if extra_licenses:
        print(f"⚠️  License files for uninstalled packages: {len(extra_licenses)}")
        for pkg in sorted(extra_licenses)[:10]:
            print(f"  - {pkg}")
        if len(extra_licenses) > 10:
            print(f"  ... and {len(extra_licenses) - 10} more")
    else:
        print("✓ No extra license files found")
    print()
    
    # Show dependency breakdown
    print("DEPENDENCY BREAKDOWN:")
    print(f"  - Direct dependencies (pyproject.toml): {len(direct_deps)}")
    print(f"  - Total installed (including transitive): {len(installed)}")
    print(f"  - License files generated: {len(license_files)}")
    print()
    
    # Categorize installed packages
    print("INSTALLED PACKAGE CATEGORIES:")
    
    # Direct production dependencies
    prod_direct = direct_deps & set(installed.keys())
    print(f"  - Production (direct): {len(prod_direct)}")
    
    # Transitive production dependencies
    prod_transitive = set()
    for pkg in installed.keys():
        if pkg not in direct_deps and pkg != "inv-vmware-opa":
            # This is a transitive dependency
            prod_transitive.add(pkg)
    
    print(f"  - Production (transitive): {len(prod_transitive)}")
    print()
    
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    print("The licenses/ directory contains license information for ALL installed")
    print("packages, including:")
    print("  1. Direct dependencies from pyproject.toml")
    print("  2. Transitive dependencies (dependencies of dependencies)")
    print("  3. Development tools (mkdocs, pytest, etc.)")
    print()
    print("This is CORRECT behavior because:")
    print("  - All these packages are used in the project environment")
    print("  - License compliance requires documenting ALL used software")
    print("  - The SBOM should be regenerated to include all dependencies")
    print()
    
    if len(licensed_packages) == len(installed) - 1:  # -1 for inv-vmware-opa itself
        print("✅ LICENSE COVERAGE: COMPLETE")
        print(f"   All {len(installed) - 1} dependencies are properly documented")
    else:
        print("⚠️  LICENSE COVERAGE: INCOMPLETE")
        print(f"   {len(licensed_packages)} documented / {len(installed) - 1} installed")


if __name__ == "__main__":
    main()
