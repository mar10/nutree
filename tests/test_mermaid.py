# (c) 2021-2024 Martin Wendt; see https://github.com/mar10/nutree
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
""" """
# ruff: noqa: T201, T203 `print` found

import shutil
from pathlib import Path

import pytest

from . import fixture


class TestMermaid:
    def test_serialize_mermaid_defaults(self):
        """Save/load as object tree with clones."""
        KEEP_FILES = not fixture.is_running_on_ci() and False
        tree = fixture.create_tree_simple(clones=True, name="Root")

        with fixture.WritableTempFile("w", suffix=".md") as temp_file:
            tree.to_mermaid_flowchart(temp_file.name)
            if KEEP_FILES:  # save to tests/temp/...
                shutil.copy(
                    temp_file.name,
                    Path(__file__).parent / "temp/test_mermaid_1.md",
                )

            buffer = Path(temp_file.name).read_text()
            # print(buffer)

        assert buffer.startswith("```mermaid\n")
        assert "title: Root" in buffer
        assert '0(["Root"])' in buffer
        assert '8["b11"]' in buffer
        assert "7 --> 8" in buffer

    def test_serialize_mermaid_mappers(self):
        """Save/load as object tree with clones."""
        KEEP_FILES = not fixture.is_running_on_ci() and False
        tree = fixture.create_tree_simple(clones=True, name="Root")

        # def node_mapper(n: Node) -> str:
        #     return f"{n.name}"

        # def edge_mapper(
        #     from_id: int, from_node: Node, to_id: int, to_node: Node
        # ) -> str:
        #     return f"{from_id}-- child -->{to_id}"

        with fixture.WritableTempFile("w", suffix=".md") as temp_file:
            tree.to_mermaid_flowchart(
                temp_file.name,
                # add_root=False,
                title=False,
                headers=["classDef default fill:#f9f,stroke:#333,stroke-width:1px;"],
                root_shape='[["{node.name}"]]',
                node_mapper='[/"{node.name}"/]',
                edge_mapper='{from_id}-. "{to_node.get_index()}" .->{to_id}',
                # unique_nodes=False,
                # format="png",
                # mmdc_options={"--theme": "forest"},
            )
            if KEEP_FILES:  # save to tests/temp/...
                shutil.copy(
                    temp_file.name,
                    Path(__file__).parent / "temp/test_mermaid_2.md",
                )

            buffer = Path(temp_file.name).read_text()
            # print(buffer)

        assert buffer.startswith("```mermaid\n")
        assert "title: Root" not in buffer
        assert '0[["Root"]]' in buffer
        assert '8[/"b11"/]' in buffer
        assert '7-. "1" .->8' in buffer
        assert "classDef default fill" in buffer

    def test_serialize_mermaid_typed(self):
        """Save/load as  object tree with clones."""
        KEEP_FILES = not fixture.is_running_on_ci() and False
        tree = fixture.create_typed_tree_simple(clones=True, name="Root")

        with fixture.WritableTempFile("w", suffix=".md") as temp_file:
            tree.to_mermaid_flowchart(
                temp_file.name,
                title="Typed Tree",
                direction="LR",
                # add_root=False,
                # node_mapper=lambda node: f"{node}",
            )
            if KEEP_FILES:  # save to tests/temp/...
                shutil.copy(
                    temp_file.name,
                    Path(__file__).parent / "temp/test_mermaid_3.md",
                )

            buffer = Path(temp_file.name).read_text()
            print(buffer)

        assert buffer.startswith("```mermaid\n")
        assert "title: Typed Tree" in buffer
        assert '0(["Root"])' in buffer
        assert '8["func2"]' in buffer
        assert '0-- "function" -->8' in buffer

    # @pytest.mark.xfail(reason="mmdc may not be installed")
    def test_serialize_mermaid_png(self):
        """Save/load as typed object tree with clones."""
        if not shutil.which("mmdc"):
            raise pytest.skip("mmdc not installed")

        KEEP_FILES = not fixture.is_running_on_ci() and False
        FORMAT = "png"

        tree = fixture.create_typed_tree_simple(clones=True, name="Root")

        with fixture.WritableTempFile("w", suffix=f".{FORMAT}") as temp_file:
            tree.to_mermaid_flowchart(
                temp_file.name,
                title="Typed Tree",
                direction="LR",
                format=FORMAT,
            )
            if KEEP_FILES:  # save to tests/temp/...
                shutil.copy(
                    temp_file.name,
                    Path(__file__).parent / f"temp/test_mermaid_4.{FORMAT}",
                )
