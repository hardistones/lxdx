Changelog
=========

v0.5.0
******

* New `set_by_path()` method to set value by path

v0.4.0
******

* Fix: must not alter data type during init
* New function
    - ``reverse()``
* More documentation
* Rename ``get()`` to ``getx()`` to not interfere with original functionality.
* Fix error when object is passed to ``copy.deepcopy()``.
* Fix consumption of iterators in ``__new__()``.

v0.3.0
******

* Support for Python 3.10
* Selected functions accept multiple keys as args
* Add metadata flagging to items
* Supplementary functions for metadata
   - ``keymeta()``
   - ``whats_hidden()``
* Additional methods
    - ``get_from()``

v0.2.1
******

* Normalisation of keys
* Dot notation accessibility due to keys normalisation
* Supporting the union operator (``|``) for ``dict``, (PEP-584_)
* Additional methods
    - ``is_submap_of()``
    - ``is_supermap_of()``
    - ``dict()``
    - ``from_json()``
    - ``json()``


.. references
.. _PEP-584: https://www.python.org/dev/peps/pep-0584
