# Decision 0001: Cache Persistence Contract

## Status

Accepted.

## Context

The package caches expensive pipeline steps in development workflows. Users can
also manage the same cache directory through the CLI. That makes the on-disk
store a shared boundary between decorated Python functions, future Python
processes, and command-line operations.

Three failure modes shaped this decision:

- failed pickle writes can leave zero-byte cache files
- externally truncating a cache can make a live `Cache` instance's manifest
  snapshot stale
- checkpoint names with shared textual prefixes can collide during truncation
  when file ownership is inferred with prefix matching

## Decision

Cache result writes and manifest writes use temporary files followed by
`os.replace`.

`Cache` reloads `cache_manifest.json` before recording a checkpoint so external
CLI or process changes are observed by existing decorated functions.

Cache file ownership is determined by parsing the filename from the right:

```text
<checkpoint-name>__<md5-key-hash>.pkl
```

Only files whose parsed checkpoint name exactly matches the target checkpoint
belong to that checkpoint.

## Consequences

- Failed result serialization leaves no final cache file behind.
- Corrupt cache entries can be treated as stale and recomputed.
- Truncation remains safe for checkpoint names that contain `__`.
- The package still does not provide full multi-process locking. Atomic writes
  avoid partial files, but simultaneous manifest writers can still race.
