# see also pytest.ini
import pytest
from benchman import BenchmarkManager


def pytest_addoption(parser):
    parser.addoption("--benchmarks", action="store_true")


@pytest.fixture(scope="session")
def benchman() -> BenchmarkManager:
    return BenchmarkManager.singleton()
