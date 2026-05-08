import json
import os
import threading

import pytest
from click.testing import CliRunner

from pickled_pipeline import Cache
from pickled_pipeline.cli import cli


def _cache_payload_files(cache):
    return sorted(
        filename
        for filename in os.listdir(cache.cache_dir)
        if filename != "cache_manifest.json"
    )


def _manifest(cache):
    with open(cache.manifest_path, encoding="utf-8") as f:
        return json.load(f)


def test_unpickleable_result_does_not_poison_future_calls(cache):
    calls = {"count": 0}

    @cache.checkpoint(name="bad_result")
    def bad_result():
        calls["count"] += 1
        return threading.Lock()

    with pytest.raises(TypeError):
        bad_result()

    assert calls["count"] == 1
    assert _cache_payload_files(cache) == []
    assert cache.list_checkpoints() == []

    with pytest.raises(TypeError):
        bad_result()

    assert calls["count"] == 2
    assert _cache_payload_files(cache) == []
    assert cache.list_checkpoints() == []


def test_existing_corrupt_cache_entry_is_recomputed(cache):
    calls = {"count": 0}

    @cache.checkpoint(name="fragile_step")
    def fragile_step():
        calls["count"] += 1
        return f"value-{calls['count']}"

    assert fragile_step() == "value-1"
    [cache_filename] = _cache_payload_files(cache)

    cache_path = os.path.join(cache.cache_dir, cache_filename)
    with open(cache_path, "wb"):
        pass

    assert fragile_step() == "value-2"
    assert calls["count"] == 2
    assert os.path.getsize(cache_path) > 0
    assert _manifest(cache) == ["fragile_step"]


def test_live_cache_reloads_manifest_after_external_cli_truncate(tmp_path):
    cache_dir = tmp_path / "cache"
    cache = Cache(cache_dir=cache_dir)

    @cache.checkpoint(name="step1")
    def step1():
        return "one"

    @cache.checkpoint(name="step2")
    def step2():
        return "two"

    step1()
    step2()

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["truncate", "step2", "--cache-dir", str(cache_dir)],
    )

    assert result.exit_code == 0
    assert _manifest(cache) == ["step1"]

    assert step2() == "two"

    assert _manifest(cache) == ["step1", "step2"]
    assert Cache(cache_dir=cache_dir).list_checkpoints() == ["step1", "step2"]


def test_live_cache_reloads_manifest_after_external_cache_truncate(tmp_path):
    cache_dir = tmp_path / "cache"
    active_cache = Cache(cache_dir=cache_dir)

    @active_cache.checkpoint(name="step1")
    def step1():
        return "one"

    @active_cache.checkpoint(name="step2")
    def step2():
        return "two"

    step1()
    step2()

    external_cache = Cache(cache_dir=cache_dir)
    assert external_cache.truncate_cache("step2") is True

    assert step2() == "two"

    assert Cache(cache_dir=cache_dir).list_checkpoints() == ["step1", "step2"]


def test_truncate_uses_exact_checkpoint_name_when_names_share_separator(cache):
    @cache.checkpoint(name="step__earlier")
    def earlier():
        return "earlier"

    @cache.checkpoint(name="step")
    def step():
        return "step"

    assert earlier() == "earlier"
    assert step() == "step"

    assert cache.truncate_cache("step") is True

    remaining_files = _cache_payload_files(cache)
    assert cache.list_checkpoints() == ["step__earlier"]
    assert len(remaining_files) == 1
    assert remaining_files[0].startswith("step__earlier__")


def test_temp_files_are_cleaned_up_after_failed_cache_write(cache):
    @cache.checkpoint(name="bad_result")
    def bad_result():
        return threading.Lock()

    with pytest.raises(TypeError):
        bad_result()

    assert [
        filename
        for filename in os.listdir(cache.cache_dir)
        if filename.startswith(".pickled-pipeline-")
    ] == []
