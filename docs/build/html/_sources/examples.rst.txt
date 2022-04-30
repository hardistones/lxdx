Examples
========

Listed here are some of the few operations ``Dixt`` can do.

.. tip::
    A great resource for ``Dixt``'s functions and operations is maybe its `unit test`_.

.. _unit test: https://github.com/hardistones/lxdx/blob/dev/tests/test_dixt.py

Initialisation
**************
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
*******
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
******************************
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


Notable Dixt methods
********************

:py:meth:`contains(*keys, assert_all=True) <lxdx.Dixt.contains>`

This is a convenience method to evaluate multiple keys at once. This has the
same effect if the ``in`` operator is used multiple times.

.. note::
    Non-normalised keys are only accepted to preserve the behaviour of the
    operator ``in``, as is used in mappings and sequences.

|

:py:meth:`get(*attrs, default=None) <lxdx.Dixt.get>`

This method, unlike in ``dict``, supports multiple arguments. The `attrs`
argument can accept normalised or non-normalised keys.

The other difference from the usual usage of this method in ``dict`` is that,
the keyword argument `default` should be always specified when putting
default values other than ``None``, or else, all the arguments will be treated
as `attrs`.

.. seealso::
    :py:meth:`setdefault(key, default=None) <lxdx.Dixt.setdefault>`

|

:py:meth:`get_from(path) <lxdx.Dixt.get_from>`

For further programmability, an item can be accessed by a 'stringified'
path to the key, formatted as

.. code-block::

    $.<key>.{series-of-keys}.<target-key>

where ``$`` is a required placeholder. The keys must be specified as normalised.

.. code-block:: python

    assert dx.get_from('$.group.name') == dx.group.name
    assert dx.group.get_from('$.name') == dx.group.name

    dx.get_from('$.some_list[1].key_from_dixt_object_inside_some_list')

|

:py:meth:`is_submap_of(other) <lxdx.Dixt.is_submap_of>`

:py:meth:`is_supermap_of(other) <lxdx.Dixt.is_supermap_of>`

These two complementary methods act the same as subset and superset in ``set``.
The items are strictly evaluated between compared objects, with the calling
object as basis/reference when calling ``is_submap_of()``; and the `other` object
as basis when calling ``is_supermap_of()``.

.. code-block:: python

    months = ['Jan', 'Feb', 'Mar']
    week = ['Mon', 'Tue', 'Wed']
    cal = {'months': months, 'week': week}

    dxc, dxm, dxw = Dixt(cal), Dixt(months=months), {'week': week}

    assert dxm.is_submap_of(dxc)
    assert dxc.is_supermap_of(dxw)

    # both lists must be equal
    assert dxc.is_supermap_of(Dixt(week=['Mon'])) == False

|

:py:meth:`from_json(json_str) <lxdx.Dixt.from_json>`

:py:meth:`json() <lxdx.Dixt.json>`

These methods are included to ease up conversion from and to JSON string.

.. code-block:: python

    json_str = '{"a": "JSON string"}'
    assert Dixt.from_json(json_str).json() == json_str
