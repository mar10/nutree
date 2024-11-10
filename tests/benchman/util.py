import os
import threading
from typing import Optional

from typing_extensions import Literal


def is_running_on_ci() -> bool:
    return bool(os.environ.get("CI") or os.environ.get("GITHUB_ACTIONS"))


def singleton(cls):
    """
    A thread-safe decorator to ensure a class follows the Singleton
    design pattern.

    This decorator allows a class to have only one instance throughout
    the application. If the instance does not exist, it will create one;
    otherwise, it will return the existing instance. This implementation
    is thread-safe, ensuring that only one instance is created even in
    multithreaded environments.

    :param: cls (type): The class to be decorated as a Singleton.
    :return: function: A function that returns the single instance of the
             class.
    """
    instances = {}
    lock = threading.Lock()

    def get_instance(*args, **kwargs) -> object:
        """
        Return a single instance of the decorated class, creating it
        if necessary.

        This function ensures that only one instance of the class exists.
        It uses a thread-safe approach to check if an instance of the class
        already exists in the `instances` dictionary. If it does not exist,
        it creates a new instance with the provided arguments. If it does
        exist, it returns the existing instance.

        :param: *args: Variable length argument list for the class constructor.
        :param: **kwargs: Arbitrary keyword arguments for the class constructor.
        :return: object: The single instance of the class.
        """
        with lock:
            if cls not in instances:
                instances[cls] = cls(*args, **kwargs)
            return instances[cls]

    return get_instance


def sluggify(text: str) -> str:
    """
    Convert a string to a slug by replacing spaces with underscores and
    removing any non-alphanumeric characters.

    :param text: The input string to be converted to a slug.
    :return: str: The slug version of the input string.
    """
    return "".join(c if c.isalnum() else "_" for c in text).strip("_")


TimeUnitType = Literal["fsec", "psec", "nsec", "μsec", "msec", "sec"]
time_units: dict[TimeUnitType, float] = {
    "fsec": 1e-15,  # femto
    "psec": 1e-12,  # pico
    "nsec": 1e-9,  # nano
    "μsec": 1e-6,  # micro
    "msec": 1e-3,  # milli
    "sec": 1.0,
}
time_scales: list[tuple[float, TimeUnitType]] = [
    (scale, unit) for unit, scale in time_units.items()
]
time_scales.sort(reverse=True)


def get_time_unit(seconds: float) -> tuple[TimeUnitType, float]:
    for scale, unit in time_scales:
        if seconds >= scale:
            return (unit, scale)
    return ("sec", 1.0)


def format_time(
    seconds: float,
    *,
    unit: Optional[TimeUnitType] = None,
    precision: int = 3,
) -> str:
    if unit is None:
        unit, scale = get_time_unit(seconds)
    else:
        scale = time_units[unit]

    return "{secs:,.{prec}f} {unit}".format(
        prec=precision, secs=seconds / scale, unit=unit
    )


def byte_number_string(
    number: float,
    thousands_sep: bool = True,
    partition: bool = True,
    base1024: bool = False,
    append_bytes: bool = False,
    prec: int = 0,
) -> str:
    """Convert bytes into human-readable representation."""
    magsuffix = ""
    bytesuffix = ""
    assert append_bytes in (False, True, "short", "iec")
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

    if append_bytes:
        if append_bytes == "iec" and magsuffix:
            bytesuffix = "iB" if base1024 else "B"
        elif append_bytes == "short" and magsuffix:
            bytesuffix = "B"
        elif number == 1:
            bytesuffix = " Byte"
        else:
            bytesuffix = " Bytes"

    if thousands_sep and (number >= 1000 or magsuffix):
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
