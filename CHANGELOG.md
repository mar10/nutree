# Changelog

## 1.0.1 (unreleased)

## 1.0.0 (2024-12-27)
- Add benchmarks (using [Benchman](https://github.com/mar10/benchman)).
- Drop support for Python 3.8

## 0.11.1 (2024-11-08)
- `t0.diff(t1, ...)` adds nodes from t1 when possible, so the new status is 
  used for modified nodes. 
- `t0.diff(t1, ...)` marks both, source and target nodes, as modified if 
  applicable.

## 0.11.0 (2024-11-07)
- Implement check for node modifications in `tree.diff(..., compare=True)`.
- `DictWrapper` supports comparision with `==`.

## 0.10.0 (2024-11-06)

- BREAKING:
  - `kind` parameter is now mandatory for `add()` and related methods.
    `kind=None` is still allowed to use the default (inherit or 'child').
  - Rename `shadow_attrs` argument to `forward_attrs`.
  - Enforce that the same object instance is not added multiple times to one parent.
  - Rename `GenericNodeData` to `DictWrapper` and remove support for attribut access.
  - Drop support for Python 3.8
  - mermaid: change mapper signatures and defaults
- tree.to_rdf() is now available for Tree (not only TypedTree).
- New method `node.up()` allows method chaining when adding nodes.
- Pass pyright 'typeCheckingMode = "standard"'.
- Use generic typing for improved type checking, e.g. use `tree = Tree[Animals]()`
  to create a type-aware container.

## 0.9.0 (2024-09-12)

- Add `Tree.build_random_tree()` (experimental).
- Add `GenericNodeData` as wrapper for `dict` data.
- Fixed #7 Tree.from_dict failing to recreate an arbitrary object tree with a mapper.

## 0.8.0 (2024-03-29)

- BREAKING: Drop Python 3.7 support (EoL 2023-06-27).
- `Tree.save()` accepts a `compression` argument that will enable compression.
  `Tree.load()` can detect if the input file has a compression header and will
  decompress transparently.
- New traversal methods `LEVEL_ORDER`, `LEVEL_ORDER_RTL`, `ZIGZAG`, `ZIGZAG_RTL`.
- New compact connector styles `'lines32c'`, `'round43c'`, ...
- Save as mermaid flow diagram.

## 0.7.1 (2023-11-08)

- Support compact serialization forrmat using `key_map` and `value_map`.
- Better support for working with derived classes (overload methods instead of
  callbacks).
- Fix invalid UniqueConstraint error message when loading a TypedTree.
- Add optional `tree.print(..., file=IO)` argument.
- Rename `default_connector_style` to `DEFAULT_CONNECTOR_STYLE`

## 0.6.0 (2023-11-01)

- Implement `Tree(..., shadow_attrs=True)`.
- `tree.load(PATH)` / `tree.save(PATH)` use UTF-8 encoding.
- Add `Tree.system_root` as alias for `Tree._root`.
- Add `Tree.get_toplevel_nodes()` as alias for `tree.children.`
- Support and test with Py3.12: don't forget to update pip, pipenv, and tox.
- Deprecate Python 3.7 support (EoL 2023-06-27).

## 0.5.1 (2023-05-29)

- BREAKING: renamed `tree.to_dict()` to `tree.to_dict_list()`.
- BREAKING: changed `tree.load()` / `tree.save()` storage format.
- `tree.load()` / `tree.save()` accept path in addition to file objects.

## 0.5.0 (2023-05-28)

- BREAKING: changed `tree.load()` / `tree.save()` signature, and storage format.
- Support load/save for TypedTree

## 0.4.0 (2023-02-22)

- BREAKING: Rename `node.move()` -> `node.move_to()`
- New `tree.copy_to()` and `node.copy_to()`
- New `tree.children` property
- Configurable default connector style

## 0.3.0 (2022-08-01 and before)

Initial releases.
