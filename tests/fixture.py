# -*- coding: utf-8 -*-
# (c) 2021-2022 Martin Wendt and contributors; see https://github.com/mar10/nutree
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
Test helpers.
"""
import re

# import timeit
from textwrap import dedent, indent
from typing import Union

from nutree.tree import Node, Tree


class Person:
    def __init__(self, name, age) -> None:
        self.name = name
        self.age = age

    def __repr__(self) -> str:
        return f"Person<{self.name}, {self.age}>"


class Department:
    def __init__(self, name) -> None:
        self.name = name

    def __repr__(self) -> str:
        return f"Department<{self.name}>"


# class Item:
#     def __init__(self, name, price, count):
#         self.name = name
#         self.price = float(price)
#         self.count = int(count)

#     def __repr__(self):
#         return f"Item<{self.name!r}, {self.price:.2f}$>"


def create_tree(style="1", name="fixture") -> Tree:
    tree = tree = Tree(name)
    if style == "1":
        a = tree.add("A")
        a1 = a.add("a1")
        a1.add("a11")
        a1.add("a12")
        a.add("a2")
        b = tree.add("B")
        b1 = b.add("b1")
        b1.add("b11")
    else:
        raise NotImplementedError(style)
    return tree


def flatten_nodes(tree):
    """Return a comma separated list of node names."""
    res = []
    for n in tree:
        d = n.data
        if type(d) is str:
            res.append(d)
        else:
            res.append(d.name)
    return ",".join(res)


def canonical_repr(obj: Union[str, Tree, Node]) -> str:
    if isinstance(obj, (Node, Tree)):
        res = obj.format(repr="{node.data}", style="ascii32")
    else:
        res = obj
    res = dedent(res).strip()
    return res


tree_header_pattern = re.compile(r"Tree<.*>")
canonical_tree_header = "Tree<*>"


def check_content(tree: Tree, expect_ascii, *, msg="", ignore_tree_name=True):
    s1 = indent(canonical_repr(tree), "    ")
    s2 = indent(canonical_repr(expect_ascii), "    ")
    if ignore_tree_name:
        s1 = tree_header_pattern.sub(canonical_tree_header, s1, count=1)
        s2 = tree_header_pattern.sub(canonical_tree_header, s2, count=1)

    if s1 != s2:
        err = f"Mismatch {msg}: Expected:\n{s2}\nbut got:\n{s1}"
        # print(err)
        raise AssertionError(err) from None

    # assert s1 == s2
    return True


def trees_equal(tree_1, tree_2, ignore_tree_name=True) -> bool:
    return check_content(tree_1, tree_2, ignore_tree_name=ignore_tree_name)


# def run_timings(
#     name: str, stmt: str, setup="pass", *, verbose=0, number=0, globals=None
# ):
#     """Taken from Python `timeit.main()` module."""
#     timer = timeit.default_timer
#     # if o in ("-p", "--process"):
#     #     timer = time.process_time
#     # number = 0  # auto-determine
#     repeat = timeit.default_repeat
#     time_unit = None
#     units = {"nsec": 1e-9, "usec": 1e-6, "msec": 1e-3, "sec": 1.0}
#     precision = 4 if verbose else 3

#     stmt = dedent(stmt).strip()
#     if isinstance(setup, str):
#         setup = dedent(setup).strip()
#     # print(stmt)
#     # print(setup)
#     t = timeit.Timer(stmt, setup, timer, globals=globals)

#     if number == 0:
#         # determine number so that 0.2 <= total time < 2.0
#         callback = None
#         if verbose:

#             def callback(number, time_taken):
#                 msg = "{num} loop{s} -> {secs:.{prec}g} secs"
#                 plural = number != 1
#                 print(
#                     msg.format(
#                         num=number,
#                         s="s" if plural else "",
#                         secs=time_taken,
#                         prec=precision,
#                     )
#                 )

#         try:
#             number, _ = t.autorange(callback)
#         except Exception:
#             t.print_exc()
#             return 1

#         if verbose:
#             print()

#     try:
#         raw_timings = t.repeat(repeat, number)
#     except Exception:
#         t.print_exc()
#         return 1

#     def format_time(dt):
#         unit = time_unit

#         if unit is not None:
#             scale = units[unit]
#         else:
#             scales = [(scale, unit) for unit, scale in units.items()]
#             scales.sort(reverse=True)
#             for scale, unit in scales:
#                 if dt >= scale:
#                     break

#         return "%.*g %s" % (precision, dt / scale, unit)

#     timings = [dt / number for dt in raw_timings]

#     best = min(timings)

#     result = "%s: %d loop%s, best of %d: %s per loop" % (
#         name,
#         number,
#         "s" if number != 1 else "",
#         repeat,
#         format_time(best),
#     )

#     best = min(timings)
#     worst = max(timings)
#     if worst >= best * 4:
#         import warnings

#         warnings.warn_explicit(
#             "The test results are likely unreliable. "
#             "The worst time ({}) was more than four times "
#             "slower than the best time ({}).".format(
#                 format_time(worst), format_time(best)
#             ),
#             UserWarning,
#             "",
#             0,
#         )
#     return result
