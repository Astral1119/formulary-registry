---
title: flookup
version: 0.1.0
description: A library of common string comparison algorithms.
latest: true
keywords: string, levenshtein, jaro, jaro-winkler, flookup
homepage: https://sheets.wiki
license: MIT
searchIndex: "flookup A library of common string comparison algorithms. ['string', 'levenshtein', 'jaro', 'jaro-winkler', 'flookup'] FLOOKUP Fuzzy lookup using one of the non-weighted string comparison algorithms. FLOOKUP_THRESHOLD Fuzzy lookup using one of the non-weighted string comparison algorithms. Uses a threshold to return #N/A if there are no good matches. JAROSIM Finds the Jaro Similarity between two strings. JWSIM Finds the Jaro-Winkler Similarity between two strings. LEVDIST Finds the Levenshtein Distance between two strings. LEVDIST_WEIGHTED Finds the Levenshtein Distance between two strings. Allows weighting for deletion, insertion, and substitution. OSA Finds the Optimal String Alignment between two strings. OSA_WEIGHTED Finds the Optimal String Alignment between two strings. Allows weighting for deletion, insertion, and substitution."
dependencies: ["error>=0.2.0"]
---

## API Reference

### `FLOOKUP`

Fuzzy lookup using one of the non-weighted string comparison algorithms.

**Arguments**:
- `algorithm`: The non-weighted string comparison algorithm to use.
- `is_ascending`: Whether or not to sort by weights ascending. Similarity metrics should generally be descending and distance metrics should be ascending.
- `search_key`: The value to search for.
- `lookup_range`: The range to consider for the search. This range must be a singular row or column.
- `result_range`: The range to consider for the result. This range's row or column size should be the same as the lookup_range's, depending on how the lookup is done.

### `FLOOKUP_THRESHOLD`

Fuzzy lookup using one of the non-weighted string comparison algorithms. Uses a threshold to return #N/A if there are no good matches.

**Arguments**:
- `algorithm`: The non-weighted string comparison algorithm to use.
- `is_ascending`: Whether or not to sort by weights ascending. Similarity metrics should generally be descending and distance metrics should be ascending.
- `threshold`: The cutoff for candidate matches.
- `search_key`: The value to search for.
- `lookup_range`: The range to consider for the search. This range must be a singular row or column.
- `result_range`: The range to consider for the result. This range's row or column size should be the same as the lookup_range's, depending on how the lookup is done.

### `JAROSIM`

Finds the Jaro Similarity between two strings.

**Arguments**:
- `source`: Source string.
- `target`: Target string.

### `JWSIM`

Finds the Jaro-Winkler Similarity between two strings.

**Arguments**:
- `source`: Source string.
- `target`: Target string.

### `LEVDIST`

Finds the Levenshtein Distance between two strings.

**Arguments**:
- `source`: Source string.
- `target`: Target string.

### `LEVDIST_WEIGHTED`

Finds the Levenshtein Distance between two strings. Allows weighting for deletion, insertion, and substitution.

**Arguments**:
- `source`: Source string.
- `target`: Target string.
- `delete_cost`: The cost for deletion.
- `insert_cost`: The cost for insertion.
- `substitute_cost`: The cost for substitution.

### `OSA`

Finds the Optimal String Alignment between two strings.

**Arguments**:
- `source`: Source string.
- `target`: Target string.

### `OSA_WEIGHTED`

Finds the Optimal String Alignment between two strings. Allows weighting for deletion, insertion, and substitution.

**Arguments**:
- `source`: Source string.
- `target`: Target string.
- `delete_cost`: The cost for deletion.
- `insert_cost`: The cost for insertion.
- `substitute_cost`: The cost for substitution.
- `transpose_cost`: The cost for transposition.



<div class="auto-doc-callout">
This package does not have a custom README. This page was automatically generated from package metadata.
</div>
