.. _main-index:

######
nutree
######

|pypi_badge| |nbsp| |gha_badge| |nbsp| |coverage_badge| |nbsp| |lic_badge| 
|nbsp| |rtd_badge| |nbsp| |so_badge|

*A Python library for tree data structures with an intuitive, yet powerful, API.*

:Project:   https://github.com/mar10/nutree/
:Version:   |version|, Date: |today|


.. toctree::
   :hidden:

   Overview<self>
   installation
   take_the_tour
   user_guide
   reference_guide
   development
   changes


::

   $ pip install nutree

**Note:** Run ``pip install "nutree[graph]"`` or ``pip install "nutree[all]"`` 
instead, in order to install additional graph support.

.. ::

..    from nutree import Tree, Node

..    tree = Tree("Store")

..    n = tree.add("Records")

..    n.add("Let It Be")
..    n.add("Get Yer Ya-Ya's Out!")

..    n = tree.add("Books")
..    n.add("The Little Prince")

..    tree.print()

.. ::

..    Tree<'Store'>
..    ├─── 'Records'
..    │    ├─── 'Let It Be'
..    │    ╰─── "Get Yer Ya-Ya's Out!"
..    ╰─── 'Books'
..         ╰─── 'The Little Prince'


.. Tree nodes wrap the data and also expose methods for navigation, searching,
.. iteration, ... ::

..    records_node = tree["Records"]

..    assert isinstance(records_node, Node)
..    assert records_node.name == "Records"

..    print(records_node.first_child())

.. ::

..    Node<'Let It Be', data_id=510268653885439170>

.. Nodes may be strings or arbitrary objects::

..    alice = Person("Alice", age=23, guid="{123-456}")
..    tree.add(alice)

..    # Lookup nodes by object, data_id, name pattern, ...
..    alice_node = tree[alice]
..    assert isinstance(alice_node.data, Person)
..    assert alice_node.data is alice

..    del tree[alice]


Nutree Facts
============

  * :ref:`Handle multiple references of single objects ('clones') <clones>`
  * :ref:`Search by name pattern, id, or object reference <searching>`
  * :ref:`Unobtrusive handling of arbitrary objects <objects>`
  * :ref:`Compare two trees and calculate patches <diff-and-merge>`
  * :ref:`Save as DOT file and graphwiz diagram <save-dot>`
  * :ref:`Nodes can be plain strings or objects <objects>`
  * :ref:`(De)Serialize to (compressed) JSON <serialize>`
  * :ref:`Save as Mermaid flow diagram <save-mermaid>`
  * :ref:`Different traversal methods <traversal>`
  * :ref:`Generate random trees <randomize>`
  * :ref:`Convert to RDF graph <save-rdf>`
  * :ref:`Fully type annotated <api-reference>`
  * :ref:`Typed child nodes <typed-tree>`
  * :ref:`Pretty print <pretty-print>`
  * :ref:`Navigation <navigate>`
  * :ref:`Filtering <mutation>`



Now read about :doc:`installation` and :doc:`take_the_tour` ...



.. |gha_badge| image:: https://github.com/mar10/nutree/actions/workflows/tests.yml/badge.svg
   :alt: Build Status
   :target: https://github.com/mar10/nutree/actions/workflows/tests.yml

.. |pypi_badge| image:: https://img.shields.io/pypi/v/nutree.svg
   :alt: PyPI Version
   :target: https://pypi.python.org/pypi/nutree/

.. |lic_badge| image:: https://img.shields.io/pypi/l/nutree.svg
   :alt: License
   :target: https://github.com/mar10/nutree/blob/main/LICENSE.txt

.. |rtd_badge| image:: https://readthedocs.org/projects/nutree/badge/?version=latest
   :target: https://nutree.readthedocs.io/
   :alt: Documentation Status

.. |coverage_badge| image:: https://codecov.io/github/mar10/nutree/branch/main/graph/badge.svg?token=9xmAFm8Icl
   :target: https://codecov.io/github/mar10/nutree
   :alt: Coverage Status

.. .. |black_badge| image:: https://img.shields.io/badge/code%20style-black-000000.svg
..    :target: https://github.com/ambv/black
..    :alt: Code style: black

.. |so_badge| image:: https://img.shields.io/badge/StackOverflow-nutree-blue.svg
   :target: https://stackoverflow.com/questions/tagged/nutree
   :alt: StackOverflow: nutree

.. |logo| image:: ../nutree_48x48.png
   :height: 48px
   :width: 48px
   :alt: nutree

.. |nutree| raw:: html

   <a href="https://en.wikipedia.org/wiki/Stressor"><abbr title="A nutree is a chemical or biological agent, environmental condition, external stimulus or an event that causes stress to an organism.">nutree</abbr></a>
