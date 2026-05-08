from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_agent_entrypoint_routes_to_system_of_record():
    agents = _read("AGENTS.md")

    assert len(agents.splitlines()) <= 80
    assert "docs/index.md" in agents
    assert "docs/architecture.md" in agents
    assert "docs/development.md" in agents
    assert "docs/quality.md" in agents
    assert "pdm run check" in agents


def test_docs_index_links_core_repo_knowledge():
    docs_index = _read("docs/index.md")

    required_docs = [
        "architecture.md",
        "development.md",
        "quality.md",
        "decisions/0001-cache-persistence-contract.md",
        "legibility-audit.md",
    ]

    for doc_path in required_docs:
        assert (ROOT / "docs" / doc_path).exists(), (
            f"Missing docs/{doc_path}. Restore the documented repo knowledge "
            "artifact or update docs/index.md with the replacement."
        )
        assert doc_path in docs_index, (
            f"docs/index.md must link docs/{doc_path} so future agents can "
            "discover the source of truth."
        )


def test_quality_gate_includes_lint_typecheck_and_tests():
    pyproject = _read("pyproject.toml")
    workflow = _read(".github/workflows/python-package.yml")
    quality = _read("docs/quality.md")
    development = _read("docs/development.md")

    for required in [
        'lint = "ruff check src tests"',
        'typecheck = "mypy"',
        'test = "pytest"',
        'check = {composite = ["lint", "typecheck", "test"]}',
    ]:
        assert required in pyproject

    for command in [
        "pdm run lint",
        "pdm run typecheck",
        "pdm run test",
    ]:
        assert command in workflow
        assert command in quality
        assert command in development


def test_architecture_docs_name_cache_persistence_invariants():
    architecture = _read("docs/architecture.md").lower()
    decision = _read("docs/decisions/0001-cache-persistence-contract.md").lower()

    for required in [
        "atomic",
        "manifest",
        "from the right",
        "prefix",
        "multi-process locking",
    ]:
        assert required in architecture
        assert required in decision
