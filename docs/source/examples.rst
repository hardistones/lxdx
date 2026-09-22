Examples
========

Listed here are some of the few operations ``Dixt`` can do.

.. tip::
    A great resource for ``Dixt``'s functions and operations is maybe its `unit test`_.

Initialisation
**************
.. code-block:: python

    from lxdx import Dixt

    # an empty Dixt object is equal to an empty dict
    dx = Dixt()
    assert dx == {}

    # allows for dictionaries with keys not strings
    dic = {1: 1, 'alpha': 'α'}
    dx = Dixt(dic)
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

``Dixt`` also accepts iterables of key-value pairs, including iterators.

.. code-block:: python

    alpha, omega = [1, 'a'], [9, 'z']
    assert Dixt(zip(alpha, omega)) == {1: 9, 'a': 'z'}

Constructing from another ``Dixt`` copies its visible top-level entries,
without their metadata. Nested ``Dixt`` values may still be shared.


Merging
*******
Starting with Python 3.9, two ``dict``\s can be merged using the ``|`` operator,
which ``Dixt`` also supports. ``|`` creates a new mapping; matching original
keys take their values from the right operand. Nested mappings are replaced,
not merged. ``|=`` updates the existing object in place.

.. code-block:: python

    dx = Dixt({'alpha': 'α', 'beta': 'β'})
    ex = dx | {'gamma': 'γ'}
    assert ex == {'alpha': 'α', 'beta': 'β', 'gamma': 'γ'}
    assert isinstance(ex, Dixt)

    dx |= {'beta': 'B'}
    assert dx == {'alpha': 'α', 'beta': 'B'}

.. important::
    ``Dixt | dict`` returns a ``Dixt``; ``dict | Dixt`` returns a ``dict``.
    Hidden entries are excluded from ``|``. For ``|=`` visibility rules,
    see :doc:`metadata`.

Use :py:meth:`merge_update() <lxdx.Dixt.merge_update>` to merge nested mappings
in place. Lists are replaced by default. With ``recurse_lists=True``, list
items are merged by position and the list is resized to the incoming length.

.. code-block:: python

    dx = Dixt(settings={'colour': 'blue', 'size': 2})
    dx.merge_update({'settings': {'size': 3}})
    assert dx.settings == {'colour': 'blue', 'size': 3}

    dx = Dixt(rows=[{'name': 'A', 'count': 1}, {'name': 'B'}])
    dx.merge_update({'rows': [{'count': 2}]}, recurse_lists=True)
    assert dx.rows == [{'name': 'A', 'count': 2}]


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
        'some-list': [{}, {}, {'some-key': 'old value'}],
        'Product-List': {'names': ['Red', 'Green', 'Blue']},
    }

    dx = Dixt(data)
    assert dx.accept_encoding == dx['Accept-Encoding'] == 'gzip'
    assert dx.product_name == dx['Product Name'] == 'Data Blue'

    dx.metadata.content_type = 'application/xml'
    assert dx.metadata.content_type == dx['metadata']['Content-Type'] == 'application/xml'

    # setting items to a Dixt object inside of a list
    dx.some_list[2].some_key = 'new value'
    assert dx.some_list[2]['some-key'] == 'new value'
    assert 'some_key' not in dx.some_list[2]

    # depending on the original key,
    # this could be equivalent to dx['product-list']['names'][-2:]
    # or dx['Product-List']['names'][-2:]
    dx.product_list.names[-2:]

Attribute assignment updates the original key through its normalised alias.
Bracket assignment to an existing item requires the original key; using a
different spelling of its alias raises ``KeyError``. Use brackets for keys
that collide with method names, such as ``dx['items']``.

When adding new items by 'setting attributes' using the dot notation, keys are taken verbatim:

.. code-block:: python

    # should be the same as dx['something_new'] = 'new-value'
    dx.something_new = 'new-value'
    assert 'something_new' in dx
    assert 'Something-New' not in dx

Auto conversion of ``dict`` to a ``Dixt`` object is also possible when adding new items.

.. code-block:: python

    dx.existing = {'name': 'A'}
    dx.new_attrib = {'name': 'B'}

    # or

    dx['existing'] = {'name': 'A'}
    dx['new_attrib'] = {'name': 'B'}
    assert dx.new_attrib.name == 'B'

.. caution::
    When inserting or appending ``dict`` objects in ``list``\s,
    if the desired object should be a ``Dixt`` object,
    initialise it first as a ``Dixt`` object, like so:

    .. code-block:: python

        dx.some_list.append(Dixt(name='C'))
        dx.some_list[2] = Dixt(name='D')

    The assignment is handled by ``list``, and ``Dixt`` can do nothing about it.

