Normalisation
=============

To achieve the attribute-like accessibility of keys in a ``Dixt`` object,
normalisation of keys is implemented.

In the context of ``Mapping`` objects, there are only `keys` and `values`.
But in ``Dixt``, a `key` can be accessed and modified by using the
`dot notation`_, which makes it a `semi-attribute`.

Keys are stored as:
    * non-normalised
        These are the literal/original, unchanged keys passed as they are,
        like in the usual ``dict``.

    * normalised
        The modified keys, used for comparison when keys are accessed using
        the dot notation.

So in the context of the ``Dixt`` class and its object, `key` and `attribute` can be
interchangeable.


How it looks
------------
A normalised key looks like a lower-case-converted string with spaces
and hyphens replaced with underscores.

So a key like ``Man-made Object`` will be normalised as ``man_made_object``,
and can be accessed either by

.. code-block::

    dixt['Man-made Object']

or

.. code-block::

    dixt.man_made_object

Caveat
------

.. important::
    In effect, ``Dixt`` imposes case-insensitive keys due to the
    normalisation. For instance, the following keys will be the same:

    * An-Attribute
    * an_attribute
    * an attribute

This makes the item setting stricter than the usual in ``dict``:

.. code-block::

    dixt['An-Attribute'] = 'value'
    dixt['an_attribute'] = 'value'  # throws KeyError in Dixt, but not with dict


.. References
.. _dot notation: https://en.wikipedia.org/wiki/Property_(programming)#Dot_notation
