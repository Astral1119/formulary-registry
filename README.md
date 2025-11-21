# Formulary Registry

The official package registry for [Formulary](https://github.com/Astral1119/formulary), a Google Sheets package manager.

## Publishing Packages

To publish a package to this registry:

1. **Install Formulary CLI** and authenticate with GitHub:
   ```bash
   gh auth login
   ```

2. **Create and test your package** locally:
   ```bash
   formulary pack
   formulary install --local ./dist/your-package-0.1.0.gspkg
   ```

3. **Publish to registry**:
   ```bash
   formulary publish
   ```

This will automatically:
- Validate your package name and version
- Create a fork of this registry (if needed)
- Add your package to the registry
- Create a pull request for review

## Package Naming Rules

Package names must:
- Be lowercase with hyphens only (e.g., `math-utils`)
- Start with a letter
- Not use A1 or R1C1 syntax

## CI/CD

All pull requests are automatically validated by GitHub Actions:
- Package name and version validation
- Ownership verification (for package updates)
- Dependency checking
- File structure validation

## Registry Structure

```
packages/
  {package-name}/
    {version}/
      {package-name}-{version}.gspkg
```

**index.json** format:
```json
{
  "package-name": {
    "owners": ["github-username"],
    "versions": {
      "1.0.0": {
        "path": "packages/package-name/1.0.0/package-name-1.0.0.gspkg",
        "dependencies": ["other-package>=1.0.0"]
      }
    },
    "latest": "1.0.0"
  }
}
```

## License

CC0-1.0
