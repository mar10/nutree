# (c) 2021-2024 Martin Wendt; see https://github.com/mar10/nutree
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
""" """

# NO_ruff: noqa: T201, T203 `print` found
from __future__ import annotations

import json
import math
import pprint
import time
from pathlib import Path
from typing import Any, Iterator

from typing_extensions import Self

from .context_info import BaseContextInfo
from .timings import TimingsResult, run_timings
from .util import TimeUnitType, byte_number_string, format_time, get_time_unit, sluggify

global_benchman: BenchmarkManager | None = None


def get_or_create_benchman() -> BenchmarkManager:
    global global_benchman
    if global_benchman is None:
        global_benchman = BenchmarkManager(
            project_name="nutree", project_root=Path(__file__).parent.parent.parent
        )
    return global_benchman


# @pytest.fixture
# def benchman() -> BenchmarkManager:
#     return get_or_create_benchman()


# @final
# class Automatic:
#     pass


class BenchmarkRun:
    """One single benchmark run.

    Note: it's tempting to calculate mean and standard deviation from the result
    vector and report these.  However, this is not very useful.
    In a typical case, the lowest value gives a lower bound for how fast your
    machine can run the given code snippet; higher values in the result vector
    are typically not caused by variability in Python's speed, but by other
    processes interfering with your timing accuracy.
    So the min() of the result is probably the only number you should be
    interested in.
    After that, you should look at the entire vector and apply common sense
    rather than statistics.
    """

    def __init__(
        self, benchmark_manager: BenchmarkManager, name: str, *, variant: str = ""
    ):
        assert name, name

        self.benchmark_manager: BenchmarkManager = benchmark_manager
        #: A name for this benchmark.
        self.name: str = name
        #: A variant name for this benchmark run (optional, defaults to "").
        self.variant: str = variant
        #: Start time of this benchmark run
        self.start_time: float = 0.0
        #: Total time for the whole benchmark loop
        self.elap: float = 0.0
        #: Number of iterations in one run (used for 'items per sec.')
        self.number: int = 0
        #: List of timings for each run divided by `number`, i.e. 'seconds per
        #: iteration'
        self.timings: list[float] = []

    def __str__(self) -> str:
        return self.to_str()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}<{self.name}, {self.elap}s>"

    def __lt__(self, other: Any) -> bool:
        if not isinstance(other, BenchmarkRun):
            return NotImplemented
        return self.best < other.best

    def to_str(self, *, time_unit: TimeUnitType | None = None) -> str:
        return "{}: {:,d} loop{}, best of {:,}: {} per loop ({} per sec.)".format(
            self.display_name,
            self.number,
            "" if self.number == 1 else "s",
            self.repeat,
            format_time(self.best, unit=time_unit),
            byte_number_string(self.number / self.best),
        )

    @property
    def display_name(self) -> str:
        return f"{self.name} ({self.variant})" if self.variant else self.name

    @property
    def repeat(self) -> int:
        return len(self.timings)

    @property
    def best(self) -> float:
        return min(self.timings)

    @property
    def worst(self) -> float:
        return max(self.timings)

    @property
    def mean(self) -> float:
        """Return the arithmetic average time per iteration, aka 'X̄'."""
        return sum(self.timings) / len(self.timings)

    @property
    def stdev(self) -> float:
        """Return the standard deviation of the time per iteration (aka SD, σ)."""
        n = len(self.timings)

        if n <= 1:
            return 0.0
        mean: float = self.mean
        return math.sqrt(sum((x - mean) ** 2 for x in self.timings) / n)

    @property
    def median(self) -> float:
        """Return the median time per iteration (aka med(x))."""
        timings = sorted(self.timings)
        n = len(timings)
        if n % 2 == 0:
            return (timings[n // 2 - 1] + timings[n // 2]) / 2
        return timings[n // 2]

    @property
    def outliers(self) -> list[float]:
        """Return a list of timings that are considered outliers."""
        # https://en.wikipedia.org/wiki/Outlier
        # https://en.wikipedia.org/wiki/Interquartile_range
        timings = sorted(self.timings)
        n = len(timings)
        q1 = timings[n // 4]
        q3 = timings[3 * n // 4]
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        return [x for x in timings if x < lower_bound or x > upper_bound]

    @property
    def slug(self) -> str:
        return sluggify(self.display_name)

    def __enter__(self) -> Self:
        self.start_time = time.monotonic()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.elap = time.monotonic() - self.start_time

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "variant": self.variant,
            "start_time": self.start_time,
            "elap": self.elap,
            "number": self.number,
            "timings": self.timings,
        }

    def save(self, folder: Path):
        path = folder / f"{self.slug}.json"
        with open(path, "w") as f:
            json.dump(self.to_dict(), f)

    @classmethod
    def load(cls, benchmark_manager: BenchmarkManager, path: Path) -> Self:
        with path.open("r") as f:
            data = json.load(f)
        return cls(benchmark_manager, data["name"], variant=data["variant"])


# @singleton
class BenchmarkManager:
    """Manage multiple benchmarks."""

    DEFAULT_OPTIONS = {
        "results_file": "benchman-results.json",
    }

    def __init__(
        self,
        *,
        project_name: str,
        project_root: Path | str,
        create: bool = False,
    ):
        self.context = BaseContextInfo(
            project_name=project_name, project_root=project_root
        )
        #: A list of all benchmarks, grouped by group name.
        self.benchmarks: dict[str, list[BenchmarkRun]] = {"": []}

        self.folder: Path = self.context.project.root_folder
        if not self.folder.is_dir():
            if not create:
                raise FileNotFoundError(f"Folder not found: {self.folder}")
            self.folder.mkdir(parents=True, exist_ok=True)

        # Load options from pyproject.toml `[tool.benchman]`
        self.options: dict[str, Any] = {}
        pyproject_toml = self.context.project.pyproject_toml
        if pyproject_toml:
            self.options.update(pyproject_toml.get("tool", {}).get("benchman", {}))

        pprint.pprint(self.context.to_dict())  # noqa: T203
        return

    def __repr__(self):
        return f"{self.__class__.__name__}<{self.context}, n={len(self.benchmarks)}>"

    @property
    def project_name(self) -> str:
        return self.context.project.name

    @property
    def project_version(self) -> str:
        return self.context.project.version

    def iter_benchmarks(
        self, *, group: str | None = None, name: str | None = None
    ) -> Iterator[BenchmarkRun]:
        if group is None:
            assert name is None
            for _group, benchmarks in self.benchmarks.items():
                yield from benchmarks
        elif name:
            for bench in self.benchmarks.get(group, []):
                if bench.name == name:
                    yield bench
        else:
            yield from self.benchmarks.get(group, [])

    def get_best(
        self, *, group: str | None = None, name: str | None = None
    ) -> BenchmarkRun | None:
        """Return the benchmark with the best runtime."""
        assert self.benchmarks
        best: BenchmarkRun | None = None
        for b in self.iter_benchmarks(group=group, name=name):
            if not best or b.best < best.best:
                best = b
        return best

    def get_best_time_unit(
        self, *, group: str | None = None, name: str | None = None
    ) -> TimeUnitType:
        best = self.get_best(group=group, name=name)
        if best is None:
            return "sec"
        unit, _scale = get_time_unit(best.best)
        return unit

    def _path_and_prefix(self, *, group: str) -> tuple[Path, str]:
        path = self.folder / ".benchman" / self.context.slug()
        prefix = "$".join([group])
        return path, prefix

    def add_benchmark(self, benchmark: BenchmarkRun, *, group: str = "") -> None:
        if group not in self.benchmarks:
            self.benchmarks[group] = []
        self.benchmarks[group].append(benchmark)

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

    def format_results(self) -> list[str]:
        results = []
        # Sort by group name
        for group, benchmarks in self.benchmarks.items():
            results.append(f"Group: {group or 'default'}")
            # TODO: use get_best_time_unit() to unify unit for the group?
            # Sort by best time
            for i, benchmark in enumerate(sorted(benchmarks), 1):
                ol = benchmark.outliers
                results.append(f"  {i}: {benchmark}, {len(ol)} outliers")
                # outliers = [format_time(ol) for ol in benchmark.outliers]
                # results.append(f"  {i}: {benchmark}, {outliers=}")

                # pprint.pprint(benchmark.to_dict())  # noqa: T203

        return results

    def print_results(self):
        for line in self.format_results():
            print(line)  # noqa: T201

    def run_timings(
        self,
        #: A name for this benchmark run.
        name: str,
        *,
        #: The statement to be timed.
        stmt: str,
        #: A variant name for this benchmark run.
        variant: str = "",
        #: A setup statement to execute before the main statement (not timed).
        setup: str = "pass",
        #: Verbosity level (0: quiet, 1: normal, 2: verbose)
        verbose: int = 0,
        #: Number of times to repeat the test.
        repeat: int = 5,
        #: Number of loops to run. If 0, `timeit` will determine the number
        #: automatically.
        number: int = 0,
        #: A dict containing the global variables.
        globals: dict[str, Any] | None = None,
        #: Use `time.process_time` instead of `time.monotonic` for measuring CPU time.
        process_time: bool = False,
        #: A group name for this benchmark run.
        group: str = "",
        # #: Save results to disk.
        # save_results: bool = False,
    ) -> BenchmarkRun:
        start: float = time.monotonic()
        res: TimingsResult = run_timings(
            name=name,
            stmt=stmt,
            setup=setup,
            verbose=verbose,
            repeat=repeat,
            number=number,
            globals=globals,
            process_time=process_time,
        )
        elap = time.monotonic() - start

        benchmark = BenchmarkRun(self, name, variant=variant)
        benchmark.start_time = start
        benchmark.elap = elap
        benchmark.number = res.number
        benchmark.timings = res.timings.copy()

        self.add_benchmark(benchmark, group=group)
        return benchmark
