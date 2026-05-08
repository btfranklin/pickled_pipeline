# Agent Map

This repository is a small typed Python package for caching deterministic
pipeline checkpoints on disk. Keep changes narrow and preserve the cache
persistence contracts documented in `docs/architecture.md`.

## Start Here

- Read `docs/index.md` for the repo knowledge map.
- Read `docs/architecture.md` before changing cache keys, manifests, file
  naming, truncation, or CLI behavior.
- Read `docs/development.md` before changing dependencies, scripts, CI, or
  release packaging.
- Read `docs/quality.md` before changing tests or validation gates.

## Validation

Use PDM for all environment and package work.

```bash
pdm run check
```

The check script runs Ruff, mypy, and pytest. If you need a narrower loop while
working, use `pdm run lint`, `pdm run typecheck`, or `pdm run test`.

## Dependency Rules

- Add or update Python packages with PDM.
- Use `>=` dependency constraints and resolve the latest available version when
  adding dependencies.
- Do not pin exact package versions unless functionality requires it.

## Refactoring Rules

- Preserve the public API: `from pickled_pipeline import Cache` and the
  `pickled-pipeline` CLI.
- Do not delete or weaken cache lifecycle tests when changing persistence code.
- When removing functionality, delete the dead surface directly. Do not add
  tests whose only purpose is proving removed behavior is gone.
