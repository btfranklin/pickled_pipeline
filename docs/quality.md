# Quality

The quality bar is behavior-first: tests should encode the cache contract that
users rely on, not only the implementation details that happen to pass today.

## Required Gate

```bash
pdm run check
```

This runs:

- Ruff for syntax and style errors
- mypy for source and test type checking
- pytest for behavior and regression coverage

The component commands are `pdm run lint`, `pdm run typecheck`, and
`pdm run test`.

## Cache Correctness Contracts

Tests must protect these behaviors:

- same checkpoint and same included arguments load the cached result
- changed included arguments produce distinct entries
- excluded arguments do not affect the cache key
- unpickleable included arguments fail before writing cache files
- unpickleable results do not leave partial cache files
- corrupt cache files are removed and recomputed
- truncation removes the selected checkpoint and later checkpoints only
- truncation uses exact checkpoint identity, even when names contain `__`
- a live `Cache` instance observes manifest changes made by another `Cache`
  instance or the CLI
- CLI commands exercise the same core persistence rules as the Python API

When changing `src/pickled_pipeline/cache.py`, add or update tests in the same
change if any of these contracts move.

## Structural Legibility Checks

`tests/test_repo_legibility.py` keeps the repo's navigation and validation
surface present. If this test fails, repair the missing map, docs link, or PDM
script instead of deleting the check.

## Type Checking

The package is typed and ships `py.typed`. Public functions and helpers that
affect public behavior should have annotations. Tests are also included in mypy
so fixture and helper mistakes are caught early.

## Test Style

- Prefer direct behavior assertions over testing private helper names.
- Regression tests should explain the user-visible failure they prevent.
- Do not add tests that only prove removed functionality no longer exists.
- Keep cache directories test-local; do not depend on shared state in the repo
  root.
