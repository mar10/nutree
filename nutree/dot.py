# -*- coding: utf-8 -*-
# (c) 2021-2022 Martin Wendt; see https://github.com/mar10/nutree
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
Functions and declarations used by the :mod:`nutree.tree` and :mod:`nutree.node`
modules.
"""
import os
from pathlib import PurePath
from typing import IO, TYPE_CHECKING, Generator, Union

if TYPE_CHECKING:  # Imported by type checkers, but prevent circular includes
    from .node import Node
    from .tree import Tree
try:
    import pydot
except ImportError:
    pydot = None


def node_to_dot(
    node: "Node",
    *,
    add_self=False,
    single_inst=True,
    node_mapper=None,
    edge_mapper=None,
) -> Generator[str, None, None]:
    """Generate DOT formatted output.

    Args:
        mapper (method):
        add_self (bool):
        single_inst (bool):
    """
    indent = "  "
    name = node.tree.name
    used_keys = set()

    def _key(n: "Node"):
        return n._data_id if single_inst else n._node_id

    yield "// Generator: https://github.com/mar10/nutree/"
    yield f"digraph {name} {{"

    yield f"{indent}// Node definitions"
    if add_self:
        if node._parent:
            yield f"{indent}{_key(node)}"
        else:  # __root__ inherits tree name
            yield f'{indent}{_key(node)} [label="{name}" shape="box"]'

    for n in node:
        if single_inst:
            key = n._data_id
            if key in used_keys:
                continue
            used_keys.add(key)
        else:
            key = n._node_id

        yield f'{indent}{key} [label="{n.name}"]'

    yield ""
    yield f"{indent}// Edge definitions"
    for n in node:
        if not add_self and n._parent is node:
            continue
        # parent_key = _key(n._parent) if n._parent else 0
        # yield f"{indent}{parent_key} -> {_key(n)}"
        yield f"{indent}{_key(n._parent)} -> {_key(n)}"

    yield "}"


def tree_to_dotfile(
    tree: "Tree",
    target: Union[IO[str], str, PurePath],
    *,
    format=None,
    add_root=True,
    single_inst=True,
    node_mapper=None,
    edge_mapper=None,
):
    if isinstance(target, (str, PurePath)):
        with open(target, "w") as fp:
            tree.to_dotfile(
                fp,
                add_root=add_root,
                single_inst=single_inst,
                node_mapper=node_mapper,
                edge_mapper=edge_mapper,
            )
        if format:
            if not pydot:
                raise RuntimeError("Need pydot installed to convert DOT output.")
            pydot.call_graphviz(
                "dot",
                ["-O", f"-T{format}", target],
                working_dir=os.path.dirname(target),
            )
            # https://graphviz.org/docs/outputs/
            # check_call(f"dot -h")
            # check_call(f"dot -O -T{format} {target}")
            # check_call(f"dot -o{target}.{format} -T{format} {target}")
        return

    if format:
        raise RuntimeError("Need a filepath to convert DOT output.")

    with tree:
        for line in tree.to_dot(
            add_root=add_root,
            single_inst=single_inst,
            node_mapper=node_mapper,
            edge_mapper=edge_mapper,
        ):
            target.write(line + "\n")
    return


# def tree_from_dot(tree, dot):
#     pass
