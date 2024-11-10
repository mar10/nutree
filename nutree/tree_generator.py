"""
Implements a generator that creates a random tree structure from a specification.

See :ref:`randomize` for details.
"""

from __future__ import annotations

import random
import sys
from abc import ABC, abstractmethod
from collections.abc import Sequence
from datetime import date, datetime, timedelta, timezone
from typing import Any, Union

from nutree.common import DictWrapper
from nutree.node import Node
from nutree.tree import Tree
from nutree.typed_tree import TypedNode

try:
    from fabulist import Fabulist

    fab = Fabulist()
except ImportError:  # pragma: no cover
    # We run without fabulist (with reduced functionality in this case)
    Fabulist = None
    fab = None

# TTree = TypeVar("TTree", bound=Tree)


# ------------------------------------------------------------------------------
# Randomizers
# ------------------------------------------------------------------------------
class Randomizer(ABC):
    """
    Abstract base class for randomizers.

    Args:
        probability (float, optional): The probability of using the randomizer.
            Must be in the range [0.0, 1.0]. Defaults to 1.0.
    """

    def __init__(self, *, probability: float = 1.0) -> None:
        assert (
            isinstance(probability, float) and 0.0 <= probability <= 1.0
        ), f"probality must be in the range [0.0 .. 1.0]: {probability}"
        self.probability = probability

    def _skip_value(self) -> bool:
        use = self.probability == 1.0 or random.random() <= self.probability
        return not use

    @abstractmethod
    def generate(self) -> Any: ...


class RangeRandomizer(Randomizer):
    """
    A randomizer class that generates random values within a specified range.

    Args:
        min_val (float| int): The minimum value of the range.
        max_val (float| int): The maximum value of the range.
        probability (float, optional): The probability of generating a value.
            Defaults to 1.0.
        none_value (Any, optional): The value to return when skipping generation.
            Defaults to None.

    Returns:
        Union[float, int, None]: The generated random value, or none_value
            if generation is skipped.
    """

    """"""

    def __init__(
        self,
        min_val: float | int,
        max_val: float | int,
        *,
        probability: float = 1.0,
        none_value: Any = None,
    ) -> None:
        super().__init__(probability=probability)
        assert type(min_val) is type(
            max_val
        ), f"min_val and max_val must be of the same type: {min_val}, {max_val}"
        self.is_float = isinstance(min_val, float)
        self.min = min_val
        self.max = max_val
        self.none_value = none_value
        assert self.max > self.min

    def generate(self) -> Union[float, int, Any, None]:
        if self._skip_value():
            return self.none_value
        if self.is_float:
            return random.uniform(self.min, self.max)
        return random.randrange(self.min, self.max)  # type: ignore


class DateRangeRandomizer(Randomizer):
    """
    A randomizer class that generates random dates within a specified range.

    Args:
        min_dt (date): The minimum date of the range.
        max_dt (date | int): The maximum date of the range.
            Pass an integer to specify the number of days from min_dt.
        as_js_stamp (bool, optional): If True, return the date as a JavaScript
            timestamp. Defaults to True.
        probability (float, optional): The probability of generating a value.
            Defaults to 1.0.
    Examples:
        >>> DateRangeRandomizer(date(2020, 1, 1), date(2020, 12, 31)).generate()
        datetime.date(2020, 3, 7)
        >>> DateRangeRandomizer(date(2020, 1, 1), 365).generate()
    """

    def __init__(
        self,
        min_dt: date,
        max_dt: date | int,
        *,
        as_js_stamp=True,
        probability: float = 1.0,
    ) -> None:
        super().__init__(probability=probability)
        assert isinstance(min_dt, date), f"min_dt must be a date: {min_dt}"
        assert isinstance(
            max_dt, (date, int)
        ), f"max_dt must be a date or int: {max_dt}"

        if isinstance(max_dt, int):
            self.delta_days = max_dt
            max_dt = min_dt + timedelta(days=self.delta_days)
        else:
            self.delta_days = (max_dt - min_dt).days

        assert (
            max_dt > min_dt
        ), f"max_dt must be greater than min_dt: {min_dt}, {max_dt}"

        self.min = min_dt
        self.max = max_dt
        self.as_js_stamp = as_js_stamp

    def generate(self) -> Union[date, float, None]:
        # print(self.min, self.max, self.delta_days, self.probability)
        if self._skip_value():
            return None
        res = self.min + timedelta(days=random.randrange(self.delta_days))

        if self.as_js_stamp:
            ONE_DAY_SEC = 24 * 60 * 60
            dt = datetime(res.year, res.month, res.day)
            dt_utc = dt.replace(tzinfo=timezone.utc)
            stamp_ms = (dt_utc.timestamp() + ONE_DAY_SEC) * 1000.0
            return stamp_ms
        return res


