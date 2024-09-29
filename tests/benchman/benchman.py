# (c) 2021-2024 Martin Wendt; see https://github.com/mar10/nutree
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
""" """
# ruff: noqa: T201, T203 `print` found

import os
import time
import timeit
from textwrap import dedent


def is_running_on_ci() -> bool:
    return bool(os.environ.get("CI") or os.environ.get("GITHUB_ACTIONS"))


def byte_number_string(
    number, thousandsSep=True, partition=True, base1024=False, appendBytes=False, prec=0
):
    """Convert bytes into human-readable representation."""
    magsuffix = ""
    bytesuffix = ""
    assert appendBytes in (False, True, "short", "iec")
    if partition:
        magnitude = 0
        if base1024:
            while number >= 1024:
                magnitude += 1
                #                 number = number >> 10
                number /= 1024.0
        else:
            while number >= 1000:
                magnitude += 1
                number /= 1000.0
        magsuffix = ["", "K", "M", "G", "T", "P"][magnitude]
        if magsuffix:
            magsuffix = " " + magsuffix

    if appendBytes:
        if appendBytes == "iec" and magsuffix:
            bytesuffix = "iB" if base1024 else "B"
        elif appendBytes == "short" and magsuffix:
            bytesuffix = "B"
        elif number == 1:
            bytesuffix = " Byte"
        else:
            bytesuffix = " Bytes"

    if thousandsSep and (number >= 1000 or magsuffix):
        # locale.setlocale(locale.LC_ALL, "")
        # TODO: make precision configurable
        if prec > 0:
            # fs = "%.{}f".format(prec)
            # snum = locale.format_string(fs, number, thousandsSep)
            snum = f"{number:,.{prec}g}"
        else:
            # snum = locale.format("%d", number, thousandsSep)
            snum = f"{number:,g}"
        # Some countries like france use non-breaking-space (hex=a0) as group-
        # seperator, that's not plain-ascii, so we have to replace the hex-byte
        # "a0" with hex-byte "20" (space)
        # snum = hexlify(snum).replace("a0", "20").decode("hex")
    else:
        snum = str(number)

    return f"{snum}{magsuffix}{bytesuffix}"


def run_timings(
    name: str,
    stmt: str,
    setup="pass",
    *,
    verbose=0,
    repeat=5,  # timeit.default_repeat,
    number=0,
    globals=None,
    time_unit=None,
):
    """Taken from Python `timeit.main()` module."""
    timer = timeit.default_timer
    # if o in ("-p", "--process"):
    #     timer = time.process_time
    # number = 0  # auto-determine
    # repeat = timeit.default_repeat
    # time_unit = None
    units = {
        "fsec": 1e-15,  # femto
        "psec": 1e-12,  # pico
        "nsec": 1e-9,  # nano
        "μsec": 1e-6,  # micro
        "msec": 1e-3,  # milli
        "sec": 1.0,
    }
    precision = 4 if verbose else 3

    stmt = dedent(stmt).strip()
    if isinstance(setup, str):
        setup = dedent(setup).strip()
    # print(stmt)
    # print(setup)
    t = timeit.Timer(stmt, setup, timer, globals=globals)

    if number == 0:
        # determine number so that 0.2 <= total time < 2.0
        callback = None  # type: ignore
        if verbose:

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

    def format_time(dt):
        unit = time_unit
        if unit is not None:
            scale = units[unit]
        else:
            scales = [(scale, unit) for unit, scale in units.items()]
            scales.sort(reverse=True)
            for scale, unit_2 in scales:
                if dt >= scale:
                    unit = unit_2
                    break

        # return "%.*g %s" % (precision, dt / scale, unit)
        return "{secs:,.{prec}f} {unit}".format(
            prec=precision, secs=dt / scale, unit=unit
        )

    timings = [dt / number for dt in raw_timings]

    best = min(timings)

    result = "{}: {:,d} loop{}, best of {:,}: {} per loop ({} per sec.)".format(
        name,
        number,
        "s" if number != 1 else "",
        repeat,
        format_time(best),
        byte_number_string(number / best),
    )

    best = min(timings)
    worst = max(timings)
    if worst >= best * 4:
        import warnings

        warnings.warn_explicit(
            "The test results are likely unreliable. "
            f"The worst time ({format_time(worst)}) was more than four times "
            f"slower than the best time ({format_time(best)}).",
            UserWarning,
            "",
            0,
        )
    return result


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


class ClientInfo:
    def __init__(self, *, version: str | None = None):
        self.computer = "computer"
        self.version = version

    def __repr__(self):
        return f"<ClientInfo {self.computer}>"

    @classmethod
    def collect_client_info(cls, *, remarks: str | None = None):
        """
        docstring
        """
        pass


class Benchmark:
    def __init__(self, name, *, client: ClientInfo | None = None):
        self.name = name
        self.client = client

    def run(self):
        pass

    def __repr__(self):
        return f"<Benchmark {self.name}>"


class BenchmarkManager:
    def __init__(self, *, client: str = "auto"):
        self.client = client
        self.benchmarks = []
        self.results = []

    def add_benchmark(self, benchmark):
        self.benchmarks.append(benchmark)

    def save_results(self):
        pass

    def load_results(self):
        pass

    def compare_results(self, other):
        pass

    # def save_results(self):
    #     with open(self.config["results_file"], "w") as f:
    #         f.write(json.dumps(self.results))
