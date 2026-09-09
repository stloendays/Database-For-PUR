# Legacy recovery and validation

## Why this exists

The historical repository contained two binary payloads that were not reproducibly readable in CI:

- `releases/pur_core_integration_v005.zip` had a valid ZIP local-header prefix but a truncated central directory / later payload;
- the historical `data/legacy/viscosity_curves.csv.gz` was also truncated.

These files are retained only as historical artifacts. The canonical build no longer depends on them.

## Canonical legacy relational payload

The complete legacy SQLite source was exported into four relational CSVs and packed into three Git-tracked gzip/tar chunks:

- formulations: 85 rows;
- formulation components: 278 rows;
- measurements: 547 rows;
- protocols: 22 rows.

`scripts/rebuild_integration_release.py` validates these row counts before rebuilding the integration ZIP.

## Canonical viscosity payload

The complete legacy SQLite `viscosity_curves` table was normalized to the current schema and reconstructed as a gzip containing:

- 4,559 rows;
- 39 curve samples;
- `pnco_pct` levels 4.0 through 10.0;
- positive numeric viscosity values;
- normalized `pnco_pct` spelling instead of the legacy mixed-case `pNCO_pct` field.

`scripts/restore_viscosity_curves.py` reassembles SHA-pinned Git blobs, checks each Git blob SHA, decompresses the gzip, validates schema and row semantics, writes the canonical gzip, and performs a round-trip read check.

## SQLite merge semantics

The master builder uses UPSERT rather than `INSERT OR REPLACE`.

SQLite `REPLACE` is delete-plus-insert. Replacing an already-referenced parent row such as `sources` can violate foreign keys. The builder therefore updates conflicting rows in place and preserves row identity.

## CI gate

The validation workflow executes, in order:

1. all Batch 006-016 staging validators;
2. canonical 4,559-point viscosity reconstruction;
3. deterministic Batch 005 integration-release rebuild and ZIP CRC test;
4. cumulative `pur_master_v2.db` build;
5. core and v2 RAG index construction;
6. v2 database validation;
7. ML / Agent export generation;
8. database health reporting;
9. artifact upload.

A change is considered integration-ready only when this full pipeline is green.
