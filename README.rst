lxdx
====

``lxdx`` is an "extended" Python ``dict`` with attribute-like accessibility.
Other than the usual ``dict`` operations, functions and methods,
some useful functions are incorporated as well.

Only supports Python 3.9+, due to the usage of the `union operator`__ for ``dict``.

Why this project?
-----------------
* Hobbies and curiosities. Just for the fun of programming.
* ``dataclass`` is not cut for modelling hierarchical data.
* Brackets when accessing multi-layer data is too many. `Dot notation`__ may be a cleaner way.
* Introduce utility functions like ``get_from(path)``, inspired from `JsonPath`__, for programmability.

Installation
------------
``lxdx`` is available in `PyPI <https://pypi.org/project/lxdx>`_, and installable via ``pip``:

.. code-block::

    pip install lxdx


Examples
--------
.. code-block:: python

    from lxdx import Dixt

    assert Dixt() == {}
    assert Dixt({1: 1, 'alpha': 'α'}) == {1: 1, 'alpha': 'α'}
    assert Dixt(alpha='α', beta='β') == {'alpha': 'α', 'beta': 'β'}
    assert Dixt(alpha='α', beta='β').is_supermap_of({'beta': 'β'})

    # data can be deeply nested
    data = {'Accept-Encoding': 'gzip', 'metadata': {'Content-Type': 'application/json'}}
    dx = Dixt(**data)

    # update dx using the union operator
    dx |= {'other': 'dict or Dixt obj'}

    # 'Normalise' the keys to use it as attributes additionally.
    assert dx['Accept-Encoding'] == dx.accept_encoding
    del dx.accept_encoding
    print(dx.metadata.CONTENT_TYPE)

    # Instead of
    dx['a-list'][1]['obj-attr'] = 'value'

    # Is way cleaner
    dx.a_list[1].obj_attr = 'value'

    # Programmatically get values
    assert dx.a_list[1:7].obj_attr == dx.get_from('$.a_list[1:7].obj_attr')

    json_str = '{"a": "JSON string"}'
    assert Dixt.from_json(json_str).json() == json_str

Documentation
-------------
Full documentation is at https://hardistones.github.io/lxdx.

Future
------
``lxdx`` is supposed to be a library of "extended" ``list`` and ``dict``. For now there's no use case for the ``list`` extension.

License
-------
This project and all its files are licensed under the 3-Clause BSD License.

    .. include:: LICENSE


.. References
.. __: https://www.python.org/dev/peps/pep-0584
.. __: https://en.wikipedia.org/wiki/Property_(programming)#Dot_notation
.. __: https://github.com/json-path/JsonPath
