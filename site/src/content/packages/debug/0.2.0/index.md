---
title: debug
version: 0.2.0
description: Debugging utilities, especially for LAMBDA objects.
latest: true
keywords: debug, lambda, udt
homepage: https://sheets.wiki
license: MIT
searchIndex: "debug Debugging utilities, especially for LAMBDA objects. ['debug', 'lambda', 'udt'] QSJOIN Query Smush Join. Uses QUERY to bypass Google Sheets' limit for standard string operations. REPR Creates a string representation of any primitive type or UDT that implements \"@repr\"."
dependencies: ["error>=0.2.0"]
---

## API Reference

### `QSJOIN`

Query Smush Join. Uses QUERY to bypass Google Sheets' limit for standard string operations.

**Arguments**:
- `delimiter`: The delimiter to separate strings with. Note that due to how QUERY works, a space will be appended to the end.
- `vector`: A vector of strings to join.

### `REPR`

Creates a string representation of any primitive type or UDT that implements "@repr".

**Arguments**:
- `val`: A primitive type or UDT that implements "@repr".



<div class="auto-doc-callout">
This package does not have a custom README. This page was automatically generated from package metadata.
</div>
