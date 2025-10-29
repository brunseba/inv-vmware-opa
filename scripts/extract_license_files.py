#!/usr/bin/env python3
"""Script to extract individual license files for each dependency."""

import json
import subprocess
import sys
from pathlib import Path
from importlib.metadata import metadata, PackageNotFoundError, files
import re


def get_installed_packages():
    """Get list of installed packages."""
    result = subprocess.run(
        ["uv", "pip", "list", "--format=json"],
        capture_output=True,
        text=True,
        check=True
    )
    return json.loads(result.stdout)


def sanitize_filename(name):
    """Sanitize package name for use as filename."""
    # Replace invalid characters with underscores
    return re.sub(r'[<>:"/\\|?*]', '_', name)


def get_license_file_content(package_name):
    """Try to get license file content from package."""
    try:
        package_files = files(package_name)
        if package_files is None:
            return None
        
        # Common license file names
        license_patterns = [
            'LICENSE', 'LICENSE.txt', 'LICENSE.md', 'LICENSE.rst',
            'COPYING', 'COPYING.txt', 'COPYING.md',
            'COPYRIGHT', 'COPYRIGHT.txt',
            'LICENCE', 'LICENCE.txt', 'LICENCE.md'
        ]
        
        for file in package_files:
            file_name = str(file).split('/')[-1].upper()
            if any(pattern.upper() in file_name for pattern in license_patterns):
                try:
                    content = file.read_text()
                    return content
                except Exception:
                    continue
        
        return None
    except Exception:
        return None


def get_standard_license_text(license_name):
    """Return standard license text based on license classifier."""
    license_templates = {
        "MIT": """MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.""",

        "Apache": """Apache License
Version 2.0, January 2004
http://www.apache.org/licenses/

TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION

1. Definitions.

"License" shall mean the terms and conditions for use, reproduction,
and distribution as defined by Sections 1 through 9 of this document.

[Full Apache 2.0 license text - see http://www.apache.org/licenses/LICENSE-2.0]""",

        "BSD": """BSD License

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice,
   this list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its
   contributors may be used to endorse or promote products derived from
   this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED.""",

        "GPL": """GNU GENERAL PUBLIC LICENSE
Version 3, 29 June 2007

Copyright (C) 2007 Free Software Foundation, Inc. <https://fsf.org/>

[Full GPL license text - see https://www.gnu.org/licenses/gpl-3.0.txt]""",

        "LGPL": """GNU LESSER GENERAL PUBLIC LICENSE
Version 3, 29 June 2007

Copyright (C) 2007 Free Software Foundation, Inc. <https://fsf.org/>

[Full LGPL license text - see https://www.gnu.org/licenses/lgpl-3.0.txt]""",

        "PSF": """PYTHON SOFTWARE FOUNDATION LICENSE VERSION 2

1. This LICENSE AGREEMENT is between the Python Software Foundation ("PSF"),
and the Individual or Organization ("Licensee") accessing and otherwise using
this software ("Python") in source or binary form and its associated
documentation."""
    }
    
    # Match license name to template
    license_upper = license_name.upper()
    for key, text in license_templates.items():
        if key in license_upper:
            return text
    
    return None


def extract_license_for_package(package_name, licenses_dir):
    """Extract and save license file for a package."""
    try:
        meta = metadata(package_name)
        version = meta.get("Version", "unknown")
        license_field = meta.get("License", "")
        classifiers = meta.get_all("Classifier", [])
        license_classifiers = [c for c in classifiers if c.startswith("License ::")]
        home_page = meta.get("Home-page", "")
        
        # Try to get license file from package
        license_content = get_license_file_content(package_name)
        
        # If no license file found, try to use metadata or standard template
        if not license_content:
            if license_field and len(license_field) > 50:
                license_content = license_field
            else:
                # Try to get standard license based on classifiers
                for classifier in license_classifiers:
                    if "MIT" in classifier:
                        license_content = get_standard_license_text("MIT")
                        break
                    elif "Apache" in classifier:
                        license_content = get_standard_license_text("Apache")
                        break
                    elif "BSD" in classifier:
                        license_content = get_standard_license_text("BSD")
                        break
                    elif "GPL" in classifier and "LGPL" not in classifier:
                        license_content = get_standard_license_text("GPL")
                        break
                    elif "LGPL" in classifier:
                        license_content = get_standard_license_text("LGPL")
                        break
                    elif "PSF" in classifier or "Python" in classifier:
                        license_content = get_standard_license_text("PSF")
                        break
        
        # Create the license file
        safe_name = sanitize_filename(package_name)
        license_file = licenses_dir / f"{safe_name}-{version}.txt"
        
        with open(license_file, "w") as f:
            f.write(f"Package: {package_name}\n")
            f.write(f"Version: {version}\n")
            f.write(f"License: {license_field if license_field else 'See below'}\n")
            
            if license_classifiers:
                f.write(f"License Classifiers:\n")
                for classifier in license_classifiers:
                    f.write(f"  - {classifier}\n")
            
            if home_page:
                f.write(f"Homepage: {home_page}\n")
            
            f.write("\n" + "="*80 + "\n\n")
            
            if license_content:
                f.write(license_content)
            else:
                f.write("No license text available in package metadata.\n")
                f.write(f"Please refer to the package homepage for license information:\n")
                f.write(f"{home_page if home_page else 'Homepage not available'}\n")
        
        return True
    except Exception as e:
        print(f"  Warning: Could not extract license for {package_name}: {e}")
        return False


def main():
    """Main function to extract all license files."""
    print("Extracting individual license files for all dependencies...")
    
    packages = get_installed_packages()
    licenses_dir = Path("licenses")
    licenses_dir.mkdir(exist_ok=True)
    
    success_count = 0
    failed_count = 0
    
    for pkg in packages:
        name = pkg["name"]
        if name == "inv-vmware-opa":  # Skip our own package
            continue
        
        print(f"Extracting license for {name}...")
        if extract_license_for_package(name, licenses_dir):
            success_count += 1
        else:
            failed_count += 1
    
    print(f"\n✓ License extraction complete!")
    print(f"  - Successfully extracted: {success_count}")
    print(f"  - Failed: {failed_count}")
    print(f"  - Total: {success_count + failed_count}")
    print(f"  - Location: {licenses_dir}/")


if __name__ == "__main__":
    main()
