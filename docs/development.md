# Development

Use PDM for dependency management, virtual environments, scripts, and package
builds.

## Setup

```bash
pdm install --group dev
```

## Validation

Run the full local gate before handing off changes:

```bash
pdm run check
```

The component scripts are:

```bash
pdm run lint
pdm run typecheck
pdm run test
```

`pdm run check` runs those in order: Ruff, mypy, then pytest.

## Dependency Changes

When adding Python packages:

1. use `pdm add`
2. keep dependency constraints in the `>=` style
3. resolve the latest available stable version at the time of the change
4. commit both `pyproject.toml` and `pdm.lock`

Examples:

```bash
pdm add "package-name"
pdm add -dG dev --save-minimum "dev-package-name"
```

Do not edit dependency metadata by hand unless PDM cannot represent the needed
change.

## CI

`.github/workflows/python-package.yml` runs on pushes and pull requests to
`main`. It validates Python 3.10 through 3.14 and runs:

1. `pdm run lint --statistics`
2. `pdm run typecheck`
3. `pdm run test`

`.github/workflows/python-publish.yml` builds and publishes the package when a
GitHub release is published. Versioning is SCM-driven through `pdm-backend`.

## Release Surface

The package excludes tests from distribution and exports inline types through
`src/pickled_pipeline/py.typed`. Keep the type-checking lane green whenever
public signatures change.

## Useful Local Commands

```bash
pdm run pickled-pipeline list --cache-dir pipeline_cache
pdm run pickled-pipeline truncate <checkpoint-name> --cache-dir pipeline_cache
pdm run pickled-pipeline clear --cache-dir pipeline_cache
```
