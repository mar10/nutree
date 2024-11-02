# (c) 2021-2024 Martin Wendt and contributors; see https://github.com/mar10/nutree
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
Implement diff/merge algorithms.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # Imported by type checkers, but prevent circular includes
    from nutree.tree import Node, Tree

from enum import Enum


class DiffClassification(Enum):
    ADDED = 1
    REMOVED = 2
    MOVED_HERE = 3
    MOVED_TO = 4


#: Alias for DiffClassification
DC = DiffClassification


def _find_child(arr, child):
    for i, c in enumerate(arr):
        if c == child:
            return (i, c)
    return (-1, None)


def _copy_children(source: Node, dest: Node, add_set: set, meta: tuple) -> None:
    assert source.has_children() and not dest.has_children()
    for n in source.children:
        n_dest = dest.append_child(n)
        add_set.add(n_dest._node_id)
        if meta:
            n_dest.set_meta(*meta)
        if n._children:
            # meta is only set on top node
            _copy_children(n, n_dest, add_set, meta=None)  # type: ignore
    return


def diff_node_formatter(node):
    """Use with :meth:`~nutree.tree.format` or :meth:`~nutree.tree.print`
    `repr=...` arguments."""
    s = f"{node.name}"
    meta = node.meta

    if meta:
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
        elif isinstance(dc, tuple):  # == DC.SHIFTED:
            ofs = dc[1] - dc[0]
            flags.append(f"Order {ofs:+d}")  # ⇳ ⇵
            # flags.append("Shifted")  # ⇳ ⇵
        elif dc:
            flags.append(f"{dc}")

        if meta.get("dc_renumbered"):
            flags.append("Renumbered")
        if meta.get("dc_cleared"):
            flags.append("Children cleared")

        flags = "[" + "], [".join(flags) + "]"
        s += f" - {flags}"

    return s


def diff_tree(t0: Tree[Any], t1: Tree[Any], *, ordered=False, reduce=False) -> Tree:
    from nutree import Tree

    t2 = Tree(f"diff({t0.name!r}, {t1.name!r})")
    added_nodes = set()
    removed_nodes = set()

    def compare(p0: Node, p1: Node, p2: Node):
        p0_data_ids = set()
        # `p0.children` always returns an (empty) array
        for i0, c0 in enumerate(p0.children):
            p0_data_ids.add(c0._data_id)
            i1, c1 = _find_child(p1.children, c0)

            c2 = p2.add(c0)
            if i0 == i1:
                # Exact match of node and position
                pass
            elif c1:
                # Matching node, but at another position
                if ordered:
                    p2.set_meta("dc_renumbered", True)
                    c2.set_meta("dc", (i0, i1))
            else:
                # t0 node is not found in t1
                c2.set_meta("dc", DC.REMOVED)
                removed_nodes.add(c2._node_id)

            if c0._children:
                if c1:
                    compare(c0, c1, c2)
                    # if c1._children:
                    #     # c0 and c1 have children: Recursively visit peer nodes
                    #     compare(c0, c1, c2)
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
                    compare(c0, c1, c2)
                else:
                    # Neither c0 nor c1 have children: Nothing to do
                    pass

        # print(p1, p1._children, p0_data_ids)
        # Collect t1 nodes that are not in t0:
        for c1 in p1.children:  # `p1.children` always returns an (empty) array
            # print("  ", c1, c1._data_id in p0_data_ids)
            if c1._data_id not in p0_data_ids:
                c2 = p2.add(c1)
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
        return  # def compare()

    compare(t0._root, t1._root, t2._root)

    # Re-classify: check added/removed nodes for move operations
    # print(added_nodes)
    # print(removed_nodes)
    for nid in added_nodes:
        added_node = t2._node_by_id[nid]
        # print(added_node)
        other_clones = added_node.get_clones()
        # print(other_clones)
        removed_clones = [n for n in other_clones if n.get_meta("dc") == DC.REMOVED]
        if removed_clones:
            added_node.set_meta("dc", DC.MOVED_HERE)
            for n in removed_clones:
                n.set_meta("dc", DC.MOVED_TO)

    # Purge unchanged parts from tree
    if reduce:

        def pred(node):
            return bool(node.get_meta("dc"))

        t2.filter(predicate=pred)

    return t2
