Examples
========

Listed here are some of the few operations ``Dixt`` can do.

.. note::
    A great resource for ``Dixt``'s functions and operations is maybe its `unit test`__.

.. __: https://github.com/hardistones/lxdx/blob/dev/tests/test_dixt.py

Initialisation
--------------
.. code-block:: python

    from lxdx import Dixt

    # an empty Dixt object is equal to an empty dict
    dx = Dixt()
    assert dx == {}

    # allows for dictionaries with keys not strings
    dic = {1: 1, 'alpha': 'α'}
    dx = Dixt(d)
    assert dx == dic

    # or Dixt(dic), whichever you prefer
    dic = {'alpha': 'α', 'beta': 'β'}
    dx = Dixt(**dic)
    assert dx == dic

    # updates beta
    dx = Dixt(dic, beta='B')
    assert dx == {'alpha': 'α', 'beta': 'B'}

    # or initialise with another Dixt object
    ex = Dixt(dx)
    assert ex == dx

Merging
-------
Starting with Python 3.9, two ``dict``\s can be merged using the ``|`` operator,
which ``Dixt`` also supports. The right side of the operator will update
the left side, if any of the first layer keys are the same.

.. code-block:: python

    dx = Dixt({'alpha': 'α', 'beta': 'β'})
    ex = dx | {'gamma': 'γ'}
    assert ex == {'alpha': 'α', 'beta': 'β', 'gamma': 'γ'}
    assert isinstance(ex, Dixt)

.. note::
    Only when a ``Dixt`` object is at the left of the operator will
    the resulting object a ``Dixt`` object, otherwise ``dict``.


Getting and setting attributes
------------------------------
`Attributes` in a ``Dixt`` object are just items' normalised keys.
See the :ref:`dixt-class-label` reference for more info.

.. code-block:: python

    # a nested/hierarchical data
    data = {
        'Accept-Encoding': 'gzip',
        'metadata': {'Content-Type': 'application/json'},
        'Product Name': 'Data Blue',
        ...
    }

    dx = Dixt(data)
    assert dx.accept_encoding == dx['Accept-Encoding'] == 'gzip'
    assert dx.product_name == dx['Product Name'] == 'Data Blue'

    dx.metadata.content_type = 'application/xml'
    assert dx.metadata.content_type == dx['metadata']['Content-Type'] == 'application/xml'

    # depending on the original key,
    # this could be equivalent to dx['product-list']['names'][-2:]
    dx.product_list.names[-2:]

When adding new items by 'setting attributes' using the dot notation, keys are taken verbatim:

.. code-block:: python

    # should be the same as dx['something_new'] = 'new-value'
    dx.something_new = 'new-value'
    assert 'something_new' in dx
    assert 'Something-New' not in dx

Auto conversion of ``dict`` to a ``Dixt`` object is also possible when adding new items.

.. code-block:: python

    dx.existing = {...}
    dx.new_attrib = {...}

    # or

    dx['existing'] = {...}
    dx['new_attrib'] = {...}

.. caution::
    When inserting or appending ``dict`` objects in ``list``\s,
    if the desired object should be a ``Dixt`` object,
    initialise it first as a ``Dixt`` object, like so:

    .. code-block:: python

        dx.this_is_a_list.append(Dixt({...}))
        dx.this_is_a_list[2] = Dixt({...})

    The assignment is handled by ``list``, and ``Dixt`` can do nothing about it.

Aside from the usual deletion of items in a ``dict``, deleting items `attribute` style
is also handled.

.. code-block:: python

    del dx['something']['inside-one']
    del dx.something.inside_two
    assert 'inside_two' not in dx.something


Dixt methods
------------

:py:meth:`contains() <lxdx.Dixt.contains>`

WIP

|

:py:meth:`get_from() <lxdx.Dixt.get_from>`

WIP

|

:py:meth:`is_submap_of() <lxdx.Dixt.is_submap_of>`

:py:meth:`is_supermap_of() <lxdx.Dixt.is_supermap_of>`

WIP

|

:py:meth:`from_json() <lxdx.Dixt.from_json>`

:py:meth:`json() <lxdx.Dixt.json>`

Conversion from and to JSON string.

.. code-block:: python

    json_str = '{"a": "JSON string"}'
    assert Dixt.from_json(json_str).json() == json_str
