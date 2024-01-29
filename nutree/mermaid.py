# (c) 2021-2023 Martin Wendt; see https://github.com/mar10/nutree
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
Functions and declarations to support 
`Mermaid <https://mermaid-js.github.io/mermaid/#/flowchart>`_ exports.
"""
from __future__ import annotations

from pathlib import Path
from typing import IO, TYPE_CHECKING, Iterator, Optional, Union

from .common import MapperCallbackType, call_mapper

if TYPE_CHECKING:  # Imported by type checkers, but prevent circular includes
    from .node import Node
    from .tree import Tree


def node_to_dot(
    node: Node,
    *,
    add_self=False,
    unique_nodes=True,
    graph_attrs=None,
    node_attrs=None,
    edge_attrs=None,
    node_mapper=None,
    edge_mapper=None,
) -> Iterator[str]:
    """Generate DOT formatted output line-by-line.

    https://graphviz.org/doc/info/attrs.html
    Args:
        mapper (method):
        add_self (bool):
        unique_nodes (bool):
    """
    indent = "  "
    name = node.tree.name
    used_keys = set()

    def _key(n: Node):
        return n._data_id if unique_nodes else n._node_id

    def _attr_str(attr_def: dict, mapper=None, node=None):
        if mapper:
            if attr_def is None:
                attr_def = {}
            call_mapper(mapper, node, attr_def)
        if not attr_def:
            return ""
        attr_str = " ".join(f'{k}="{v}"' for k, v in attr_def.items())  # noqa: B028
        return " [" + attr_str + "]"

    yield "# Generator: https://github.com/mar10/nutree/"
    yield f'digraph "{name}" {{'  # noqa: B028

    if graph_attrs or node_attrs or edge_attrs:
        yield ""
        yield f"{indent}# Default Definitions"
        if graph_attrs:
            yield f"{indent}graph {_attr_str(graph_attrs)}"
        if node_attrs:
            yield f"{indent}node {_attr_str(node_attrs)}"
        if edge_attrs:
            yield f"{indent}edge {_attr_str(edge_attrs)}"

    yield ""
    yield f"{indent}# Node Definitions"

    if add_self:
        if node._parent:
            attr_def = {}
        else:  # __root__ inherits tree name by default
            attr_def = {"label": f"{name}", "shape": "box"}

        attr_str = _attr_str(attr_def, node_mapper, node)
        yield f"{indent}{_key(node)}{attr_str}"

    for n in node:
        if unique_nodes:
            key = n._data_id
            if key in used_keys:
                continue
            used_keys.add(key)
        else:
            key = n._node_id

        attr_def = {"label": n.name}
        attr_str = _attr_str(attr_def, node_mapper, n)
        yield f"{indent}{key}{attr_str}"

    yield ""
    yield f"{indent}# Edge Definitions"
    for n in node:
        if not add_self and n._parent is node:
            continue
        attr_def = {}
        attr_str = _attr_str(attr_def, edge_mapper, n)
        yield f"{indent}{_key(n._parent)} -> {_key(n)}{attr_str}"

    yield "}"


def tree_to_mermaid(
    tree: Tree,
    target: Union[IO[str], str, Path],
    *,
    format=None,
    add_root=True,
    unique_nodes=True,
    graph_attrs=None,
    node_attrs=None,
    edge_attrs=None,
    node_mapper: Optional[MapperCallbackType] = None,
    edge_mapper: Optional[MapperCallbackType] = None,
) -> None:
    if isinstance(target, str):
        target = Path(target)

    if isinstance(target, Path):
        if format:
            dot_path = target.with_suffix(".gv")
        else:
            dot_path = target

        # print("write", dot_path)
        with open(dot_path, "w") as fp:
            tree_to_mermaid(
                tree=tree,
                target=fp,
                add_root=add_root,
                unique_nodes=unique_nodes,
                graph_attrs=graph_attrs,
                node_attrs=node_attrs,
                edge_attrs=edge_attrs,
                node_mapper=node_mapper,
                edge_mapper=edge_mapper,
            )
        return

    # `target` is suppoesed to be an open, writable filelike
    if format:
        raise RuntimeError("Need a filepath to convert DOT output.")

    with tree:
        for line in tree.to_mermaid(
            add_root=add_root,
            unique_nodes=unique_nodes,
            graph_attrs=graph_attrs,
            node_attrs=node_attrs,
            edge_attrs=edge_attrs,
            node_mapper=node_mapper,
            edge_mapper=edge_mapper,
        ):
            target.write(line + "\n")
    return
