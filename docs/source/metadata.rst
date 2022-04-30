Metadata
========

Metadata in ``Dixt`` are an extra information alongside the key-value pair data.
It is implemented using flags with boolean values, and in effect alter the
behaviour of some of the ``Dixt`` (and ``dict``) functions.

Currently, only one flag is supported.

Available flags
***************

**hidden** `(boolean)`
    This flag hides the key-value items from the result of, or processing inside,
    the following methods, builtin functions, and iterators:

    * ``len()``
    * ``str()``
    * ``repr()``
    * ``iter()``
    * :py:meth:`keys() <lxdx.Dixt.keys>`
    * :py:meth:`items() <lxdx.Dixt.items>`
    * :py:meth:`values() <lxdx.Dixt.values>`
    * :py:meth:`contains() <lxdx.Dixt.contains>`
    * :py:meth:`dict() <lxdx.Dixt.dict>`
    * :py:meth:`json() <lxdx.Dixt.json>`
    * :py:meth:`is_supermap_of() <lxdx.Dixt.is_supermap_of>`
    * :py:meth:`is_submap_of() <lxdx.Dixt.is_submap_of>`

    Flagged items are also hidden from the operators:

    * ``==``
    * ``!=``
    * ``in``
    * ``not in``

    This flag does not block the accessibility (get, set) nor removal of the items
    from methods such as :py:meth:`clear() <lxdx.Dixt.clear>`,
    :py:meth:`update() <lxdx.Dixt.update>`, :py:meth:`pop() <lxdx.Dixt.pop>`,
    nor affect the `union operator`_ (``|``). These functions and operations
    are preserved so that items can be "updated in the background".


Supplementary Methods
*********************

:py:meth:`keymeta(*keys, **flags) <lxdx.Dixt.keymeta>`

:py:meth:`whats_hidden() <lxdx.Dixt.whats_hidden>`


Examples
********

**Flagging items as hidden**

.. code-block:: python

    from lxdx import Dixt

    data = {'group_name': str,
            'name': str,
            'href': str,
            'kind': str,
            'value': int}

    dx = Dixt(data)
    dx.keymeta('group_name', 'href', hidden=True)

    assert dx == {'name': str, 'kind': str, 'value': int}
    assert 'href' not in dx
    assert dx.href == str

    assert dx.flagged_items() == ('href', 'group_name')

    dx.keymeta('href', hidden=False)
    assert 'href' in dx.whats_hidden() == False

    assert dx.keymeta('group_name') == {'group_name': {'hidden': True}}


.. References
.. _union operator: https://www.python.org/dev/peps/pep-0584