class ValueRandomizer(Randomizer):
    """
    A randomizer class that generates a fixed value with a given probability.

    Args:
        value (Any): The value to generate.
        probability (float): The probability of generating a value [0.0 .. 1.0].
    """

    def __init__(self, value: Any, *, probability: float) -> None:
        super().__init__(probability=probability)
        self.value = value

    def generate(self) -> Any:
        if self._skip_value():
            return
        return self.value


class SparseBoolRandomizer(ValueRandomizer):
    """
    A randomizer class that generates a boolean value with a given probability.
    If the value is False, it is returned as None.
    """

    def __init__(self, *, probability: float) -> None:
        super().__init__(True, probability=probability)


class SampleRandomizer(Randomizer):
    """
    A randomizer class that generates a random value from a sample list.
    """

    def __init__(
        self, sample_list: Sequence, *, counts=None, probability: float = 1.0
    ) -> None:
        super().__init__(probability=probability)
        self.sample_list = sample_list
        # TODO: remove this when support for Python 3.8 is removed
        if sys.version_info < (3, 9) and counts:  # pragma: no cover
            raise RuntimeError("counts argument requires Python 3.9 or later.")

        self.counts = counts

    def generate(self) -> Any:
        if self._skip_value():
            return
        # TODO: remove this when support for Python 3.8 is removed
        if sys.version_info < (3, 9) and not self.counts:  # pragma: no cover
            return random.sample(self.sample_list, 1)[0]
        return random.sample(self.sample_list, 1, counts=self.counts)[0]


# class BoolRandomizer(SampleRandomizer):
#     def __init__(self, *, allow_none: bool = False) -> None:
#         if allow_none:
#             super().__init__((True, False, None))
#         else:
#             super().__init__((True, False))


class TextRandomizer(Randomizer):
    """
    A randomizer class that generates a random string value from a Fabulist template.

    Uses the [`fabulist`](https://github.com/mar10/fabulist/) library to generate
    text values.

    Args:
        template (str | list): A template string or list of strings.
        probability (float, optional): The probability of generating a value.
            Defaults to 1.0.
    """

    def __init__(self, template: str | list[str], *, probability: float = 1.0) -> None:
        super().__init__(probability=probability)
        if not fab:  # pragma: no cover
            raise RuntimeError("Need fabulist installed to generate random text.")
        self.template = template

    def generate(self) -> Any:
        if self._skip_value():
            return
        return fab.get_quote(self.template)  # type: ignore[reportOptionalMemberAccess]


