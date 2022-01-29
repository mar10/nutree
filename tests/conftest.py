# -*- coding: utf-8 -*-

# see also pytest.ini
def pytest_addoption(parser):
    parser.addoption("--benchmarks", action="store_true")
