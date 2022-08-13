# -*- coding: utf-8 -*-
# (c) 2021-2022 Martin Wendt; see https://github.com/mar10/nutree
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
"""
import re

from nutree.typed_tree import ANY_KIND, TypedNode, TypedTree, _SystemRootTypedNode

from . import fixture


class TestTypedTree:
    def test_add_child(self):
        tree = TypedTree("fixture")

        # --- Empty tree
        assert not tree, "empty tree is falsy"
        assert tree.count == 0
        assert len(tree) == 0
        assert f"{tree}" == "TypedTree<'fixture'>"
        assert isinstance(tree._root, _SystemRootTypedNode)

        # ---
        func = tree.add("func1", kind="function")

        assert isinstance(func, TypedNode)
        assert (
            re.sub(r"data_id=[-\d]+>", "data_id=*>", f"{func}")
            == "TypedNode<'func1', data_id=*>"
        )

        fail1 = func.add("fail1", kind="failure")

        fail1.add("cause1", kind="cause")
        fail1.add("cause2", kind="cause")

        fail1.add("eff1", kind="effect")
        fail1.add("eff2", kind="effect")

        func.add("fail2", kind="failure")

        func2 = tree.add("func2", kind="function")

        assert fixture.check_content(
            tree,
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
           """,
        )

        assert len(fail1.children) == 4
        assert fail1.get_children(kind=ANY_KIND) == fail1.children

        assert len(fail1.get_children(kind="cause")) == 2
        assert fail1.get_children(kind="unknown") == []

        assert fail1.has_children(kind="unknown") is False
        assert fail1.has_children(kind=ANY_KIND) is True
        assert fail1.has_children(kind="cause") is True

        assert fail1.first_child(kind="cause").name == "cause1"
        assert fail1.first_child(kind="effect").name == "eff1"
        assert fail1.first_child(kind=ANY_KIND).name == "cause1"
        assert fail1.first_child(kind="unknown") is None

        assert fail1.last_child(kind="cause").name == "cause2"
        assert fail1.last_child(kind="effect").name == "eff2"
        assert fail1.last_child(kind=ANY_KIND).name == "eff2"
        assert fail1.last_child(kind="unknown") is None

        cause1 = tree["cause1"]
        cause2 = tree["cause2"]
        eff1 = tree["eff1"]
        eff2 = tree["eff2"]

        assert cause2.get_siblings(any_kind=True, add_self=True) == fail1.get_children(
            kind=ANY_KIND
        )
        assert cause2.get_siblings() != fail1.get_children(kind=ANY_KIND)
        assert cause2.get_siblings(add_self=True) == fail1.get_children(kind="cause")

        assert cause2.parent is fail1

        assert len(list(tree.iter_by_type("cause"))) == 2

        assert cause2.get_children("undefined") == []

        assert cause2.first_child(ANY_KIND) is None
        assert cause2.first_child("undefined") is None

        assert cause2.last_child(ANY_KIND) is None
        assert cause2.last_child("undefined") is None

        assert cause2.first_sibling() is cause1
        assert cause2.first_sibling(any_kind=True) is cause1

        assert cause2.last_sibling() is cause2
        assert cause2.last_sibling(any_kind=True) is eff2

        assert cause1.prev_sibling() is None
        assert cause1.prev_sibling(any_kind=True) is None
        assert cause2.prev_sibling() is cause1
        assert cause2.prev_sibling(any_kind=True) is cause1

        assert cause1.next_sibling() is cause2
        assert cause1.next_sibling(any_kind=True) is cause2
        assert cause2.next_sibling() is None
        assert cause2.next_sibling(any_kind=True) is eff1

        assert eff1.is_first_sibling()
        assert not eff1.is_first_sibling(any_kind=True)
        assert not eff2.is_first_sibling()

        assert not eff1.is_last_sibling()
        assert not eff1.is_last_sibling(any_kind=True)
        assert eff2.is_last_sibling()
        assert eff2.is_last_sibling(any_kind=True)

        assert eff1.get_index() == 0
        assert eff2.get_index() == 1
        assert eff1.get_index(any_kind=True) == 2

        # Copy node
        assert not fail1.is_clone()
        func2.add(fail1)
        assert fail1.is_clone()

        subtree = func2.copy()
        assert isinstance(subtree, TypedTree)

    def test_graph(self):
        tree = TypedTree("fixture")

        alice = tree.add("Alice")
        bob = tree.add("Bob")

        alice.add("Carol", kind="friends")

        alice.add("Bob", kind="family")
        bob.add("Alice", kind="family")
        bob.add("Dan", kind="friends")

        # carol.add(bob, kind="friends")

        assert fixture.check_content(
            tree,
            """
            TypedTree<*>
            +- child → Alice
            |  +- friends → Carol
            |  `- family → Bob
            `- child → Bob
               +- family → Alice
               `- friends → Dan
           """,
        )

        # with fixture.WritableTempFile("w", suffix=".png") as temp_file:

        #     tree.to_dotfile(
        #         # temp_file.name,
        #         "/Users/martin/Downloads/tree.png",
        #         format="png",
        #         add_root=False,
        #         # node_mapper=node_mapper,
        #         # edge_mapper=edge_mapper,
        #         # unique_nodes=False,
        #     )
        #     assert False

    def test_graph_product(self):
        tree = TypedTree("Pencil")

        func = tree.add("Write on paper", kind="function")
        fail = func.add("Wood shaft breaks", kind="failure")
        fail.add("Unable to write", kind="effect")
        fail.add("Injury from splinter", kind="effect")
        fail.add("Wood too soft", kind="cause")

        fail = func.add("Lead breaks", kind="failure")
        fail.add("Cannot erase (dissatisfaction)", kind="effect")
        fail.add("Lead material too brittle", kind="cause")

        func = tree.add("Erase text", kind="function")

        assert fixture.check_content(
            tree,
            """
            TypedTree<*>
            +- function → Write on paper
            |  +- failure → Wood shaft breaks
            |  |  +- effect → Unable to write
            |  |  +- effect → Injury from splinter
            |  |  `- cause → Wood too soft
            |  `- failure → Lead breaks
            |     +- effect → Cannot erase (dissatisfaction)
            |     `- cause → Lead material too brittle
            `- function → Erase text
           """,
        )
        # tree.print()
        # raise

        # with fixture.WritableTempFile("w", suffix=".png") as temp_file:

        #     tree.to_dotfile(
        #         # temp_file.name,
        #         "/Users/martin/Downloads/tree_graph_pencil.png",
        #         format="png",
        #         graph_attrs={"rankdir": "LR"},
        #         # add_root=False,
        #         # node_mapper=node_mapper,
        #         # edge_mapper=edge_mapper,
        #         # unique_nodes=False,
        #     )
        #     assert False

    def test_rdf(self):
        tree = TypedTree("Pencil")

        func = tree.add("Write on paper", kind="function")
        fail = func.add("Wood shaft breaks", kind="failure")
        fail.add("Unable to write", kind="effect")
        fail.add("Injury from splinter", kind="effect")
        fail.add("Wood too soft", kind="cause")

        fail = func.add("Lead breaks", kind="failure")
        fail.add("Cannot erase (dissatisfaction)", kind="effect")
        fail.add("Lead material too brittle", kind="cause")

        func = tree.add("Erase text", kind="function")

        assert fixture.check_content(
            tree,
            """
            TypedTree<*>
            +- function → Write on paper
            |  +- failure → Wood shaft breaks
            |  |  +- effect → Unable to write
            |  |  +- effect → Injury from splinter
            |  |  `- cause → Wood too soft
            |  `- failure → Lead breaks
            |     +- effect → Cannot erase (dissatisfaction)
            |     `- cause → Lead material too brittle
            `- function → Erase text
           """,
        )

        # tree.print()
        # print()

        g = tree.to_rdf_graph()

        turtle_fmt = g.serialize()
        print(turtle_fmt)
        print()
        assert 'nutree:kind "failure"' in turtle_fmt
        assert 'nutree:name "Wood shaft breaks' in turtle_fmt

        # Basic triple matching: All cause types
        # Note that Literal will be `None` if rdflib is not available
        from nutree.rdf import NUTREE_NS, Literal

        cause_kind = Literal("cause")
        n = 0
        for s, _p, o in g.triples((None, NUTREE_NS.kind, cause_kind)):
            name = g.value(s, NUTREE_NS.name)
            print(f"{name} is a {o}")
            n += 1
        print()
        assert n == 2

        # SPARQL query:

        query = """
        PREFIX nutree: <http://wwwendt.de/namespace/nutree/rdf/0.1/>

        SELECT ?data_id ?kind ?name
        WHERE {
            BIND("cause" as ?kind)

            ?data_id nutree:kind ?kind ;
                nutree:name ?name .
        }
        """

        qres = g.query(query)
        n = 0
        for row in qres:
            print(f"{row.data_id} {row.name} is a {row.kind}")
            n += 1
        assert n == 2

        # tree.print()
        # raise

        node = tree["Wood shaft breaks"]

        g = node.to_rdf_graph()
        print(g.serialize())

        calls = 0

        def node_mapper(graph, graph_node, tree_node):
            nonlocal calls
            calls += 1

        g = node.to_rdf_graph(add_self=False, node_mapper=node_mapper)
        print(g.serialize())

        assert calls == 3
        # raise
