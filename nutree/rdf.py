# (c) 2021-2023 Martin Wendt; see https://github.com/mar10/nutree
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
Functions and declarations to implement `rdflib <https://github.com/RDFLib/rdflib>`_.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Union

from nutree.common import IterationControl

if TYPE_CHECKING:  # Imported by type checkers, but prevent circular includes
    from .node import Node

    # from .tree import Tree
    from .typed_tree import TypedNode, TypedTree

# Export some common rdflib attributes, so they can be accessed as
# `from nutree.rdf import Literal` without having to `import rdflib`
# (which may not be available):
try:
    import rdflib
    from rdflib import Graph, IdentifiedNode, Literal, URIRef
    from rdflib.namespace import RDF, XSD, DefinedNamespace, Namespace
except ImportError:
    rdflib = None
    Graph = IdentifiedNode = Literal = URIRef = None
    RDF = XSD = DefinedNamespace = Namespace = None
    # raise

RDFMapperCallbackType = Callable[[Graph, IdentifiedNode, "Node"], Union[None, bool]]

if Namespace:

    class NUTREE_NS(DefinedNamespace):
        """
        nutree vocabulary
        """

        _fail = True

        # diff_meta:
        index: URIRef  #
        has_child: URIRef  #
        kind: URIRef  #
        name: URIRef  #
        system_root: URIRef  #

        _NS = Namespace("http://wwwendt.de/namespace/nutree/rdf/0.1/")

else:  # rdflib unavailable
    NUTREE_NS = None


def _make_graph() -> Graph:
    if not rdflib:
        raise RuntimeError("Need rdflib installed.")
    graph = Graph()

    graph.bind("nutree", NUTREE_NS)
    graph.bind("rdf", RDF)
    return graph


def _add_child_node(
    graph: Graph,
    parent_graph_node: IdentifiedNode | None,
    tree_node: TypedNode,
    index: int,
    node_mapper: RDFMapperCallbackType,
) -> IdentifiedNode | IterationControl | bool:
    """"""
    graph_node = Literal(tree_node.data_id)

    # Mapper can call `graph.add()`
    if node_mapper:
        try:
            res = node_mapper(graph, graph_node, tree_node)
            if isinstance(res, (IterationControl, StopIteration)):
                return res
        except (IterationControl, StopIteration) as e:
            return e  # SkipBranch, SelectBranch, StopTraversal, StopIteration
    else:
        res = None

    if parent_graph_node:
        graph.add((parent_graph_node, NUTREE_NS.has_child, graph_node))

    if res is False:
        # node_mapper wants to prevent adding standard attributes?
        return False

    # Add standard attributes

    graph.add((graph_node, NUTREE_NS.kind, Literal(tree_node.kind)))
    graph.add((graph_node, NUTREE_NS.name, Literal(tree_node.name)))
    if index >= 0:
        graph.add((graph_node, NUTREE_NS.index, Literal(index, datatype=XSD.integer)))

    # if add_diff_meta:
    #     pass

    return graph_node


def _add_child_nodes(
    graph: Graph,
    graph_node: IdentifiedNode,
    tree_node: TypedNode,
    node_mapper: RDFMapperCallbackType = None,
) -> None:
    """"""
    for index, child_tree_node in enumerate(tree_node._children or ()):
        cgn = _add_child_node(
            graph,
            parent_graph_node=graph_node,
            tree_node=child_tree_node,
            index=index,
            node_mapper=node_mapper,
        )
        if child_tree_node.has_children:
            _add_child_nodes(graph, cgn, child_tree_node, node_mapper)

    return


def node_to_rdf(
    tree_node: TypedNode,
    *,
    add_self: bool = True,
    node_mapper: RDFMapperCallbackType = None,
) -> Graph:
    """Generate DOT formatted output line-by-line."""
    graph = _make_graph()

    if add_self:
        root_graph_node = _add_child_node(
            graph,
            parent_graph_node=None,
            tree_node=tree_node,
            index=-1,
            node_mapper=node_mapper,
        )
    else:
        root_graph_node = None

    _add_child_nodes(
        graph,
        graph_node=root_graph_node,
        tree_node=tree_node,
        node_mapper=node_mapper,
    )

    return graph


def tree_to_rdf(
    tree: TypedTree,
    *,
    node_mapper: RDFMapperCallbackType = None,
) -> Graph:
    graph = _make_graph()

    root_graph_node = URIRef(NUTREE_NS.system_root)
    graph.add((root_graph_node, NUTREE_NS.name, Literal(tree.name)))

    _add_child_nodes(
        graph, graph_node=root_graph_node, tree_node=tree._root, node_mapper=node_mapper
    )
    return graph
