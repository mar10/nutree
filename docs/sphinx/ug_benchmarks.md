# Benchmarks

# Benchmark Data

> Client: arm64_16_GB, Darwin_24.1.0

| Name             | Variant                                   | Python     | Minimum time   | maxOPS    | Std Dev (σ)   |
|:-----------------|:------------------------------------------|:-----------|:---------------|:----------|:--------------|
| access node.data | node._data (attr)                         | 3.9.20     | 29 ns          | 34.911 M  | 1 ns          |
| access node.data | node._data (attr)                         | 3.10.15    | 29 ns          | 34.012 M  | 1 ns          |
| access node.data | node._data (attr)                         | 3.11.10    | 22 ns          | 44.912 M  | 0 ns          |
| access node.data | node._data (attr)                         | 3.12.6     | 9 ns           | 116.281 M | 0 ns          |
| access node.data | node._data (attr)                         | 3.13.0rc3+ | 7 ns           | 134.332 M | 0 ns          |
| access node.data | node.data (property)                      | 3.9.20     | 75 ns          | 13.334 M  | 0 ns          |
| access node.data | node.data (property)                      | 3.10.15    | 79 ns          | 12.616 M  | 0 ns          |
| access node.data | node.data (property)                      | 3.11.10    | 56 ns          | 17.833 M  | 0 ns          |
| access node.data | node.data (property)                      | 3.12.6     | 52 ns          | 19.222 M  | 0 ns          |
| access node.data | node.data (property)                      | 3.13.0rc3+ | 49 ns          | 20.374 M  | 0 ns          |
| iterate          | for _ in tree.iterator(): ...             | 3.9.20     | 2,639 ns       | 0.379 M   | 12 ns         |
| iterate          | for _ in tree.iterator(): ...             | 3.10.15    | 2,563 ns       | 0.390 M   | 6 ns          |
| iterate          | for _ in tree.iterator(): ...             | 3.11.10    | 2,138 ns       | 0.468 M   | 223 ns        |
| iterate          | for _ in tree.iterator(): ...             | 3.12.6     | 1,666 ns       | 0.600 M   | 53 ns         |
| iterate          | for _ in tree.iterator(): ...             | 3.13.0rc3+ | 1,508 ns       | 0.663 M   | 6 ns          |
| iterate          | for _ in tree.iterator(LEVEL_ORDER): ...  | 3.9.20     | 1,776 ns       | 0.563 M   | 6 ns          |
| iterate          | for _ in tree.iterator(LEVEL_ORDER): ...  | 3.10.15    | 1,908 ns       | 0.524 M   | 9 ns          |
| iterate          | for _ in tree.iterator(LEVEL_ORDER): ...  | 3.11.10    | 1,552 ns       | 0.644 M   | 4 ns          |
| iterate          | for _ in tree.iterator(LEVEL_ORDER): ...  | 3.12.6     | 1,309 ns       | 0.764 M   | 4 ns          |
| iterate          | for _ in tree.iterator(LEVEL_ORDER): ...  | 3.13.0rc3+ | 1,222 ns       | 0.818 M   | 3 ns          |
| iterate          | for _ in tree.iterator(POST_ORDER): ...   | 3.9.20     | 3,201 ns       | 0.312 M   | 7 ns          |
| iterate          | for _ in tree.iterator(POST_ORDER): ...   | 3.10.15    | 3,134 ns       | 0.319 M   | 6 ns          |
| iterate          | for _ in tree.iterator(POST_ORDER): ...   | 3.11.10    | 2,667 ns       | 0.375 M   | 10 ns         |
| iterate          | for _ in tree.iterator(POST_ORDER): ...   | 3.12.6     | 2,292 ns       | 0.436 M   | 7 ns          |
| iterate          | for _ in tree.iterator(POST_ORDER): ...   | 3.13.0rc3+ | 2,088 ns       | 0.479 M   | 87 ns         |
| iterate          | for _ in tree.iterator(PRE_ORDER): ...    | 3.9.20     | 2,696 ns       | 0.371 M   | 93 ns         |
| iterate          | for _ in tree.iterator(PRE_ORDER): ...    | 3.10.15    | 2,566 ns       | 0.390 M   | 5 ns          |
| iterate          | for _ in tree.iterator(PRE_ORDER): ...    | 3.11.10    | 2,109 ns       | 0.474 M   | 92 ns         |
| iterate          | for _ in tree.iterator(PRE_ORDER): ...    | 3.12.6     | 1,690 ns       | 0.592 M   | 47 ns         |
| iterate          | for _ in tree.iterator(PRE_ORDER): ...    | 3.13.0rc3+ | 1,498 ns       | 0.668 M   | 7 ns          |
| iterate          | for _ in tree.iterator(RANDOM_ORDER): ... | 3.9.20     | 2,561 ns       | 0.390 M   | 96 ns         |
| iterate          | for _ in tree.iterator(RANDOM_ORDER): ... | 3.10.15    | 2,556 ns       | 0.391 M   | 12 ns         |
| iterate          | for _ in tree.iterator(RANDOM_ORDER): ... | 3.11.10    | 1,766 ns       | 0.566 M   | 46 ns         |
| iterate          | for _ in tree.iterator(RANDOM_ORDER): ... | 3.12.6     | 1,825 ns       | 0.548 M   | 43 ns         |
| iterate          | for _ in tree.iterator(RANDOM_ORDER): ... | 3.13.0rc3+ | 1,728 ns       | 0.579 M   | 7 ns          |
| iterate          | for _ in tree.iterator(UNORDERED): ...    | 3.9.20     | 491 ns         | 2.035 M   | 4 ns          |
| iterate          | for _ in tree.iterator(UNORDERED): ...    | 3.10.15    | 492 ns         | 2.032 M   | 4 ns          |
| iterate          | for _ in tree.iterator(UNORDERED): ...    | 3.11.10    | 394 ns         | 2.538 M   | 0 ns          |
| iterate          | for _ in tree.iterator(UNORDERED): ...    | 3.12.6     | 398 ns         | 2.510 M   | 3 ns          |
| iterate          | for _ in tree.iterator(UNORDERED): ...    | 3.13.0rc3+ | 336 ns         | 2.977 M   | 1 ns          |
| iterate          | for _ in tree: ...                        | 3.9.20     | 2,652 ns       | 0.377 M   | 21 ns         |
| iterate          | for _ in tree: ...                        | 3.10.15    | 2,554 ns       | 0.392 M   | 233 ns        |
| iterate          | for _ in tree: ...                        | 3.11.10    | 2,157 ns       | 0.464 M   | 4 ns          |
| iterate          | for _ in tree: ...                        | 3.12.6     | 1,687 ns       | 0.593 M   | 18 ns         |
| iterate          | for _ in tree: ...                        | 3.13.0rc3+ | 1,527 ns       | 0.655 M   | 107 ns        |
| iterate          | tree.visit(lambda node, memo: None)       | 3.9.20     | 2,532 ns       | 0.395 M   | 85 ns         |
| iterate          | tree.visit(lambda node, memo: None)       | 3.10.15    | 2,595 ns       | 0.385 M   | 88 ns         |
| iterate          | tree.visit(lambda node, memo: None)       | 3.11.10    | 1,998 ns       | 0.501 M   | 7 ns          |
| iterate          | tree.visit(lambda node, memo: None)       | 3.12.6     | 1,513 ns       | 0.661 M   | 38 ns         |
| iterate          | tree.visit(lambda node, memo: None)       | 3.13.0rc3+ | 1,383 ns       | 0.723 M   | 42 ns         |
| search           | by index                                  | 3.9.20     | 516 ns         | 1.937 M   | 48 ns         |
| search           | by index                                  | 3.10.15    | 487 ns         | 2.052 M   | 31 ns         |
| search           | by index                                  | 3.11.10    | 287 ns         | 3.480 M   | 27 ns         |
| search           | by index                                  | 3.12.6     | 342 ns         | 2.922 M   | 30 ns         |
| search           | by index                                  | 3.13.0rc3+ | 348 ns         | 2.875 M   | 30 ns         |
| search           | find()                                    | 3.9.20     | 274 ns         | 3.647 M   | 1 ns          |
| search           | find()                                    | 3.10.15    | 247 ns         | 4.053 M   | 15 ns         |
| search           | find()                                    | 3.11.10    | 145 ns         | 6.912 M   | 8 ns          |
| search           | find()                                    | 3.12.6     | 151 ns         | 6.632 M   | 8 ns          |
| search           | find()                                    | 3.13.0rc3+ | 148 ns         | 6.766 M   | 7 ns          |
| search           | find_all()                                | 3.9.20     | 267 ns         | 3.748 M   | 10 ns         |
| search           | find_all()                                | 3.10.15    | 240 ns         | 4.160 M   | 12 ns         |
| search           | find_all()                                | 3.11.10    | 141 ns         | 7.104 M   | 5 ns          |
| search           | find_all()                                | 3.12.6     | 156 ns         | 6.392 M   | 5 ns          |
| search           | find_all()                                | 3.13.0rc3+ | 148 ns         | 6.768 M   | 6 ns          |
| serialize_load   | ZIP_BZIP2 ('.bz2')                        | 3.9.20     | 240 ms         | 4.168     | 0 ms          |
| serialize_load   | ZIP_BZIP2 ('.bz2')                        | 3.10.15    | 208 ms         | 4.808     | 0 ms          |
| serialize_load   | ZIP_BZIP2 ('.bz2')                        | 3.11.10    | 163 ms         | 6.129     | 0 ms          |
| serialize_load   | ZIP_BZIP2 ('.bz2')                        | 3.12.6     | 165 ms         | 6.055     | 0 ms          |
| serialize_load   | ZIP_BZIP2 ('.bz2')                        | 3.13.0rc3+ | 175 ms         | 5.722     | 0 ms          |
| serialize_load   | ZIP_DEFLATED ('.zip')                     | 3.9.20     | 209 ms         | 4.785     | 0 ms          |
| serialize_load   | ZIP_DEFLATED ('.zip')                     | 3.10.15    | 210 ms         | 4.770     | 0 ms          |
| serialize_load   | ZIP_DEFLATED ('.zip')                     | 3.11.10    | 148 ms         | 6.756     | 0 ms          |
| serialize_load   | ZIP_DEFLATED ('.zip')                     | 3.12.6     | 164 ms         | 6.102     | 0 ms          |
| serialize_load   | ZIP_DEFLATED ('.zip')                     | 3.13.0rc3+ | 159 ms         | 6.294     | 0 ms          |
| serialize_load   | ZIP_LZMA ('.lzma')                        | 3.9.20     | 204 ms         | 4.907     | 0 ms          |
| serialize_load   | ZIP_LZMA ('.lzma')                        | 3.10.15    | 208 ms         | 4.805     | 0 ms          |
| serialize_load   | ZIP_LZMA ('.lzma')                        | 3.11.10    | 162 ms         | 6.187     | 0 ms          |
| serialize_load   | ZIP_LZMA ('.lzma')                        | 3.12.6     | 167 ms         | 5.975     | 0 ms          |
| serialize_load   | ZIP_LZMA ('.lzma')                        | 3.13.0rc3+ | 156 ms         | 6.424     | 0 ms          |
| serialize_load   | uncompressed ('.json')                    | 3.9.20     | 203 ms         | 4.926     | 0 ms          |
| serialize_load   | uncompressed ('.json')                    | 3.10.15    | 200 ms         | 4.990     | 0 ms          |
| serialize_load   | uncompressed ('.json')                    | 3.11.10    | 145 ms         | 6.902     | 0 ms          |
| serialize_load   | uncompressed ('.json')                    | 3.12.6     | 171 ms         | 5.848     | 0 ms          |
| serialize_load   | uncompressed ('.json')                    | 3.13.0rc3+ | 149 ms         | 6.709     | 0 ms          |
| serialize_save   | ZIP_BZIP2 ('.bz2')                        | 3.9.20     | 353 ms         | 2.835     | 0 ms          |
| serialize_save   | ZIP_BZIP2 ('.bz2')                        | 3.10.15    | 378 ms         | 2.649     | 0 ms          |
| serialize_save   | ZIP_BZIP2 ('.bz2')                        | 3.11.10    | 320 ms         | 3.125     | 0 ms          |
| serialize_save   | ZIP_BZIP2 ('.bz2')                        | 3.12.6     | 325 ms         | 3.081     | 0 ms          |
| serialize_save   | ZIP_BZIP2 ('.bz2')                        | 3.13.0rc3+ | 281 ms         | 3.558     | 0 ms          |
| serialize_save   | ZIP_DEFLATED ('.zip')                     | 3.9.20     | 333 ms         | 3.000     | 0 ms          |
| serialize_save   | ZIP_DEFLATED ('.zip')                     | 3.10.15    | 344 ms         | 2.907     | 0 ms          |
| serialize_save   | ZIP_DEFLATED ('.zip')                     | 3.11.10    | 286 ms         | 3.498     | 0 ms          |
| serialize_save   | ZIP_DEFLATED ('.zip')                     | 3.12.6     | 268 ms         | 3.738     | 0 ms          |
| serialize_save   | ZIP_DEFLATED ('.zip')                     | 3.13.0rc3+ | 244 ms         | 4.091     | 0 ms          |
| serialize_save   | ZIP_LZMA ('.lzma')                        | 3.9.20     | 626 ms         | 1.597     | 0 ms          |
| serialize_save   | ZIP_LZMA ('.lzma')                        | 3.10.15    | 660 ms         | 1.515     | 0 ms          |
| serialize_save   | ZIP_LZMA ('.lzma')                        | 3.11.10    | 593 ms         | 1.685     | 0 ms          |
| serialize_save   | ZIP_LZMA ('.lzma')                        | 3.12.6     | 566 ms         | 1.766     | 0 ms          |
| serialize_save   | ZIP_LZMA ('.lzma')                        | 3.13.0rc3+ | 568 ms         | 1.762     | 0 ms          |
| serialize_save   | uncompressed ('.json')                    | 3.9.20     | 293 ms         | 3.410     | 0 ms          |
| serialize_save   | uncompressed ('.json')                    | 3.10.15    | 305 ms         | 3.274     | 0 ms          |
| serialize_save   | uncompressed ('.json')                    | 3.11.10    | 272 ms         | 3.671     | 0 ms          |
| serialize_save   | uncompressed ('.json')                    | 3.12.6     | 230 ms         | 4.352     | 0 ms          |
| serialize_save   | uncompressed ('.json')                    | 3.13.0rc3+ | 215 ms         | 4.660     | 0 ms          |

