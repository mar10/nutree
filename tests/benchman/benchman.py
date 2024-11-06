# (c) 2021-2024 Martin Wendt; see https://github.com/mar10/nutree
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
""" """

# NO_ruff: noqa: T201, T203 `print` found
from __future__ import annotations

import time
from pathlib import Path
from typing import Self, final

from .context_info import BaseContextInfo
from .timings import TimingsResult, run_timings
from .util import singleton


@final
class Automatic:
    pass


class Benchmark:
    """One benchmark run."""

    def __init__(
        self, benchmark_manager: BenchmarkManager, name: str, *, variant: str = ""
    ):
        self.benchmark_manager = benchmark_manager
        self.name = name
        self.variant = variant
        self.start_time: float = 0.0
        self.elap: float = 0.0

    def __str__(self) -> str:
        return f"Benchmark {self.name} took {self.elap} seconds."

    def __repr__(self) -> str:
        return f"Benchmark<{self.name}, {self.elap}s>"

    def __enter__(self) -> Self:
        self.start_time = time.monotonic()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.elap = time.monotonic() - self.start_time

    @classmethod
    def from_timings_result(
        cls, benchmark_manager: BenchmarkManager, res: TimingsResult
    ) -> Self:
        benchmark = cls(benchmark_manager, res.name)
        benchmark.start_time = res.start_time
        return benchmark

    def run(self):
        pass


@singleton
class BenchmarkManager:
    """Manage multiple benchmarks."""

    def __init__(
        self,
        *,
        folder: Path | str | type[Automatic] = Automatic,
        create: bool = False,
        # client: BaseContextInfo | type[Automatic] = Automatic,
    ):
        self.context: BaseContextInfo = BaseContextInfo()
        self.benchmarks: list[Benchmark] = []

        if folder is Automatic:
            folder = Path.cwd()
        elif isinstance(folder, str):
            folder = Path(folder)
        assert isinstance(folder, Path)
        self.folder: Path = folder

        if not self.folder.is_dir():
            if create:
                self.folder.mkdir(parents=True, exist_ok=True)
            else:
                raise FileNotFoundError(f"Folder not found: {folder}")
        return

    def __repr__(self):
        return f"{self.__class__.__name__}<{self.context}, n={len(self.benchmarks)}>"

    # @classmethod
    def run_timings(
        self,
        name: str,
        stmt: str,
        *,
        setup: str = "pass",
        verbose: int = 0,
        repeat: int = 5,  # timeit.default_repeat,
        number: int = 0,
        globals=None,
        time_unit=None,
        variant: str = "",
        save_results: bool = False,
    ) -> Benchmark:
        res: TimingsResult = run_timings(
            name=name,
            stmt=stmt,
            setup=setup,
            verbose=verbose,
            repeat=repeat,
            number=number,
            globals=globals,
            time_unit=time_unit,
        )
        # print(res)
        benchmark = Benchmark(self, name)
        benchmark.set_timings_result(res)
        self.benchmarks.append(benchmark)
        return benchmark

    def add_benchmark(self, benchmark: Benchmark) -> None:
        self.benchmarks.append(benchmark)

    def save_results(
        self,
    ):
        pass

    def load_results(self):
        pass

    def compare_results(self, other):
        pass

    # def save_results(self):
    #     with open(self.config["results_file"], "w") as f:
    #         f.write(json.dumps(self.results))

    def print_results(self):
        pass
