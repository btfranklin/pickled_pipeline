# Legibility Audit

## Current Strengths

- The package has a small source layout and one obvious public abstraction:
  `Cache`.
- PDM owns dependency resolution, scripts, and distribution metadata.
- The test suite covers basic caching, truncation, CLI errors, excluded
  arguments, and pipeline-style usage.
- CI already runs across the supported Python versions.

## Remediated Gaps

- Missing entry-point map: added `AGENTS.md` as a short routing layer.
- Missing system of record: added `docs/index.md` plus architecture,
  development, quality, and decision docs.
- Hidden cache persistence contracts: documented atomic writes, manifest
  reloads, exact checkpoint identity, and known concurrency limits.
- Weak validation lane: added `pdm run typecheck` and the composite
  `pdm run check` gate.
- Missing mechanical doc guard: added a structural repo-legibility test.
- Missing regression coverage: added tests for partial writes, corrupt cache
  files, external manifest truncation, and checkpoint names containing `__`.

## Remaining Watchlist

1. Full multi-process locking is not implemented. Atomic replacement prevents
   partial files, but concurrent manifest writers can still race.
2. Cache keys still rely on pickle serialization of arguments. That is simple
   and inspectable, but it means unpickleable included arguments fail before
   the wrapped function runs.
3. The CLI currently prints messages from both `Cache` and Click wrappers.
   This is acceptable for now, but a future output cleanup should centralize
   user-facing reporting.

## Next Best Investments

1. Add a lock-file protocol if simultaneous writers become a supported use
   case.
2. Add a small cache inspection command that reports manifest entries, payload
   files, and orphaned or corrupt cache files.
3. Add a release checklist if packaging or publish failures start recurring.
