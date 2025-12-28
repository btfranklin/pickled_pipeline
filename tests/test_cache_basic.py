"""
Tests for the basic functionality of the pickled_pipeline.Cache class.
These tests ensure that caching, cache retrieval, and handling of different
arguments work as expected.
"""

import os
import pytest


def test_cache_checkpoint(cache):
    # Define a sample function to test caching
    @cache.checkpoint()
    def test_function(x):
        return x * x

    # Call the function for the first time
    result1 = test_function(3)
    assert result1 == 9

    # Check that the cache file was created (excluding the manifest)
    cache_files = [
        filename
        for filename in os.listdir(cache.cache_dir)
        if filename != "cache_manifest.json"
    ]
    assert len(cache_files) == 1

    # Call the function again with the same argument
    result2 = test_function(3)
    assert result2 == 9

    # Ensure the cache file count hasn't increased
    cache_files_after = [
        f for f in os.listdir(cache.cache_dir) if f != "cache_manifest.json"
    ]
    assert len(cache_files_after) == 1


def test_custom_checkpoint_name(cache):
    @cache.checkpoint(name="custom_checkpoint_name")
    def test_function(x):
        return x * 2

    # Call the function for the first time
    result1 = test_function(5)
    assert result1 == 10

    # Verify that the checkpoint name is 'custom_checkpoint_name'
    assert cache.checkpoint_order == ["custom_checkpoint_name"]

    # Check that the cache file was created with the custom name
    cache_files = [
        filename
        for filename in os.listdir(cache.cache_dir)
        if filename != "cache_manifest.json"
    ]
    assert len(cache_files) == 1
    assert cache_files[0].startswith("custom_checkpoint_name__")

    # Call the function again with the same argument to test cache retrieval
    result2 = test_function(5)
    assert result2 == 10

    # Ensure no new cache files were created
    cache_files_after = [
        f for f in os.listdir(cache.cache_dir) if f != "cache_manifest.json"
    ]
    assert len(cache_files_after) == 1

    # Call the function with a different argument
    result3 = test_function(6)
    assert result3 == 12

    # Verify that a new cache file was created for the new input
    cache_files_final = [
        f for f in os.listdir(cache.cache_dir) if f != "cache_manifest.json"
    ]
    assert len(cache_files_final) == 2


def test_cache_different_arguments(cache):
    @cache.checkpoint()
    def test_function(x):
        return x + 1

    # Call the function with different arguments
    result1 = test_function(1)
    result2 = test_function(2)
    result3 = test_function(1)  # Should load from cache

    assert result1 == 2
    assert result2 == 3
    assert result3 == 2

    # Check that two cache files were created (excluding the manifest)
    cache_files = [
        filename
        for filename in os.listdir(cache.cache_dir)
        if filename != "cache_manifest.json"
    ]
    assert len(cache_files) == 2


def test_cache_with_varargs(cache):
    @cache.checkpoint()
    def add(*args):
        return sum(args)

    result1 = add(1, 2)
    result2 = add(2, 3)

    assert result1 == 3
    assert result2 == 5

    cache_files = [
        filename
        for filename in os.listdir(cache.cache_dir)
        if filename != "cache_manifest.json"
    ]
    assert len(cache_files) == 2


def test_cache_kwargs_ordering_does_not_create_new_entry(cache):
    @cache.checkpoint()
    def add(**kwargs):
        return kwargs["a"] + kwargs["b"]

    result1 = add(a=1, b=2)
    assert result1 == 3

    cache_files = [
        filename
        for filename in os.listdir(cache.cache_dir)
        if filename != "cache_manifest.json"
    ]
    assert len(cache_files) == 1

    result2 = add(b=2, a=1)
    assert result2 == 3

    cache_files_after = [
        f for f in os.listdir(cache.cache_dir) if f != "cache_manifest.json"
    ]
    assert len(cache_files_after) == 1


def test_cache_with_complex_arguments(cache):
    @cache.checkpoint()
    def complex_function(a, b):
        return a, b  # Return a tuple of the arguments

    dict_arg = {"key1": "value1", "key2": "value2"}
    list_arg = [1, 2, 3]

    result = complex_function(dict_arg, list_arg)
    assert result == (dict_arg, list_arg)

    # Call again with the same arguments to test cache retrieval
    result_cached = complex_function(dict_arg, list_arg)
    assert result_cached == result


def test_cache_pickleable_objects(cache):
    @cache.checkpoint()
    def non_pickleable_function():
        return lambda x: x * x  # Functions are not pickleable

    with pytest.raises(Exception):
        non_pickleable_function()


def test_cache_with_non_serializable_included_arg(cache):
    import threading

    unpickleable_arg = threading.Lock()

    @cache.checkpoint()
    def test_function(unpickleable_arg):
        return "result"

    # This should raise an exception because the argument cannot be pickled
    with pytest.raises(Exception):
        test_function(unpickleable_arg)


def test_cache_error_with_unpickleable_return(cache):
    @cache.checkpoint()
    def test_function():
        import threading

        return threading.Lock()  # Unpickleable return value

    with pytest.raises(Exception):
        test_function()


def test_clear_cache(cache):
    @cache.checkpoint()
    def step1():
        return "result1"

    @cache.checkpoint()
    def step2():
        return "result2"

    # Run steps
    _ = step1()
    _ = step2()

    # Ensure cache files are created (excluding manifest)
    cache_files = [
        filename
        for filename in os.listdir(cache.cache_dir)
        if filename != "cache_manifest.json"
    ]
    assert len(cache_files) == 2

    # Clear the cache
    cache.clear_cache()

    # Verify that cache files are deleted (excluding manifest)
    cache_files_after_clear = [
        f for f in os.listdir(cache.cache_dir) if f != "cache_manifest.json"
    ]
    assert len(cache_files_after_clear) == 0

    # Verify that manifest is empty
    assert cache.checkpoint_order == []
