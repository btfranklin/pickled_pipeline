# Pickled Pipeline Docs

This directory is the source of truth for repository structure, development
workflow, and maintenance expectations.

## Map

- `architecture.md` - package shape, cache persistence contracts, CLI boundary,
  and rules for changing file or manifest behavior.
- `development.md` - local setup, PDM usage, validation commands, CI, and
  release notes for maintainers and coding agents.
- `quality.md` - required quality gates, cache correctness contracts, and test
  coverage expectations.
- `decisions/0001-cache-persistence-contract.md` - why the cache store uses
  atomic writes, exact filename parsing, and manifest reloads.
- `legibility-audit.md` - current legibility status, completed improvements,
  and remaining watchlist items.

## Working Rule

When code behavior changes, update the document that owns that behavior in the
same change. `README.md` is the public user introduction; `docs/` is the
maintainer and agent system of record.
