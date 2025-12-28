"""
Tests for the 'exclude_args' feature of the pickled_pipeline.Cache class.
These tests ensure that arguments can be excluded from the cache key,
allowing for unpickleable objects or sensitive data to be passed without
affecting caching behavior.
"""

import os
import threading
import pytest


def test_cache_with_excluded_unpickleable_argument(cache):
    # Define an unpickleable object
    unpickleable_arg = threading.Lock()

    @cache.checkpoint(exclude_args=["unpickleable_arg"])
    def test_function(x, unpickleable_arg):
        return x * 2

    # Call the function
    result = test_function(5, unpickleable_arg)
    assert result == 10

    # Verify that the cache file was created
    cache_files = [
        filename
        for filename in os.listdir(cache.cache_dir)
        if filename != "cache_manifest.json"
    ]
    assert len(cache_files) == 1

    # Call the function again with the same 'x' but a different
    # 'unpickleable_arg'.
    new_unpickleable_arg = threading.Lock()
    result_cached = test_function(5, new_unpickleable_arg)
    assert result_cached == 10

    # Ensure that the cached result was used (no new cache file created).
    cache_files_after = [
        filename
        for filename in os.listdir(cache.cache_dir)
        if filename != "cache_manifest.json"
    ]
    assert len(cache_files_after) == 1


def test_cache_excluded_argument_affects_result(cache):
    @cache.checkpoint(exclude_args=["excluded_arg"])
    def test_function(x, excluded_arg):
        return x * excluded_arg

    # Call the function with different 'excluded_arg' values
    result1 = test_function(5, 2)
    result2 = test_function(5, 3)

    # Since 'excluded_arg' is excluded from the cache key, both calls should
    # retrieve the same cached result.
    # This demonstrates that excluding arguments affecting the output can lead
    # to incorrect caching.
    # Both results are from the first computation.
    assert result1 == result2 == 10


def test_cache_with_multiple_excluded_arguments(cache):
    unpickleable_arg1 = threading.Lock()
    unpickleable_arg2 = threading.Lock()

    @cache.checkpoint(exclude_args=["unpickleable_arg1", "unpickleable_arg2"])
    def test_function(x, unpickleable_arg1, unpickleable_arg2):
        return x * 2

    # Call the function
    result = test_function(5, unpickleable_arg1, unpickleable_arg2)
    assert result == 10

    # Verify that the cache file was created
    cache_files = [
        filename
        for filename in os.listdir(cache.cache_dir)
        if filename != "cache_manifest.json"
    ]
    assert len(cache_files) == 1


def test_cache_included_arguments_affect_cache(cache):
    @cache.checkpoint(exclude_args=["excluded_arg"])
    def test_function(x, excluded_arg):
        return x + excluded_arg

    # Call with x=5
    result1 = test_function(5, 10)
    assert result1 == 15

    # Call with x=6
    result2 = test_function(6, 10)
    assert result2 == 16

    # Verify that two cache files were created since 'x' is included in the
    # cache key.
    cache_files = [
        filename
        for filename in os.listdir(cache.cache_dir)
        if filename != "cache_manifest.json"
    ]
    assert len(cache_files) == 2


def test_cache_excluding_nonexistent_argument(cache):
    @cache.checkpoint(exclude_args=["nonexistent_arg"])
    def test_function(x):
        return x + 1

    # Call the function
    result = test_function(5)
    assert result == 6

    # Verify that cache works even when excluding a non-existent argument.
    cache_files = [
        filename
        for filename in os.listdir(cache.cache_dir)
        if filename != "cache_manifest.json"
    ]
    assert len(cache_files) == 1


def test_cache_with_excluded_kwargs(cache):
    @cache.checkpoint(exclude_args=["excluded_kwarg"])
    def test_function(x, **kwargs):
        return x + kwargs.get("excluded_kwarg", 0)

    # Call the function with different 'excluded_kwarg' values
    result1 = test_function(5, excluded_kwarg=10)
    result2 = test_function(5, excluded_kwarg=20)

    # Since 'excluded_kwarg' is excluded, both results should be cached as the
    # same.
    assert result1 == result2 == 15


def test_cache_with_args_and_excluded_args(cache):
    @cache.checkpoint(exclude_args=["excluded_arg"])
    def test_function(*args, **kwargs):
        return sum(args) + sum(kwargs.values())

    # Call the function
    result = test_function(
        1,
        2,
        excluded_arg=3,
        included_arg=4,
    )
    assert result == 10  # 1 + 2 + 3 + 4

    # Verify that 'excluded_arg' does not affect the cache key
    cache_files = [
        filename
        for filename in os.listdir(cache.cache_dir)
        if filename != "cache_manifest.json"
    ]
    assert len(cache_files) == 1

    # Call again with a different 'excluded_arg'
    result_cached = test_function(
        1,
        2,
        excluded_arg=5,
        included_arg=4,
    )
    assert result_cached == 10  # Cached result from the first call

    # Demonstrate that excluding arguments affecting the output can lead to
    # incorrect caching.
    assert result_cached != 12  # The result is not updated due to caching


def test_cache_with_default_arguments(cache):
    @cache.checkpoint(exclude_args=["excluded_arg"])
    def test_function(x, excluded_arg="default"):
        return f"{x}_{excluded_arg}"

    # Call the function without specifying 'excluded_arg'
    result1 = test_function(5)
    assert result1 == "5_default"

    # Call the function with a different 'excluded_arg'
    result2 = test_function(5, excluded_arg="changed")
    # Cached result from the first call.
    assert result2 == "5_default"

    # Demonstrate that excluding arguments affecting the output can lead to
    # incorrect caching.
    # The result is not updated due to caching.
    assert result2 != "5_changed"


def test_cache_with_unpickleable_return_and_excluded_args(cache):
    @cache.checkpoint(exclude_args=["x"])
    def test_function(x):
        return threading.Lock()  # Unpickleable return value

    # Even though 'x' is excluded, the return value is unpickleable
    with pytest.raises(Exception):
        test_function(5)
