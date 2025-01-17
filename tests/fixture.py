# (c) 2021-2024 Martin Wendt; see https://github.com/mar10/nutree
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
Test helpers.
"""
# ruff: noqa: T201, T203 `print` found

from __future__ import annotations

import os
import re
import tempfile
import time
import timeit
import uuid
from random import randint
from textwrap import dedent, indent
from typing import IO, Any

from nutree.common import ReprArgType
from nutree.tree import Node, Tree
from nutree.typed_tree import TypedNode, TypedTree


def is_running_on_ci() -> bool:
    return bool(os.environ.get("CI") or os.environ.get("GITHUB_ACTIONS"))


class OrgaUnit:
    def __init__(self, name: str, *, guid: str | None = None) -> None:
        self.name: str = name
        self.guid: str = uuid.uuid4().hex if guid is None else guid

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}<{self.name}>"


class Person(OrgaUnit):
    def __init__(self, name: str, *, age: int, guid: str | None = None) -> None:
        super().__init__(name, guid=guid)
        self.age: int = age

    def __repr__(self) -> str:
        return f"Person<{self.name}, {self.age}>"

    # def __eq__(self, other):
    #     return (
    #         self.__class__ == other.__class__
    #         and self.guid == other.guid
    #         and self.name == other.name
    #         and self.age == other.age
    #     )


class Department(OrgaUnit):
    def __init__(self, name: str, *, guid: str | None = None) -> None:
        super().__init__(name, guid=guid)

    # def __repr__(self) -> str:
    #     return f"Department<{self.name}>"

    # def __eq__(self, other):
    #     return (
    #         self.__class__ == other.__class__
    #         and self.guid == other.guid
    #         and self.name == other.name
    #     )


def create_tree_objects(
    *,
    name="fixture",
    clones=False,
    tree: Tree | None = None,
    print=True,
) -> Tree[OrgaUnit]:
    """
    Tree<'2009255653136'>
    ├── Node<'Department<Development>', data_id=125578508105>
    │   ├── Node<'Person<Alice, 23>', data_id={123-456}>
    │   ├── Node<'Person<Bob, 32>', data_id={234-456}>
    │   ╰── Node<'Person<Charleen, 43>', data_id={345-456}>
    ╰── Node<'Department<Marketing>', data_id=125578508063>
        ├── Node<'Person<Charleen, 43>', data_id={345-456}>
        ╰── Node<'Person<Dave, 54>', data_id={456-456}>
    """
    if tree is not None:
        assert not tree, "must be empty"
        assert isinstance(tree, Tree)
    else:
        tree = Tree[OrgaUnit](name, calc_data_id=lambda tree, data: data.guid)

    dev = tree.add(Department("Development", guid="{012-345}"))
    dev.add(Person("Alice", age=23, guid="{123-456}"))
    dev.add(Person("Bob", age=32, guid="{234-456}"))
    markt = tree.add(Department("Marketing", guid="{012-456}"))
    charleen = markt.add(Person("Charleen", age=43, guid="{345-456}"))
    markt.add(Person("Dave", age=54, guid="{456-456}"))
    if clones:
        dev.add(charleen)

    # Since the output is only displayed when a test fails, it may be handy to
    # see (unless caller modifies afterwards and then prints):
    if print:
        tree.print(repr="{node}")
    return tree


def create_tree_simple(
    *,
    name="fixture",
    clones=False,
    tree: Tree | None = None,
    print=True,
) -> Tree:
    """
    Tree<'fixture'>
    ├── 'A'
    │   ├── 'a1'
    │   │   ├── 'a11'
    │   │   ╰── 'a12'
    │   ╰── 'a2'
    ╰── 'B'
        ╰── 'b1'
            ├── 'a11'  <- CLONE
            ╰── 'b11'
    """
    if tree is not None:
        assert not tree, "must be empty"
        assert isinstance(tree, Tree)
    else:
        tree = Tree(name)

    a = tree.add("A")
    a1 = a.add("a1")
    a11 = a1.add("a11")
    a1.add("a12")
    a.add("a2")
    b = tree.add("B")
    b1 = b.add("b1")
    b1.add("b11")
    if clones:
        b1.prepend_child(a11)

    # Since the output is only displayed when a test fails, it may be handy to
    # see (unless caller modifies afterwards and then prints):
    if print:
        tree.print(repr="{node}")
    return tree


def create_typed_tree_objects(
    *,
    name="fixture",
    clones=False,
    tree: TypedTree[OrgaUnit] | None = None,
    print=True,
) -> TypedTree[OrgaUnit]:
    """
    TypedTree<'*'>
    ├── org_unit → Department<Development>
    │   ├── manager → Person<Alice, 23>
    │   ├── member → Person<Bob, 32>
    │   ╰── member → Person<Charleen, 43>
    ╰── department → Department<Marketing>
        ├── member → Person<Charleen, 43>
        ╰── manager → Person<Dave, 54>
    """
    if tree is None:
        tree = TypedTree[OrgaUnit](name)
    assert len(tree) == 0

    dev = tree.add(Department("Development", guid="{012-345}"), kind="org_unit")
    dev.add(Person("Alice", age=23, guid="{123-456}"), kind="manager")
    dev.add(Person("Bob", age=32, guid="{234-456}"), kind="member")

    markt = tree.add(Department("Marketing", guid="{345-456}"), kind="org_unit")
    charleen = markt.add(Person("Charleen", age=43, guid="{345-456}"), kind="member")
    markt.add(Person("Dave", age=54, guid="{456-456}"), kind="manager")

    if clones:
        dev.add(charleen, kind="member")

    # Since the output is only displayed when a test fails, it may be handy to
    # see (unless caller modifies afterwards and then prints):
    if print:
        tree.print(repr="{node}")
    return tree


def create_typed_tree_simple(
    *,
    name="fixture",
    clones=False,
    tree: TypedTree[Any] | None = None,
    print=True,
) -> TypedTree:
    """
    TypedTree<*>
    +- function → func1
    |  +- failure → fail1
    |  |  +- cause → cause1
    |  |  +- cause → cause2
    |  |  +- effect → eff1
    |  |  `- effect → eff2
    |  `- failure → fail2
    `- function → func2
    """
    if tree is not None:
        assert not tree, "must be empty"
        assert isinstance(tree, TypedTree)
    else:
        tree = TypedTree[Any](name)

    func = tree.add("func1", kind="function")
    fail1 = func.add("fail1", kind="failure")
    fail1.add("cause1", kind="cause")
    fail1.add("cause2", kind="cause")
    fail1.add("eff1", kind="effect")
    fail1.add("eff2", kind="effect")
    func.add("fail2", kind="failure")
    func2 = tree.add("func2", kind="function")

    if clones:
        func2.add(fail1, kind=None)
        # func2.add(fail1, kind="failure")

    # Since the output is only displayed when a test fails, it may be handy to
    # see (unless caller modifies afterwards and then prints):
    if print:
        tree.print(repr="{node}")

    return tree


def generate_tree(level_defs: list[int]) -> Tree:
    """Generate a tree.

    Example:
        generate_tree([10, 100, 100])
    """
    tree = Tree[str]()

    def _generate_tree(levels, name: str, root: Node):
        count, *rest = levels
        min_childs, max_childs = count, count
        for i in range(randint(min_childs, max_childs)):
            node = root.add(f"{name}.{i + 1}")
            if rest:
                _generate_tree(rest, node.name, node)

    _generate_tree(level_defs, "n", tree._root)
    return tree


def flatten_nodes(tree):
    """Return a comma separated list of node names."""
    res = []
    for n in tree:
        d = n.data
        if isinstance(d, str):
            res.append(d)
        else:
            res.append(d.name)
    return ",".join(res)


def canonical_repr(
    obj: str | TypedTree | Tree | Node,
    *,
    repr: ReprArgType | None = None,
    style="ascii32",
) -> str:
    if repr is None:
        if isinstance(obj, (TypedTree, TypedNode)):
            repr = TypedNode.DEFAULT_RENDER_REPR  # "{node.kind} → {node.data}"
        else:
            repr = "{node.data}"
            # repr = Node.DEFAULT_RENDER_REPR
    if isinstance(obj, (Node, Tree)):
        res = obj.format(repr=repr, style=style)
    else:
        res = obj
    res = dedent(res).strip()
    return res


tree_header_pattern = re.compile(r"Tree<.*>")
canonical_tree_header = "Tree<*>"


def _check_content(
    tree: TypedTree | Tree | Node | str,
    expect_ascii,
    msg="",
    ignore_tree_name=True,
    repr: ReprArgType | None = None,
    style: str | None = None,
):
    if style is None:
        if "├── " in expect_ascii or "╰── " in expect_ascii:
            style = "round43"
        else:
            style = "ascii32"

    if isinstance(tree, Tree):
        assert tree._self_check()

    s1 = indent(canonical_repr(tree, repr=repr, style=style), "    ")
    s2 = indent(canonical_repr(expect_ascii, repr=repr, style=style), "    ")
    if ignore_tree_name:
        s1 = tree_header_pattern.sub(canonical_tree_header, s1, count=1)
        s2 = tree_header_pattern.sub(canonical_tree_header, s2, count=1)

    if s1 != s2:
        err = f"Mismatch {msg}: Expected:\n{s2}\nbut got:\n{s1}"
        return err
    return None


def check_content(
    tree: TypedTree | Tree | Node | str,
    expect_ascii,
    *,
    msg="",
    ignore_tree_name=True,
    repr: ReprArgType | None = None,
    style=None,
) -> bool:
    err = _check_content(tree, expect_ascii, msg, ignore_tree_name, repr, style)
    if err:
        raise AssertionError(err) from None
    return True


def trees_equal(tree_1, tree_2, ignore_tree_name=True) -> bool:
    assert tree_1 is not tree_2
    if not tree_1 or not tree_2 or (len(tree_1) != len(tree_2)):
        return False
    return check_content(tree_1, tree_2, ignore_tree_name=ignore_tree_name)


def byteNumberString(
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
    repeat=timeit.default_repeat,  # type: ignore
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
        scale = 0
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
        byteNumberString(number / best),
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


class WritableTempFile:
    """
    Avoid "Permission denied error" on Windows:
      with tempfile.NamedTemporaryFile("w", suffix=".gv") as temp_file:
        # Not writable on Windows:
        # https://docs.python.org/3/library/tempfile.html#tempfile.NamedTemporaryFile

    Example:
        with WritableTempFile("w", suffix=".gv") as temp_file:
            tree.to_dotfile(temp_file.name)
    """

    def __init__(self, mode="w", *, encoding=None, suffix=None):
        self.temp_file: IO[str] = None  # type: ignore
        self.mode = mode
        self.encoding = encoding
        self.suffix = suffix

    def __enter__(self) -> IO[str]:
        self.temp_file = tempfile.NamedTemporaryFile(
            self.mode, encoding=self.encoding, suffix=self.suffix, delete=False
        )
        return self.temp_file

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.temp_file.close()
        os.unlink(self.temp_file.name)


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
        print(f"{self}")
