import pytest
from pickled_pipeline import Cache


@pytest.fixture(scope="function")
def cache(tmp_path):
    return Cache(cache_dir=tmp_path / "pipeline_cache")
