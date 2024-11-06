# (c) 2021-2024 Martin Wendt; see https://github.com/mar10/nutree
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
""" """
# ruff: noqa: T201, T203 `print` found
# pyright: reportAttributeAccessIssue=false

from nutree.typed_tree import TypedTree

from . import fixture


class TestRDF:
    def test_tree(self):
        tree = fixture.create_tree_simple()

        g = tree.to_rdf_graph()

        turtle_fmt = g.serialize()
        tree.print()
        print(turtle_fmt)

        assert "nutree:kind" not in turtle_fmt
        assert 'nutree:name "b1" .' in turtle_fmt

    def test_typed_tree(self):
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

        eff1 = tree["Unable to write"]
        eff2 = tree["Injury from splinter"]
        cause1 = tree["Wood too soft"]

        assert eff1.first_sibling() is eff1
        assert eff1.last_sibling() is eff2
        assert eff1.last_sibling(any_kind=True) is cause1

        assert cause1.get_index() == 0
        assert cause1.get_index(any_kind=True) == 2

        assert len(list(tree.iter_by_type("effect"))) == 3

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
