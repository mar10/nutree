# (c) 2021-2024 Martin Wendt; see https://github.com/mar10/nutree
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
"""
# ruff: noqa: T201, T203 `print` found

from typing import Generic, Iterator, TypeVar

import pytest

pytest.skip(allow_module_level=True)

try:
    from typing import Self
except ImportError:
    # from typing_extensions import Self
    typing_extensions = pytest.importorskip("typing_extensions")
    Self = typing_extensions.Self


ElementType = TypeVar("ElementType", bound="Element")


class Element:
    def __init__(self, parent: Self, name: str):
        self.name = name
        self.children: list[ElementType] = []

    def __repr__(self):
        return f"{self.__class__.__name__}({self.name})"

    def get_pred(self) -> Self:
        return self.parent.children[0]


class AgedElement(Element):
    def __init__(self, parent: Self, name: str, age: int):
        super().__init__(parent, name)
        self.age = age

    def __repr__(self):
        return f"{self.__class__.__name__}({self.name}, {self.age})"

    def is_adult(self) -> bool:
        return self.age >= 18


class Container(Generic[ElementType]):
    def __init__(self, name: str):
        # root = Element(None, "__root__")
        self.name = name
        self.children: ElementType = []

    def add(self, name: ElementType) -> ElementType:
        self.children.append(ElementType(self, name))

    def __iter__(self) -> Iterator[ElementType]:
        return iter(self.children)

    def __repr__(self):
        return f"{self.__clas__.__name__}({self.name})"


class AgedContainer(Container[AgedElement]):
    def __init__(self, name: str):
        self.name = name
        self.children: ElementType = []

    def add(self, name: str, age: int) -> AgedElement:
        self.children.append(AgedElement)

    def __iter__(self) -> Iterator[ElementType]:
        return iter(self.children)


class TestConcept:
    def test_concept(self):
        root = Container[Element]("SimpleContainer")
        root.add("a")
        root.add(Element("b"))
        root.add(Element("c"))
        root.add(AgedElement("d", 4))

        for child in root:
            print(child)

        root2 = Container[AgedElement]("")
        root2.add(AgedElement("a", 1))
        root2.add(AgedElement("b", 2))
        root2.add(AgedElement("c", 3))
        root2.add(Element("d"))

        for child in root2:
            print(child)
