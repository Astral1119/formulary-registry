#!/usr/bin/env python3
import json
import os
import sys
import zipfile
import subprocess
import argparse
import re
from typing import Dict, Any, Optional
from packaging.version import Version, InvalidVersion

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def run_command(cmd: list[str], cwd: Optional[str] = None) -> str:
    try:
        result = subprocess.run(
            cmd, cwd=cwd, check=True, capture_output=True, text=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command {' '.join(cmd)}: {e.stderr}", file=sys.stderr)
        raise

def get_remote_index() -> Dict[str, Any]:
    """fetch index.json from origin/main."""
    try:
        run_command(["git", "fetch", "origin", "main"])
        content = run_command(["git", "show", "origin/main:index.json"])
        return json.loads(content)
    except Exception:
        print("Warning: Could not fetch remote index (might be first commit or network issue). Assuming empty.", file=sys.stderr)
        return {}

def validate_package_name(name: str) -> Optional[str]:
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

def validate_version(version_str: str) -> Optional[str]:
    """validate version string."""
    try:
        Version(version_str)
        return None
    except InvalidVersion:
        return f"Invalid version '{version_str}'. Must be valid semantic version (e.g., '1.0.0')"

def validate_package_file(file_path: str, expected_name: str, expected_version: str):
    """check if package file is valid and matches expected metadata."""
    if not os.path.exists(file_path):
        raise ValueError(f"Package file not found: {file_path}")
    
    # check size
    size = os.path.getsize(file_path)
    if size > MAX_FILE_SIZE:
        raise ValueError(f"Package file too large: {size} bytes (max {MAX_FILE_SIZE})")
    
    # check zip structure
    if not zipfile.is_zipfile(file_path):
        raise ValueError("File is not a valid zip archive")
        
    try:
        with zipfile.ZipFile(file_path, 'r') as zf:
            # check for zip bomb (compression ratio)
            total_size = sum(info.file_size for info in zf.infolist())
            if total_size > 100 * 1024 * 1024: # 100MB unpacked limit
                raise ValueError(f"Unpacked size too large: {total_size} bytes")
            
            # check for metadata file
            if '__GSPROJECT__.json' not in zf.namelist():
                raise ValueError("Missing __GSPROJECT__.json in package")
                
            # validate metadata content
            try:
                metadata = json.loads(zf.read('__GSPROJECT__.json'))
            except json.JSONDecodeError:
                raise ValueError("__GSPROJECT__.json is not valid JSON")
                
            required_fields = ["name", "version", "description", "license", "owners"]
            for field in required_fields:
                if field not in metadata:
                    raise ValueError(f"Missing required field '{field}' in __GSPROJECT__.json")
            
            # verify consistency with registry entry
            if metadata["name"] != expected_name:
                raise ValueError(f"Package name mismatch: expected '{expected_name}', got '{metadata['name']}'")
            
            if metadata["version"] != expected_version:
                raise ValueError(f"Package version mismatch: expected '{expected_version}', got '{metadata['version']}'")
                
            # check for functions.json
            if 'functions.json' not in zf.namelist():
                raise ValueError("Missing functions.json in package")
                
            bad_file = zf.testzip()
            if bad_file:
                raise ValueError(f"Corrupt file in zip: {bad_file}")
                
    except zipfile.BadZipFile:
        raise ValueError("Bad zip file")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--actor", required=True, help="GitHub username of the PR author")
    args = parser.parse_args()
    
    actor = args.actor
    print(f"Validating submission for actor: {actor}")
    
    # load local index
    try:
        with open("index.json", "r") as f:
            local_index = json.load(f)
    except FileNotFoundError:
        print("Error: index.json not found", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError:
        print("Error: index.json is invalid JSON", file=sys.stderr)
        sys.exit(1)
        
    remote_index = get_remote_index()
    
    # compare
    errors = []
    
    for pkg_name, pkg_data in local_index.items():
        # 1. validate package name
        name_error = validate_package_name(pkg_name)
        if name_error:
            errors.append(name_error)
            continue

        # 2. validate ownership & metadata
        if pkg_name in remote_index:
            # existing package
            print(f"✓ Updating package: {pkg_name}")
            remote_owners = remote_index[pkg_name].get("owners", [])
            if actor not in remote_owners:
                errors.append(f"Unauthorized: {actor} is not an owner of '{pkg_name}'. Owners: {remote_owners}")
        else:
            # new package
            print(f"✓ New package: {pkg_name}")
            local_owners = pkg_data.get("owners", [])
            if not local_owners:
                errors.append(f"Package '{pkg_name}' missing 'owners' field")
            elif actor not in local_owners:
                errors.append(f"Invalid ownership: New package '{pkg_name}' must list {actor} as an owner.")
            
            # validate description
            description = pkg_data.get("description", "")
            if not description:
                errors.append(f"Package '{pkg_name}' missing 'description' field")
            elif len(description) > 200:
                errors.append(f"Package '{pkg_name}' description too long (max 200 chars)")
        
        # 3. validate versions
        versions = pkg_data.get("versions", {})
        remote_versions = remote_index.get(pkg_name, {}).get("versions", {})
        
        for ver, ver_data in versions.items():
            # validate version string
            ver_error = validate_version(ver)
            if ver_error:
                errors.append(ver_error)
                continue

            # check immutability
            if ver in remote_versions:
                # version exists in base - check if it's been modified
                base_version_data = remote_versions[ver]
                if ver_data == base_version_data:
                    print(f"  → Skipping {pkg_name}@{ver} (unchanged)")
                    continue
                else:
                    print(f"    → Data mismatch for {pkg_name}@{ver}:")
                    print(f"     Base: {base_version_data}")
                    print(f"     New:  {ver_data}")
                    errors.append(f"Cannot modify existing version '{ver}' for package '{pkg_name}'")
                    continue
            
            # this is a new version being published
            
            # validate structure
            if 'path' not in ver_data:
                errors.append(f"Package '{pkg_name}' version '{ver}' missing 'path' field")
                continue
            if 'dependencies' not in ver_data:
                errors.append(f"Package '{pkg_name}' version '{ver}' missing 'dependencies' field")
                continue

            rel_path = ver_data.get("path")
            
            # check file
            try:
                validate_package_file(rel_path, pkg_name, ver)
                print(f"✓ Validated {pkg_name} v{ver}")
            except ValueError as e:
                errors.append(f"Invalid package file for {pkg_name} v{ver}: {e}")
            
            # validate dependencies exist in registry
            for dep in ver_data.get('dependencies', []):
                # parse dependency name (simple parsing for now, assuming 'name' or 'name>=ver')
                # split by common operators
                dep_name = re.split(r'[<>=!]', dep)[0].strip()
                if dep_name not in local_index:
                     errors.append(f"Dependency '{dep_name}' not found in registry for {pkg_name}@{ver}")

    if errors:
        print("\nValidation FAILED:")
        for e in errors:
            print(f"- {e}")
        sys.exit(1)
    
    print("\nValidation PASSED")

if __name__ == "__main__":
    main()
