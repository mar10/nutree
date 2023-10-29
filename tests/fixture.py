# (c) 2021-2023 Martin Wendt; see https://github.com/mar10/nutree
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
Test helpers.
"""
import os
import re
import tempfile
import time
import timeit
from random import randint
from textwrap import dedent, indent
from typing import List, Union

from nutree.tree import Node, Tree
from nutree.typed_tree import TypedNode, TypedTree


class Person:
    def __init__(self, name, *, age, guid=None) -> None:
        self.name = name
        self.age = age
        self.guid = guid

    def __repr__(self) -> str:
        return f"Person<{self.name}, {self.age}>"


class Department:
    def __init__(self, name, *, guid=None) -> None:
        self.name = name
        self.guid = guid

    def __repr__(self) -> str:
        return f"Department<{self.name}>"


def create_tree(
    *, style="simple", name="fixture", clones=False, tree=None, print=True
) -> Tree:
    if tree is not None:
        assert not tree, "must be empty"
        assert isinstance(tree, Tree)
    else:
        tree = Tree(name)

    if style == "simple":
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

    elif style == "objects":
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
        dev = tree.add(Department("Development"))
        dev.add(Person("Alice", age=23, guid="{123-456}"))
        dev.add(Person("Bob", age=32, guid="{234-456}"))
        markt = tree.add(Department("Marketing"))
        charleen = markt.add(Person("Charleen", age=43, guid="{345-456}"))
        markt.add(Person("Dave", age=54, guid="{456-456}"))
        if clones:
            dev.add(charleen)

    else:
        raise NotImplementedError(style)
    # Since the output is only displayed when a test fails, it may be handy to
    # see (unless caller modifies afterwards and then prints):
    if print:
        tree.print()

    return tree


def create_typed_tree(
    *, style="simple", name="fixture", clones=False, tree=None, print=True
) -> TypedTree:
    if tree is not None:
        assert not tree, "must be empty"
        assert isinstance(tree, TypedTree)
    else:
        tree = TypedTree(name)

    if style == "simple":
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
        func = tree.add("func1", kind="function")
        fail1 = func.add("fail1", kind="failure")
        fail1.add("cause1", kind="cause")
        fail1.add("cause2", kind="cause")
        fail1.add("eff1", kind="effect")
        fail1.add("eff2", kind="effect")
        func.add("fail2", kind="failure")
        func2 = tree.add("func2", kind="function")

        if clones:
            func2.add(fail1)

    elif style == "objects":
        """
        TypedTree<'4353629968'>
        ├── department → Department<Development>
        │   ├── manager → Person<Alice, 23>
        │   ├── member → Person<Bob, 32>
        │   ╰── member → Person<Charleen, 43>
        ╰── department → Department<Marketing>
            ├── member → Person<Charleen, 43>
            ╰── manager → Person<Dave, 54>
        """
        dev = tree.add(Department("Development"), kind="department")
        dev.add(Person("Alice", age=23, guid="{123-456}"), kind="manager")
        dev.add(Person("Bob", age=32, guid="{234-456}"), kind="member")

        markt = tree.add(Department("Marketing"), kind="department")
        charleen = markt.add(
            Person("Charleen", age=43, guid="{345-456}"), kind="member"
        )
        markt.add(Person("Dave", age=54, guid="{456-456}"), kind="manager")

        if clones:
            dev.add(charleen, kind="member")

    else:
        raise NotImplementedError(style)
    # Since the output is only displayed when a test fails, it may be handy to
    # see (unless caller modifies afterwards and then prints):
    if print:
        tree.print()

    return tree


def generate_tree(level_defs: List, root=None) -> "Tree":
    """Generate a tree.

    Example:
        generate_tree([10, 100, 100])
    """
    if root is None:
        tree = Tree()
        root = tree._root
        name = "n"
    else:
        tree = None
        name = root.name
    level_def, *rest = level_defs
    min_childs, max_childs = level_def, level_def
    for i in range(randint(min_childs, max_childs)):
        node = root.add(f"{name}.{i + 1}")
        if rest:
            generate_tree(rest, node)

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


def canonical_repr(obj: Union[str, Tree, Node], *, repr=None, style="ascii32") -> str:
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
    tree: Tree, expect_ascii, msg="", ignore_tree_name=True, repr=None, style=None
):
    if style is None:
        if "├── " in expect_ascii or "╰── " in expect_ascii:
            style = "round43"
        else:
            style = "ascii32"

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
    tree: Tree, expect_ascii, *, msg="", ignore_tree_name=True, repr=None, style=None
):
    err = _check_content(tree, expect_ascii, msg, ignore_tree_name, repr, style)
    if err:
        raise AssertionError(err) from None
    return True


def trees_equal(tree_1, tree_2, ignore_tree_name=True) -> bool:
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
    number=0,
    globals=None,
    time_unit=None,
):
    """Taken from Python `timeit.main()` module."""
    timer = timeit.default_timer
    # if o in ("-p", "--process"):
    #     timer = time.process_time
    # number = 0  # auto-determine
    repeat = timeit.default_repeat
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
        callback = None
        if verbose:

            def callback(number, time_taken):
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
        byteNumberString(number / best),
    )

    best = min(timings)
    worst = max(timings)
    if worst >= best * 4:
        import warnings

        warnings.warn_explicit(
            "The test results are likely unreliable. "
            f"The worst time ({format_time(worst)}) was more than four times "
            "slower than the best time ({format_time(best)}).",
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
        self.mode = mode
        self.encoding = encoding
        self.suffix = suffix

    def __enter__(self):
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