Aside from the usual deletion of items in a ``dict``, deleting items `attribute` style
is also handled.

.. code-block:: python

    dx.something = {'inside-one': 1, 'inside_two': 2}
    del dx['something']['inside-one']
    del dx.something.inside_two
    assert 'inside_two' not in dx.something


Notable Dixt methods
********************

:py:meth:`contains(*keys, assert_all=True) <lxdx.Dixt.contains>`

This is a convenience method to evaluate multiple keys at once. This has the
same effect if the ``in`` operator is used multiple times.
``assert_all=False`` returns one boolean per key instead of a single result.

.. code-block:: python

    dx = Dixt({'Product Name': 'Blue'})
    assert dx.contains('Product Name')
    assert dx.contains('Product Name', 'missing', assert_all=False) == (True, False)

.. note::
    Only original keys are accepted to preserve the behaviour of the
    operator ``in``, as is used in mappings and sequences.

|

:py:meth:`getx(*attrs, default=None) <lxdx.Dixt.getx>`

Get one value, or a tuple of values for multiple original or normalised keys.
Pass ``default`` by keyword: a scalar replaces every missing value; a list or
tuple supplies one default per requested key and must have the same length.
The inherited ``get(key, default=None)`` still retrieves a single value.

.. code-block:: python

    dx = Dixt({'Product Name': 'Blue'})
    assert dx.getx('product_name') == 'Blue'
    assert dx.getx('product_name', 'count', default=None) == ('Blue', None)
    assert dx.getx('count', 'colour', default=(0, 'red')) == (0, 'red')
    assert dx.get('missing', 'fallback') == 'fallback'

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

    dx = Dixt(group={'name': 'A'}, some_list=[{'name': 'B'}])
    assert dx.get_from('$.group.name') == dx.group.name
    assert dx.group.get_from('$.name') == dx.group.name

    assert dx.get_from('$.some_list[0].name') == 'B'

:py:meth:`set_by_path(path, value) <lxdx.Dixt.set_by_path>` updates an existing
target using the same path syntax. Missing keys raise ``KeyError`` and invalid
list indices raise ``IndexError``; missing intermediate objects are not created.

.. code-block:: python

    dx.set_by_path('$.some_list[0].name', 'C')
    assert dx.some_list[0].name == 'C'

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

:py:meth:`diff(other) <lxdx.Dixt.diff>`

Compare visible entries recursively using original keys. Return a list of
``(left, right)`` pairs of ``Dixt`` objects containing differences, or ``[]``
when equal. Non-mapping differences share one pair; each differing nested
mapping gets its own pair. Lists are compared by position, with consecutive
equal items collapsed to ``...`` and surplus items kept on the longer side.

.. code-block:: python

    dx = Dixt(count=1, settings={'colour': 'blue'})
    assert dx.diff({'count': 2, 'settings': {'colour': 'red'}}) == [
        ({'count': 1}, {'count': 2}),
        ({'settings': {'colour': 'blue'}}, {'settings': {'colour': 'red'}}),
    ]
    assert Dixt(values=[1, 2, 3]).diff({'values': [1, 2, 4]}) == [
        ({'values': [..., 3]}, {'values': [..., 4]}),
    ]

|

:py:meth:`dict() <lxdx.Dixt.dict>`

Recursively convert nested ``Dixt`` objects, including those in lists and
tuples, to dictionaries with original keys. Hidden entries are omitted.
The built-in ``dict(dx)`` converts only the outer mapping.

.. code-block:: python

    dx = Dixt(child={'Product Name': 'Blue'})
    assert dx.dict() == {'child': {'Product Name': 'Blue'}}
    assert isinstance(dx.dict()['child'], dict)

|

:py:meth:`from_json(json_str) <lxdx.Dixt.from_json>`

:py:meth:`json() <lxdx.Dixt.json>`

These methods are included to ease up conversion from and to JSON string.

.. code-block:: python

    json_str = '{"a": "JSON string"}'
    assert Dixt.from_json(json_str).json() == json_str

|

:py:meth:`reverse() <lxdx.Dixt.reverse>`

This function will reverse the position of items -- keys become values and
values become keys.

As with ``dict``, only `hashable`_ types are accepted as keys.

.. note::
    Hidden items (flagged with metadata) are excluded from the output.

.. code-block:: python

    dx = Dixt(alpha=100, beta=200)
    assert dx.reverse() == {100: 'alpha', 200: 'beta'}

    dx = Dixt(alpha={1,2,3})
    dx.reverse()  # TypeError


.. _unit test: https://github.com/hardistones/lxdx/tree/dev/tests
.. _hashable: https://docs.python.org/3/glossary.html#term-hashable