class BlindTextRandomizer(Randomizer):
    """
    A randomizer class that generates a random lorem ipsum text value from a template.

    Uses the [`fabulist`](https://github.com/mar10/fabulist/) library to generate
    text values.

    Args:
        sentence_count (int | tuple, optional): The number of sentences to generate.
            Defaults to (2, 6).
        dialect (str, optional): The dialect of the text. Defaults to "ipsum".
        entropy (int, optional): The entropy of the text. Defaults to 2.
        keep_first (bool, optional): If True, keep the first sentence.
            Defaults to False.
        words_per_sentence (int | tuple, optional): The number of words per sentence.
            Defaults to (3, 15).
        probability (float, optional): The probability of generating a value.
            Defaults to 1.0.
    """

    def __init__(
        self,
        *,
        sentence_count: int | tuple = (2, 6),
        dialect: str = "ipsum",
        entropy: int = 2,
        keep_first: bool = False,
        words_per_sentence: int | tuple = (3, 15),
        probability: float = 1.0,
    ) -> None:
        super().__init__(probability=probability)
        if not fab:  # pragma: no cover
            raise RuntimeError("Need fabulist installed to generate random text.")

        self.sentence_count = sentence_count
        self.dialect = dialect
        self.entropy = entropy
        self.keep_first = keep_first
        self.words_per_sentence = words_per_sentence

    def generate(self) -> Any:
        if self._skip_value():
            return
        return fab.get_lorem_paragraph(  # type: ignore[reportOptionalMemberAccess]
            sentence_count=self.sentence_count,
            dialect=self.dialect,
            entropy=self.entropy,
            keep_first=self.keep_first,
            words_per_sentence=self.words_per_sentence,
        )


def _resolve_random(val: Any) -> Any:
    if isinstance(val, Randomizer):
        return val.generate()
    return val


def _resolve_random_dict(d: dict, *, macros: dict | None = None) -> None:
    remove = []
    for key in d.keys():
        val = d[key]

        if isinstance(val, Randomizer):
            val = val.generate()
            if val is None:  # Skip due to probability
                remove.append(key)
            else:
                d[key] = val

        if macros and isinstance(val, str):
            d[key] = val.format(**macros)

    for key in remove:
        d.pop(key)
    return


# ------------------------------------------------------------------------------
# Tree Builder
# ------------------------------------------------------------------------------


def _merge_specs(node_type: str, spec: dict, types: dict) -> dict:
    res: dict = types.get("*", {}).copy()
    res.update(types.get(node_type, {}))
    res.update(spec)
    return res


def _make_tree(
    *,
    parent_node: Node,
    parent_type: str,
    types: dict,
    relations: dict,
    prefix: str,
):
    child_specs = relations[parent_type]

    for node_type, spec in child_specs.items():
        spec = _merge_specs(node_type, spec, types)
        count = spec.pop(":count", 1)
        count = _resolve_random(count) or 0
        callback = spec.pop(":callback", None)
        factory = spec.pop(":factory", DictWrapper)

        for i in range(count):
            i += 1  # 1-based
            p = f"{prefix}.{i}" if prefix else f"{i}"

            # Resolve `Randomizer` values and expand `{idx}` and `{hier_idx}` macros
            data = spec.copy()

            _resolve_random_dict(data, macros={"idx": i, "hier_idx": p})

            if callback:
                callback(data)

            node_data: Node = factory(**data)

            if isinstance(parent_node, TypedNode):
                node: Node = parent_node.add_child(node_data, kind=node_type)
            else:
                node = parent_node.add_child(node_data)

            # Generate child relations
            if node_type in relations:
                _make_tree(
                    parent_node=node,
                    parent_type=node_type,
                    types=types,
                    relations=relations,
                    prefix=p,
                )

    return


def build_random_tree(*, tree_class: type[Tree[Any, Any]], structure_def: dict) -> Tree:
    """
    Return a nutree.TypedTree with random data from a specification.
    See :ref:`randomize` for details.
    """
    structure_def = structure_def.copy()

    name = structure_def.pop("name", None)
    types = structure_def.pop("types", {})
    relations = structure_def.pop("relations")  # mandatory
    assert not structure_def, f"found extra data: {structure_def}"
    assert "__root__" in relations, "missing '__root__' relation"

    tree: Tree = tree_class(
        name=name,
        forward_attrs=True,
    )

    _make_tree(
        parent_node=tree.system_root,
        parent_type="__root__",
        types=types,
        relations=relations,
        prefix="",
    )

    return tree
