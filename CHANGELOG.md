# Changelog

## 0.7.0 (unreleased)

- Support compact serialization forrmat using `key_map` and `value_map`.
- Better support for working with derived classes (overload methods instead of
  callbacks).
- Fix invalid UniqueConstraint error message when loading a TypedTree.
- Add optional `tree.print(..., file=IO)` argument.
- Rename `default_connector_style` to `DEFAULT_CONNECTOR_STYLE`

## 0.6.0 (2023-11-01)

- Implement `Tree(..., shadow_attrs=True)`
- `tree.load(PATH)` / `tree.save(PATH)` use UTF-8 encoding.
- Add `Tree.system_root` as alias for `Tree._root`
- Add `Tree.get_toplevel_nodes()` as alias for `tree.children.`
- Support and test with Py3.12: don't forget to update pip, pipenv, and tox.

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
