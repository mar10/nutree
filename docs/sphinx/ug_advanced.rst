--------
Advanced
--------

..
    Events
    ------

    (Not Yet Implemented.)

    ::

        def on_change(tree, event):
            assert event.type == "change"

        tree.on("change", on_change)


Locking
-------

In multithreading scenarios, we can enforce critical sections like so::

    with tree:
        snapshot = tree.to_dict()
