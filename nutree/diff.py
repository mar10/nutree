# (c) 2021-2024 Martin Wendt and contributors; see https://github.com/mar10/nutree
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
Implement diff/merge algorithms.
"""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, Union

if TYPE_CHECKING:  # Imported by type checkers, but prevent circular includes
    from nutree.tree import Node, Tree


class DiffClassification(Enum):
    ADDED = 1
    REMOVED = 2
    MOVED_HERE = 3
    MOVED_TO = 4


#: Alias for DiffClassification
DC = DiffClassification

#: Callback for `tree.diff(compare=...)`
#: Return `False` if nodes are considered equal, `False` if different, or any
#: value to indicate a custom classification.
DiffCompareCallbackType = Callable[["Node", "Node", "Node"], Union[bool, Any]]


def _find_child(child_list: list[Node], child: Node) -> tuple[int, Node | None]:
    """Search for a node with the same data id and Return index and node."""
    for i, c in enumerate(child_list):
        if c.data_id == child.data_id:
            return (i, c)
    return (-1, None)


def _check_modified(
    c0: Node, c1: Node, c2: Node, compare: DiffCompareCallbackType | bool
) -> bool:
    """Test if nodes are different and set metadata if so."""
    if not compare:
        return False
    if compare is True:
        if c0.data != c1.data:
            c2.set_meta("dc_modified", True)
            return True
    else:
        if compare(c0, c1, c2):
            c2.set_meta("dc_modified", True)
            return True
    return False


def _copy_children(source: Node, dest: Node, add_set: set, meta: tuple | None) -> None:
    assert source.has_children() and not dest.has_children()
    for n in source.children:
        n_dest = dest.append_child(n)
        add_set.add(n_dest._node_id)
        if meta:
            n_dest.set_meta(*meta)
        if n._children:
            # meta is only set on top node
            _copy_children(n, n_dest, add_set, meta=None)
    return


def diff_node_formatter(node: Node) -> str:
    """Use with :meth:`~nutree.tree.format` or :meth:`~nutree.tree.print`
    `repr=...` arguments."""
    s = f"{node.name}"
    meta = node.meta

    if not meta:
        return s

    flags = []
    dc = meta.get("dc")
    if dc is None:
        pass
    elif dc == DC.ADDED:
        flags.append("Added")  # ☆ 🌟
    elif dc == DC.REMOVED:
        flags.append("Removed")  # × ❌
    elif dc == DC.MOVED_HERE:
        flags.append("Moved here")  # ←
    elif dc == DC.MOVED_TO:
        flags.append("Moved away")  # ×➡
    elif dc:  # pragma: no cover
        flags.append(f"{dc}")

    if modified := meta.get("dc_modified"):
        if isinstance(modified, str):
            flags.append(f"Modified ({modified})")
        else:
            flags.append("Modified")

    if meta.get("dc_renumbered"):  # Child order has changed
        flags.append("Renumbered")

    if order := meta.get("dc_order"):  # Node position changed
        ofs = order[1] - order[0]
        flags.append(f"Order {ofs:+d}")  # ⇳ ⇵

    # if meta.get("dc_cleared"):
    #     flags.append("Children cleared")

    if flags:
        flags_s = "[" + "], [".join(flags) + "]"
        s += f" - {flags_s}"

    return s


def diff_tree(
    t0: Tree[Any, Any],
    t1: Tree[Any, Any],
    *,
    compare: DiffCompareCallbackType | bool = True,
    ordered: bool = False,
    reduce: bool = False,
) -> Tree:
    from nutree import Tree

    t2 = Tree[Any, Any](f"diff({t0.name!r}, {t1.name!r})")
    added_nodes = set[int]()
    removed_nodes = set[int]()

    def _diff(p0: Node, p1: Node, p2: Node):
        p0_data_ids = set()

        # `p0.children` always returns an (empty) array
        for i0, c0 in enumerate(p0.children):
            p0_data_ids.add(c0._data_id)
            i1, c1 = _find_child(p1.children, c0)
            # preferably copy from T1 (which should have the current
            # modification status)
            if c1:
                c2 = p2.add(c1, data_id=c1._data_id)
            else:
                c2 = p2.add(c0, data_id=c0._data_id)

            if c1 is None:
                # t0 node is not found in t1
                c2.set_meta("dc", DC.REMOVED)
                removed_nodes.add(c2._node_id)
            else:
                # Found node with same data_id

                # Check if position changed
                if ordered and i0 != i1:
                    # Mark parent node as renumbered
                    p2.set_meta("dc_renumbered", True)
                    # Mark child node as shifted
                    c2.set_meta("dc_order", (i0, i1))

                # Check if data changed
                _check_modified(c0, c1, c2, compare)

            if c0._children:
                if c1:
                    _diff(c0, c1, c2)
                    # if c1._children:
                    #     # c0 and c1 have children: Recursively visit peer nodes
                    #     _compare(c0, c1, c2)
                    # else:
                    #     # c0 has children and c1 exists, but has no children
                    #     # TODO: copy children c0 to c2
                    #     c2.set_meta("dc_cleared", True)
                else:
                    # c0 has children, but c1 does not even exist
                    # TODO: Copy children from c0 to c2, but we need to check
                    #       if c1 is really removed or just moved-away
                    pass
            elif c1:
                if c1._children:
                    # c1 has children and c0 exists, but has no children
                    _diff(c0, c1, c2)
                else:
                    # Neither c0 nor c1 have children: Nothing to do
                    pass

        # Collect t1 nodes that are NOT in t0:
        for c1 in p1.children:  # `p1.children` always returns an (empty) array
            if c1._data_id not in p0_data_ids:
                idx = c1.get_index()  # try to maintain the order
                c2 = p2.add(c1, data_id=c1._data_id, before=idx)
                c2.set_meta("dc", DC.ADDED)
                added_nodes.add(c2._node_id)
                if c1._children:
                    # c1 has children, but c0 does not even exist
                    # TODO: Copy children from c1 to c2, but we need to check
                    #       if c1 is really added or just moved-here
                    _copy_children(c1, c2, added_nodes, ("dc", DC.ADDED))
                else:
                    # c1 does not have children and c0 does not exist:
                    # We already marked a 'new', nothing more to do.
                    pass

        return  # def _compare()

    _diff(t0._root, t1._root, t2._root)

    # Re-classify: check added/removed nodes for move operations
    for nid in added_nodes:
        added_node = t2._node_by_id[nid]
        other_clones = added_node.get_clones()
        removed_clones = [n for n in other_clones if n.get_meta("dc") == DC.REMOVED]
        if removed_clones:
            added_node.set_meta("dc", DC.MOVED_HERE)
            for n in removed_clones:
                n.set_meta("dc", DC.MOVED_TO)
                if _check_modified(n, added_node, added_node, compare):
                    n.set_meta("dc_modified", True)

    # Purge unchanged parts from tree
    if reduce:

        def pred(node):
            return bool(
                node.get_meta("dc")
                or node.get_meta("dc_modified")
                or node.get_meta("dc_order")
            )

        t2.filter(predicate=pred)

    return t2
