# see also pytest.ini
import pytest
from benchman import BenchmarkManager, get_or_create_benchman


def pytest_addoption(parser):
    parser.addoption("--benchmarks", action="store_true")


@pytest.fixture(scope="session")
def benchman() -> BenchmarkManager:
    return get_or_create_benchman(path=__file__)
