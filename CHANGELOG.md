# Changelog

## 0.6.0 (unreleased)

- Implement `Tree(..., shadow_attrs=True)`
- `tree.load(PATH)` / `tree.save(PATH)` use UTF-8 encoding.
- Support Py312

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