Benchmark date: 2024-12-27T21:32:29.559992+00:00
Fixed dataset values: client='61bdee7c56e0e5f7', debug_mode=False, hardware='arm64_16_GB', project='nutree', system='Darwin_24.1.0', tag='latest', version='0.11.2a1'.
Variant dataset values: name, python, sample_size, variant.
Showing 105 rows.
Sort order: name, variant, python.


## Ops by python

> Client: arm64_16_GB, Darwin_24.1.0

| Name             | Variant                                   | 3.9.20   | 3.10.15   | 3.11.10   | 3.12.6    | 3.13.0rc3+   |
|:-----------------|:------------------------------------------|:---------|:----------|:----------|:----------|:-------------|
| access node.data | node._data (attr)                         | 34.911 M | 34.012 M  | 44.912 M  | 116.281 M | 134.332 M    |
| access node.data | node.data (property)                      | 13.334 M | 12.616 M  | 17.833 M  | 19.222 M  | 20.374 M     |
| iterate          | for _ in tree: ...                        | 0.377 M  | 0.392 M   | 0.464 M   | 0.593 M   | 0.655 M      |
| iterate          | for _ in tree.iterator(UNORDERED): ...    | 2.035 M  | 2.032 M   | 2.538 M   | 2.510 M   | 2.977 M      |
| iterate          | for _ in tree.iterator(POST_ORDER): ...   | 0.312 M  | 0.319 M   | 0.375 M   | 0.436 M   | 0.479 M      |
| iterate          | for _ in tree.iterator(RANDOM_ORDER): ... | 0.390 M  | 0.391 M   | 0.566 M   | 0.548 M   | 0.579 M      |
| iterate          | tree.visit(lambda node, memo: None)       | 0.395 M  | 0.385 M   | 0.501 M   | 0.661 M   | 0.723 M      |
| iterate          | for _ in tree.iterator(LEVEL_ORDER): ...  | 0.563 M  | 0.524 M   | 0.644 M   | 0.764 M   | 0.818 M      |
| iterate          | for _ in tree.iterator(PRE_ORDER): ...    | 0.371 M  | 0.390 M   | 0.474 M   | 0.592 M   | 0.668 M      |
| iterate          | for _ in tree.iterator(): ...             | 0.379 M  | 0.390 M   | 0.468 M   | 0.600 M   | 0.663 M      |
| search           | find_all()                                | 3.748 M  | 4.160 M   | 7.104 M   | 6.392 M   | 6.768 M      |
| search           | find()                                    | 3.647 M  | 4.053 M   | 6.912 M   | 6.632 M   | 6.766 M      |
| search           | by index                                  | 1.937 M  | 2.052 M   | 3.480 M   | 2.922 M   | 2.875 M      |
| serialize_load   | ZIP_LZMA ('.lzma')                        | 4.907    | 4.805     | 6.187     | 5.975     | 6.424        |
| serialize_load   | uncompressed ('.json')                    | 4.926    | 4.990     | 6.902     | 5.848     | 6.709        |
| serialize_load   | ZIP_DEFLATED ('.zip')                     | 4.785    | 4.770     | 6.756     | 6.102     | 6.294        |
| serialize_load   | ZIP_BZIP2 ('.bz2')                        | 4.168    | 4.808     | 6.129     | 6.055     | 5.722        |
| serialize_save   | ZIP_BZIP2 ('.bz2')                        | 2.835    | 2.649     | 3.125     | 3.081     | 3.558        |
| serialize_save   | ZIP_DEFLATED ('.zip')                     | 3.000    | 2.907     | 3.498     | 3.738     | 4.091        |
| serialize_save   | uncompressed ('.json')                    | 3.410    | 3.274     | 3.671     | 4.352     | 4.660        |
| serialize_save   | ZIP_LZMA ('.lzma')                        | 1.597    | 1.515     | 1.685     | 1.766     | 1.762        |

Benchmark date: 2024-12-27T21:32:29.559992+00:00
Fixed dataset values: client='61bdee7c56e0e5f7', debug_mode=False, hardware='arm64_16_GB', project='nutree', system='Darwin_24.1.0', tag='latest', version='0.11.2a1'.
Variant dataset values: name, python, sample_size, variant.
: Showing 21 of 105 rows.
Sort order: name.



