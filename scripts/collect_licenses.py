#!/usr/bin/env python3
"""Script to collect licenses from all dependencies."""

import json
import subprocess
import sys
from pathlib import Path
from importlib.metadata import metadata, PackageNotFoundError


def get_installed_packages():
    """Get list of installed packages."""
    result = subprocess.run(
        ["uv", "pip", "list", "--format=json"],
        capture_output=True,
        text=True,
        check=True
    )
    return json.loads(result.stdout)


def get_license_info(package_name):
    """Get license information for a package."""
    try:
        meta = metadata(package_name)
        license_text = meta.get("License", "")
        classifiers = meta.get_all("Classifier", [])
        
        # Extract license from classifiers
        license_classifiers = [c for c in classifiers if c.startswith("License ::")]
        
        return {
            "name": package_name,
            "version": meta.get("Version", "unknown"),
            "license": license_text or "See classifiers",
            "license_classifiers": license_classifiers,
            "home_page": meta.get("Home-page", ""),
            "author": meta.get("Author", ""),
        }
    except PackageNotFoundError:
        return {
            "name": package_name,
            "version": "unknown",
            "license": "Unknown",
            "license_classifiers": [],
            "home_page": "",
            "author": "",
        }


def main():
    """Main function to collect all licenses."""
    print("Collecting license information...")
    
    packages = get_installed_packages()
    licenses_dir = Path("licenses")
    licenses_dir.mkdir(exist_ok=True)
    
    # Create summary file
    summary = []
    
    for pkg in packages:
        name = pkg["name"]
        if name == "inv-vmware-opa":  # Skip our own package
            continue
            
        print(f"Processing {name}...")
        info = get_license_info(name)
        summary.append(info)
    
    # Sort by name
    summary.sort(key=lambda x: x["name"].lower())
    
    # Write summary as markdown
    summary_path = licenses_dir / "README.md"
    with open(summary_path, "w") as f:
        f.write("# Third-Party Licenses\n\n")
        f.write("This directory contains license information for all third-party dependencies used in this project.\n\n")
        f.write(f"Total dependencies: {len(summary)}\n\n")
        f.write("## Dependency List\n\n")
        f.write("| Package | Version | License |\n")
        f.write("|---------|---------|--------|\n")
        
        for info in summary:
            license_display = info["license"][:50] if info["license"] else "Unknown"
            if len(info["license"]) > 50:
                license_display += "..."
            f.write(f"| {info['name']} | {info['version']} | {license_display} |\n")
        
        f.write("\n## License Details\n\n")
        for info in summary:
            f.write(f"### {info['name']} {info['version']}\n\n")
            f.write(f"**License:** {info['license']}\n\n")
            
            if info['license_classifiers']:
                f.write("**License Classifiers:**\n")
                for classifier in info['license_classifiers']:
                    f.write(f"- {classifier}\n")
                f.write("\n")
            
            if info['home_page']:
                f.write(f"**Home Page:** {info['home_page']}\n\n")
            
            if info['author']:
                f.write(f"**Author:** {info['author']}\n\n")
            
            f.write("---\n\n")
    
    # Write JSON version
    json_path = licenses_dir / "licenses.json"
    with open(json_path, "w") as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n✓ License information collected successfully!")
    print(f"  - Summary: {summary_path}")
    print(f"  - JSON: {json_path}")
    print(f"  - Total packages: {len(summary)}")


if __name__ == "__main__":
    main()
