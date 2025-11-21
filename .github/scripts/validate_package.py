"""Validate package submissions to the formulary registry."""
import json
import sys
import os
import re
from pathlib import Path
from packaging.version import Version, InvalidVersion


def validate_package_name(name):
    """validate package name follows naming rules."""
    if not re.match(r'^[a-z][a-z0-9\-]*$', name):
        return f"Invalid package name '{name}'. Must be lowercase, start with a letter, and contain only lowercase letters, numbers, and hyphens."
    
    if re.match(r'^[A-Z]+\d+$', name.upper()) or re.match(r'^R\d+C\d+$', name.upper()):
        return f"Package name '{name}' uses A1 or R1C1 syntax (not allowed)"
    
    if len(name) >= 255:
        return f"Package name '{name}' must be shorter than 255 characters"
    
    if name[0].isdigit():
        return f"Package name '{name}' cannot start with a number"
    
    return None


def validate_version(version_str):
    """validate version string."""
    try:
        Version(version_str)
        return None
    except InvalidVersion:
        return f"Invalid version '{version_str}'. Must be valid semantic version (e.g., '1.0.0')"


def main():
    """main validation logic."""
    # load new index
    with open('index.json') as f:
        new_index = json.load(f)
    
    # load base index
    try:
        with open('base/index.json') as f:
            base_index = json.load(f)
    except FileNotFoundError:
        base_index = {}
    
    pr_author = os.environ.get('PR_AUTHOR', '')
    errors = []
    
    # find what changed
    for package_name, package_data in new_index.items():
        # validate package name
        name_error = validate_package_name(package_name)
        if name_error:
            errors.append(name_error)
            continue
        
        # check if this is a new package or update
        is_new_package = package_name not in base_index
        
        if is_new_package:
            print(f"✓ New package: {package_name}")
            
            # validate owners field exists
            if 'owners' not in package_data:
                errors.append(f"Package '{package_name}' missing 'owners' field")
            elif pr_author and pr_author not in package_data['owners']:
                errors.append(f"PR author '{pr_author}' not in owners list for new package '{package_name}'")
            
            # validate description exists
            if 'description' not in package_data or not package_data['description']:
                errors.append(f"Package '{package_name}' missing 'description' field")
            elif len(package_data['description']) > 200:
                errors.append(f"Package '{package_name}' description too long (max 200 chars)")
        else:
            print(f"✓ Updating package: {package_name}")
            
            # check authorization for existing package
            base_owners = base_index[package_name].get('owners', [])
            if base_owners and pr_author and pr_author not in base_owners:
                errors.append(f"PR author '{pr_author}' not authorized to update package '{package_name}'. Owners: {base_owners}")
        
        # validate versions
        for version, version_data in package_data.get('versions', {}).items():
            version_error = validate_version(version)
            if version_error:
                errors.append(version_error)
                continue
            
            # check if version is new (not in base)
            is_new_version = True
            if not is_new_package and version in base_index[package_name].get('versions', {}):
                # version exists in base - check if it's been modified
                base_version_data = base_index[package_name]['versions'][version]
                # if version data is identical, it's not a new submission, just preserved
                if version_data == base_version_data:
                    is_new_version = False
                    print(f"  → Skipping {package_name}@{version} (unchanged)")
                else:
                    # version exists but data changed - that's an error
                    print(f"    → Data mismatch for {package_name}@{version}:")
                    print(f"     Base: {base_version_data}")
                    print(f"     New:  {version_data}")
                    errors.append(f"Cannot modify existing version '{version}' for package '{package_name}'")
                    continue
            
            # only validate new versions
            if not is_new_version:
                continue
            
            # validate version data structure
            if 'path' not in version_data:
                errors.append(f"Package '{package_name}' version '{version}' missing 'path' field")
            
            if 'dependencies' not in version_data:
                errors.append(f"Package '{package_name}' version '{version}' missing 'dependencies' field")
            
            # check that package file exists
            if 'path' in version_data:
                pkg_path = Path(version_data['path'])
                if not pkg_path.exists():
                    errors.append(f"Package file not found: {version_data['path']}")
                else:
                    print(f"Found package file: {version_data['path']}")
            
            # validate dependencies exist in registry
            for dep in version_data.get('dependencies', []):
                dep_name = dep.split('@')[0].split('>=')[0].split('<=')[0].split('==')[0].strip()
                if dep_name not in new_index:
                    errors.append(f"Dependency '{dep_name}' not found in registry for {package_name}@{version}")
    
    # print results
    if errors:
        print("\nValidation failed:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
    else:
        print("\nAll validation checks passed!")


if __name__ == '__main__':
    main()
