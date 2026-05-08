# Architecture

Pickled Pipeline is intentionally small. The durable architecture is one public
`Cache` abstraction, one CLI adapter, and one on-disk cache store.

## Package Shape

```text
src/pickled_pipeline/
├── __init__.py   # public import surface: Cache
├── cache.py      # decorator API, key building, manifest, and file store
├── cli.py        # Click commands for managing an existing cache directory
└── py.typed      # package exports inline types
```

Tests live in `tests/`. CI and local validation both use the PDM scripts in
`pyproject.toml`.

## Public API

The stable public import is:

```python
from pickled_pipeline import Cache
```

The stable CLI entry point is:

```bash
pickled-pipeline
```

Internal helpers in `cache.py` can change, but changes must preserve the public
decorator behavior and CLI-visible cache semantics.

## Cache Store Contract

A cache directory contains:

- `cache_manifest.json`, a JSON list of checkpoint names in first-seen order.
- one `.pkl` file per cached result and argument fingerprint.

Cache files are named:

```text
<checkpoint-name>__<md5-key-hash>.pkl
```

The checkpoint portion is parsed by splitting from the right on `__`. Do not use
plain prefix matching for checkpoint identity. Custom checkpoint names may also
contain `__`, and truncation must not delete another checkpoint's files because
of a shared textual prefix.

## Key Contract

The cache key is built from:

- the checkpoint name
- bound positional, keyword, varargs, keyword-only, and default arguments
- all non-excluded keyword arguments sorted into a stable order

Arguments listed in `exclude_args` are removed before key serialization. This
is useful for unpickleable clients or values that do not affect the result, but
it is unsafe for values that influence output.

## Persistence Contract

Cache writes are atomic:

1. compute the function result
2. pickle the result into a temporary file inside the cache directory
3. replace the final cache path only after pickle serialization succeeds

If serialization fails, the final cache path must not be created. A failed write
must not poison future calls with a zero-byte or partial `.pkl` file.

Manifest writes are also atomic. A failed manifest update must not leave a
partial JSON file behind.

Existing corrupt cache entries are treated as stale for the supported corrupt
states (`EOFError` and `pickle.UnpicklingError`): the file is removed and the
function is recomputed.

## Manifest Contract

`Cache` keeps `checkpoint_order` for convenience, but the manifest file is the
shared source of truth. Before recording a checkpoint, `Cache` reloads the
manifest from disk. This matters because users can truncate or clear a cache
from another process or from the CLI while an existing Python process still has
decorated functions in memory.

The project does not currently provide multi-process locking for simultaneous
writers. Atomic file replacement prevents partial files, but last-writer-wins
manifest races remain a known future hardening area.

## CLI Boundary

`src/pickled_pipeline/cli.py` is an adapter over `Cache`; it should not
reimplement cache file selection, manifest logic, or key behavior. Add behavior
to `Cache` first, then expose it through the CLI if needed.

## Forbidden Shortcuts

- Do not decide cache hits from partial files.
- Do not write cache or manifest data directly to the final path.
- Do not infer checkpoint ownership with `filename.startswith(...)`.
- Do not make the CLI and the Python API maintain separate persistence rules.
