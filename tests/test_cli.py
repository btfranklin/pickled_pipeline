from click.testing import CliRunner

from pickled_pipeline import Cache
from pickled_pipeline.cli import cli


def test_cli_truncate_missing_manifest(tmp_path):
    runner = CliRunner()
    cache_dir = tmp_path / "cache"

    result = runner.invoke(
        cli, ["truncate", "step1", "--cache-dir", str(cache_dir)]
    )

    assert result.exit_code == 0
    assert "Cache truncated from checkpoint" not in result.output
    assert "No manifest file found." in result.output


def test_cli_truncate_unknown_checkpoint(tmp_path):
    cache_dir = tmp_path / "cache"
    cache = Cache(cache_dir=str(cache_dir))

    @cache.checkpoint()
    def step():
        return "ok"

    step()

    runner = CliRunner()
    result = runner.invoke(
        cli, ["truncate", "missing_step", "--cache-dir", str(cache_dir)]
    )

    assert result.exit_code == 0
    assert "Cache truncated from checkpoint" not in result.output
    assert "Checkpoint 'missing_step' not found in manifest." in result.output
