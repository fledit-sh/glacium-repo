# Guidelines

You are working inside Noel’s Python framework. The codebase is a loosely coupled, modular system designed to:
- aggregate large legacy directory trees (thousands of artifacts) into HDF5 files
- convert legacy formats into Python-friendly representations
- keep external libraries behind small interfaces so modules remain reusable and testable

## Core style rules
- Minimalism first: prefer the simplest structure that stays correct.
- Avoid “framework-y” noise: no unnecessary patterns, decorators, factories, registries unless they reduce complexity.
- Methods should be short and named with a single word whenever possible (e.g. `group`, `attr`, `feed`, `read`, `write`, `parse`, `select`, `index`, `convert`).
- Prefer clear object boundaries over cleverness.
- No inline comments unless absolutely necessary (the code should read itself).
- Prefer explicit code paths over “magic”.

## Interfaces & coupling
- For external libraries (e.g. `h5py`, `pandas`, `numpy`) expose a small internal interface using `abc.ABC`.
- Do NOT create interfaces for everything; only for:
  1) external dependency boundaries
  2) plugin-like modules (parsers/converters/backends)
  3) seams that benefit tests
- Use ABCs (not Protocols) when an interface is intended to be implemented by multiple backends and should fail at runtime if incomplete.
- Keep interfaces small: 2–6 methods, cohesive responsibility.
- Implementations should be swappable without changing callers.

## Module architecture (preferred minimal split)
Organize into small modules by responsibility:
- `meta.py` (FileMeta, lightweight metadata)
- `indexer.py` (filesystem indexing)
- `store/` (HDF5 or other storage backends)
- `convert/` (converter interfaces and concrete converters)
- `select.py` (selector/registry for converters/parsers)

Avoid mixing indexing + parsing + storage in a single file.

## Data flow rules
- Separate "raw archival" from "converted outputs":
  - `/raw/...` stores original bytes + basic attributes
  - `/conv/...` stores parsed/converted results + provenance link (hash or raw path)
- Converters must be able to run from:
  - filesystem input
  - HDF5 raw bytes (no filesystem required)
So converter APIs should be content-first:
- `convert(content: bytes | str, meta: FileMeta) -> ConvResult`

## Result typing
- Return minimal, Python-friendly structures:
  - dict/list (JSON-serializable) OR
  - `numpy.ndarray` OR
  - `pandas.DataFrame` (allowed when it provides real value)
- Wrap converter output in a small result type:
  - `kind` (e.g. "json", "table", "array", "text")
  - `payload`
  - `attrs` (metadata/provenance/units)

## HDF5 storage conventions
- Store files via `uint8` datasets, not Python objects.
- Always store provenance attributes on datasets:
  - `source_name`, `source_path` (if known), `source_size`
  - optional: `sha256`, `mtime_ns`
- Never leak `h5py` objects to higher layers unless explicitly asked.

## Error handling
- Fail fast, raise clear runtime errors:
  - not open -> `RuntimeError("H5 not open")`
  - missing file -> `FileNotFoundError`
  - directory given to file API -> `IsADirectoryError`
- Do not swallow exceptions.

## Testing expectations
- Provide fakes/mocks by implementing the same ABC, not by patching deep internals.
- Keep the seam small so a Fake implementation is trivial.

## Keep compatibility with existing patterns
Noel already uses:
- FileMeta + Indexer scanning by filename tokens (shot suffix)
- Selector selecting parsers by filetype/suffix
- TextParser fallback
Preserve this structure but reduce mixing and duplication (e.g. avoid double FileMeta definitions). Refer to existing style in `reader.py`. 

## Output expectations for Codex
When you generate code:
- Provide a minimal working implementation.
- Avoid extra features unless requested.
- Keep method names one word.
- Keep modules small and responsibilities clean.
- Use ABC interfaces for external boundaries and converters.
