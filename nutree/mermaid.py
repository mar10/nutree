# (c) 2021-2023 Martin Wendt; see https://github.com/mar10/nutree
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
Functions and declarations to support 
`Mermaid <https://mermaid-js.github.io/mermaid/#/flowchart>`_ exports.
"""
# ruff: noqa: E731 # do not assign a lambda expression, use a def

from __future__ import annotations

from pathlib import Path
from subprocess import CalledProcessError, check_output
from typing import IO, TYPE_CHECKING, Callable, Iterable, Iterator, Literal

from .common import DataIdType

if TYPE_CHECKING:  # Imported by type checkers, but prevent circular includes
    from .node import Node

MermaidDirectionType = Literal["LR", "RL", "TB", "TD", "BT"]
MermaidFormatType = Literal["svg", "pdf", "png"]

#: Callback to map a node to a Mermaid node definition string.
#: The callback is called with the following arguments:
#: `node`.
MermaidNodeMapperCallbackType = Callable[["Node"], str]

#: Callback to map a node to a Mermaid edge definition string.
#: The callback is called with the following arguments:
#: `from_id`, `from_node`, `to_id`, `to_node`.
MermaidEdgeMapperCallbackType = Callable[[int, "Node", int, "Node"], str]

DEFAULT_DIRECTION: MermaidDirectionType = "TD"

DEFAULT_NODE_TEMPLATE: str = "{node.name}"

DEFAULT_EDGE_TEMPLATE: str = "{from_id} --> {to_id}"
DEFAULT_EDGE_TEMPLATE_TYPED: str = '{from_id}-- "{kind}" -->{to_id}'


def _node_to_mermaid_flowchart_iter(
    *,
    node: Node,
    as_markdown: bool = True,
    direction: MermaidDirectionType = "TD",
    title: str | bool | None = True,
    add_root: bool = True,
    unique_nodes: bool = True,
    headers: Iterable[str] | None = None,
    node_mapper: MermaidNodeMapperCallbackType | None | str = None,
    edge_mapper: MermaidEdgeMapperCallbackType | None | str = None,
) -> Iterator[str]:
    """Generate Mermaid formatted output line-by-line.

    https://mermaid.js.org/syntax/flowchart.html
    Args:
        mapper (method):
        add_self (bool):
        unique_nodes (bool):
    """
    id_to_idx = {}

    def _id(n: Node) -> DataIdType:
        return n._data_id if unique_nodes else n._node_id

    if node_mapper is None:
        node_mapper = lambda node: DEFAULT_NODE_TEMPLATE.format(node=node)
    elif isinstance(node_mapper, str):
        templ = node_mapper
        node_mapper = lambda node: templ.format(node=node)

    if isinstance(edge_mapper, str):
        templ = edge_mapper

        def edge_mapper(from_id, from_node, to_id, to_node):
            return templ.format(
                from_id=from_id, from_node=from_node, to_id=to_id, to_node=to_node
            )

    elif edge_mapper is None:

        def edge_mapper(from_id, from_node, to_id, to_node):
            kind = getattr(to_node, "kind", None)
            templ = DEFAULT_EDGE_TEMPLATE_TYPED if kind else DEFAULT_EDGE_TEMPLATE
            return templ.format(
                from_id=from_id,
                from_node=from_node,
                to_id=to_id,
                to_node=to_node,
                kind=kind,
            )

    else:
        assert callable(edge_mapper), "edge_mapper must be str or callable"

    if as_markdown:
        yield "```mermaid"

    if title:
        yield "---"
        yield f"title: {node.name if title is True else title}"
        yield "---"

    yield ""
    yield "%% Generator: https://github.com/mar10/nutree/"
    yield ""

    yield f"flowchart {direction}"

    if headers:
        yield ""
        yield "%% Headers:"
        yield from headers

    yield ""
    yield "%% Nodes:"
    if add_root:
        id_to_idx[_id(node)] = 0
        name = node.name
        yield f'0{{{{"{name}"}}}}'

    idx = 1
    for n in node:
        key = _id(n)
        if key in id_to_idx:
            continue  # we use the initial clone instead
        id_to_idx[key] = idx

        name = node_mapper(n)
        yield f'{idx}("{name}")'
        idx += 1

    yield ""
    yield "%% Edges:"
    for n in node:
        if not add_root and n._parent is node:
            continue
        parent_key = _id(n._parent)
        key = _id(n)

        parent_idx = id_to_idx[parent_key]
        idx = id_to_idx[key]
        yield edge_mapper(parent_idx, n._parent, idx, n)

    if as_markdown:
        yield "```"
    return


def node_to_mermaid_flowchart(
    node: Node,
    target: IO[str] | str | Path,
    *,
    as_markdown: bool = True,
    direction: MermaidDirectionType = "TD",
    title: str | bool | None = True,
    format: MermaidFormatType | None = None,
    mmdc_options: dict | None = None,
    add_root: bool = True,
    unique_nodes: bool = True,
    headers: Iterable[str] | None = None,
    node_mapper: MermaidNodeMapperCallbackType | None = None,
    edge_mapper: MermaidEdgeMapperCallbackType | None = None,
) -> None:
    """Write a Mermaid flowchart to a file or stream."""
    if format:
        as_markdown = False

    if mmdc_options is None:
        mmdc_options = {}

    def _write(fp):
        for line in _node_to_mermaid_flowchart_iter(
            node=node,
            as_markdown=as_markdown,
            direction=direction,
            title=title,
            add_root=add_root,
            unique_nodes=unique_nodes,
            headers=headers,
            node_mapper=node_mapper,
            edge_mapper=edge_mapper,
        ):
            fp.write(line + "\n")

    if isinstance(target, str):
        target = Path(target)

    if isinstance(target, Path):
        mm_path = target.with_suffix(".tmp") if format else target

        with open(mm_path, "w") as fp:
            _write(fp)

        if format:
            # Convert Mermaid output using mmdc
            # See https://github.com/mermaid-js/mermaid-cli

            # Make sure the source markdown stream is flushed
            # fp.close()

            mmdc_options["-i"] = str(mm_path)
            mmdc_options["-o"] = str(target)
            mmdc_options["-e"] = format

            cmd = ["mmdc"]
            for k, v in mmdc_options.items():
                cmd.extend((k, v))

            try:
                check_output(cmd)
            except CalledProcessError as e:
                raise RuntimeError(
                    f"Could not convert Mermaid output using {cmd}.\n"
                    f"Error: {e.output.decode()}"
                ) from e
            except FileNotFoundError as e:
                raise RuntimeError(
                    f"Could not convert Mermaid output using {cmd}.\n"
                    "Mermaid CLI (mmdc) not found.\n"
                    "Please install it with `npm install -g mermaid.cli`."
                ) from e
        return

    elif format:
        raise RuntimeError("Need a filepath to convert Mermaid output.")

    _write(target)
    return
