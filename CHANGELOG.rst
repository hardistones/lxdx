Changelog
=========

v1.0.0
------

* Normalisation of keys
* Dot notation accessibility due to keys normalisation
* Selected functions accept multiple keys as args
* Add metadata flagging to items with supplementary methods
    - ``keymeta()``
    - ``hidden()``

* Supporting the union operator (``|``) for `dict`, (PEP-584_)
* Additional methods
    - ``contains()``
    - ``is_submap_of()``
    - ``is_supermap_of()``
    - ``dict()``
    - ``from_json()``
    - ``json()``
    - ``get_from()``


.. references
.. _PEP-584: https://www.python.org/dev/peps/pep-0584
