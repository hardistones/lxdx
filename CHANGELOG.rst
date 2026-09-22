Changelog
=========

v0.7
****

* New ``merge_update()`` for recursive mapping updates, with optional
  positional list merging and resizing via ``recurse_lists=True``.
* New ``diff()`` for recursive mapping comparisons using original keys.
  Hidden entries are excluded; equal list runs become ``...``.
* Fix: Accept iterators and generators of key-value pairs during
  initialisation and ``update()``, and preserve identity-based keys.
* Fix: Preserve original keys with colliding normalised aliases, resolve
  constructor keyword updates through aliases, and restore aliases after deletion.
* Fix: Support ``Ellipsis`` as a key and prevent missing keys such as
  ``'items'`` from resolving to methods in item lookup, ``getx()`` and ``pop()``.
* Fix: Track metadata independently for colliding keys, allow repeated hidden
  flag assignments, and remove hidden data and metadata in ``clear()``.
* Fix: Make ``|=`` preserve the existing object's reference. Unmatched hidden
  entries remain hidden; matching visible entries on the right replace and unhide them.
* Fix: Recursively convert mappings inside tuples and plain containers in
  ``dict()`` and ``json()``, excluding nested hidden entries.
* Fix: Keep empty mappings distinct from ``None`` and handle nested
  mapping/scalar mismatches and identical ``NaN`` values in map comparisons.

v0.6
****

* Support for setting value for path with key in brackets in ``set_by_path()``

  - E.g. ``$.headers.["Content-Type"]``

* Fix: Add type checks when trying to "dictify" key-value pairs

v0.5
****

* New ``set_by_path()`` method to set value by path
* Fix: Error when keys are implicitly false, e.g. ``0``, ``False``, ``()``

v0.4
****

* Fix: must not alter data type during init
* New function

  - ``reverse()``

* More documentation
* Rename ``get()`` to ``getx()`` to not interfere with original functionality.
* Fix error when object is passed to ``copy.deepcopy()``.
* Fix consumption of iterators in ``__new__()``.

v0.3
****

* Support for Python 3.10
* Selected functions accept multiple keys as args
* Add metadata flagging to items
* Supplementary functions for metadata

  - ``keymeta()``
  - ``whats_hidden()``

* Additional methods

  - ``get_from()``

v0.2
****

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
