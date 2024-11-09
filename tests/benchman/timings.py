# (c) 2021-2024 Martin Wendt; see https://github.com/mar10/nutree
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
""" """
# ruff: noqa: T201, T203 `print` found

import logging
import time
import timeit
from dataclasses import dataclass
from textwrap import dedent
from typing import Any

from tests.benchman.util import byte_number_string, format_time

logger = logging.getLogger("benchman.timings")


class Timing:
    def __init__(self, name: str) -> None:
        self.name = name
        self.start = time.monotonic()
        self.elap = None

    def __repr__(self):
        if self.elap is None:
            elap = time.monotonic() - self.start
            return f"Timing<{self.name}> Running since {elap}..."
        return f"Timing<{self.name}> took {self.elap}."

    def __enter__(self):
        self.start = time.monotonic()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.elap = time.monotonic() - self.start
        # print(f"{self}")


@dataclass
class TimingsResult:
    name: str
    number: int
    repeat: int
    best: float
    worst: float
    timings: list[float]
    time_unit: str | None = None
    precision: int = 3

    def __str__(self):
        # return (
        #     f"{self.name}: {self.number:,d} loops, best of {self.repeat:,d}: "
        #     f"{self.best:,.3f} {self.time_unit} per loop"
        # )

        return "{}: {:,d} loop{}, best of {:,}: {} per loop ({} per sec.)".format(
            self.name,
            self.number,
            "" if self.number == 1 else "s",
            self.repeat,
            format_time(self.best, unit=self.time_unit, precision=self.precision),
            byte_number_string(self.number / self.best),
        )

    def __repr__(self):
        return (
            f"TimingsResult<{self.name}, {self.number} loops, best of {self.repeat}: "
            f"{self.best:.3f} {self.time_unit} per loop>"
        )


def run_timings(
    name: str,
    stmt: str,
    *,
    #: A setup statement to execute before the main statement.
    setup: str = "pass",
    #: Verbosity level (0: quiet, 1: normal, 2: verbose)
    verbose: int = 0,
    #: Number of times to repeat the test.
    repeat: int = 5,  # timeit.default_repeat
    #: Number of loops to run. If 0, `timeit` will determine the number automatically.
    number: int = 0,
    #: A dict containing the global variables.
    globals: dict[str, Any] | None = None,
    #: Time unit to use for formatting the result.
    time_unit: str | None = None,
    #: Use `time.process_time` instead of `time.monotonic` for measuring CPU time.
    process_time: bool = False,
) -> TimingsResult:
    """Taken from Python `timeit.main()` module."""
    timer = timeit.default_timer
    if process_time:
        timer = time.process_time
    precision = 4 if verbose > 0 else 3

    stmt = dedent(stmt).strip()
    if isinstance(setup, str):
        setup = dedent(setup).strip()
    # print(stmt)
    # print(setup)
    t = timeit.Timer(stmt, setup, timer, globals=globals)

    if number == 0:
        # determine number so that 0.2 <= total time < 2.0
        callback = None  # type: ignore
        if verbose > 0:

            def callback(number: int, time_taken: float):
                msg = "{num} loop{s} -> {secs:.{prec}g} secs"
                plural = number != 1
                print(
                    msg.format(
                        num=number,
                        s="s" if plural else "",
                        secs=time_taken,
                        prec=precision,
                    )
                )

        number, _ = t.autorange(callback)
        # try:
        #     number, _ = t.autorange(callback)
        # except Exception:
        #     t.print_exc()
        #     return 1

        if verbose:
            print()

    raw_timings = t.repeat(repeat, number)
    # try:
    #     raw_timings = t.repeat(repeat, number)
    # except Exception:
    #     t.print_exc()
    #     return 1

    timings = [dt / number for dt in raw_timings]

    best = min(timings)
    worst = max(timings)
    if worst >= best * 4:
        import warnings

        warnings.warn_explicit(
            f"The test results of {name} are likely unreliable. "
            f"The worst time ({format_time(worst)}) was more than four times "
            f"slower than the best time ({format_time(best)}).",
            UserWarning,
            "",
            0,
        )
    return TimingsResult(
        name=name,
        number=number,
        repeat=repeat,
        best=best,
        worst=worst,
        timings=timings,
        time_unit=time_unit,
        precision=precision,
    )
