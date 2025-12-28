"""
Tests for the cache truncation functionality of the Cache class.
Ensures cached results can be invalidated from a specified checkpoint
and verifies that the cache can be correctly rebuilt afterward.
"""

import os

from pickled_pipeline.cache import _default_checkpoint_name


def test_truncate_cache(cache):
    # Define functions with arbitrary names
    @cache.checkpoint()
    def examine_input():
        return "input"

    @cache.checkpoint()
    def open_document():
        return "document"

    @cache.checkpoint()
    def process_details():
        return "details"

    @cache.checkpoint()
    def analyze_result():
        return "result"

    # Run the pipeline
    _ = examine_input()
    _ = open_document()
    _ = process_details()
    _ = analyze_result()

    # Check that manifest has the correct order
    expected_order = [
        _default_checkpoint_name(examine_input),
        _default_checkpoint_name(open_document),
        _default_checkpoint_name(process_details),
        _default_checkpoint_name(analyze_result),
    ]
    assert cache.checkpoint_order == expected_order

    # Truncate from "open_document"
    cache.truncate_cache(_default_checkpoint_name(open_document))

    # Verify that cache files for "open_document" and subsequent checkpoints are deleted
    remaining_checkpoints = cache.list_checkpoints()
    assert remaining_checkpoints == [_default_checkpoint_name(examine_input)]

    # Verify that cache files are as expected (excluding the manifest)
    cache_dir = cache.cache_dir  # Access the cache directory from the cache instance
    cache_files = [f for f in os.listdir(cache_dir) if f != "cache_manifest.json"]

    # There should be cache files only for 'examine_input'
    assert len(cache_files) == 1
    assert cache_files[0].startswith(
        f"{_default_checkpoint_name(examine_input)}__"
    )

    # Re-run the truncated steps
    _ = open_document()
    _ = process_details()
    _ = analyze_result()

    # Verify that the cache is rebuilt
    remaining_checkpoints = cache.list_checkpoints()
    assert remaining_checkpoints == expected_order
