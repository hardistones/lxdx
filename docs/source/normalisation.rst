Normalisation
=============

To achieve the attribute-like accessibility of keys in a ``Dixt`` object,
normalisation of keys is implemented.

In the context of ``Mapping`` objects (like ``dict``), there are only `keys` and `values`.
But in ``Dixt``, a `key` can be accessed and modified by using the
`dot notation`_, which makes keys `semi-attributes`.

Keys are stored as:
    * non-normalised
        These are the literal/original, unchanged keys passed as they are,
        as in ``dict``.

    * normalised
        The modified keys, used for comparison when keys are accessed using
        the dot notation.

So in the context of the ``Dixt`` class and its object, `key` and `attribute` can be
interchangeable.


How it looks
************

A normalised key is a lower-case-converted string with spaces
and hyphens replaced with underscores.

So a key like ``Man-made Object`` will be normalised as ``man_made_object``,
and can be accessed either by

.. code-block:: python

    dixt['Man-made Object']

or

.. code-block:: python

    dixt.man_made_object

Restrictions
************

Some of the ``dict`` operations are preserved, like ``in``/``not in``, where
normalised keys cannot be used.

Unless specified that it cannot, methods can accept both types of keys.

.. important::

    This restriction might be perceived as incorrect when an original key
    and the corresponding normalised key are the same. This is an exception.

Limitations
***********

Normalisation cannot happen in the following code:

.. code-block:: python

    dixt.some_list[1] = {'key': 'value'}

due to the fact that the assignment is handled by ``list`` and not by ``Dixt``.
It should be wrapped before the assignment.

.. code-block:: python

    dixt.some_list[1] = Dixt(key='value')

Caveat
******

In effect, ``Dixt`` imposes case-insensitive keys due to the
normalisation. For instance, these keys will be the same: ``An-Attribute``,
``an_attribute``, ``an attribute``.

Case-insensitivity makes item setting stricter than what is usual in ``dict``:

.. code-block:: python

    dixt['An-Attribute'] = 'value'
    dixt['an_attribute'] = 'value'  # throws KeyError in Dixt, but not with dict


.. References
.. _dot notation: https://en.wikipedia.org/wiki/Property_(programming)#Dot_notation
