Metadata
========

Metadata in ``Dixt`` attach flags to individual keys and change how some
methods and operators treat their values. Flags apply only to the current
object; call ``keymeta()`` on a nested ``Dixt`` to flag its keys.

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
    * :py:meth:`reverse() <lxdx.Dixt.reverse>`
    * :py:meth:`diff() <lxdx.Dixt.diff>`
    * :py:meth:`popitem() <lxdx.Dixt.popitem>` (selects visible items only)

    Hidden items are also excluded from these operators:

    * ``==``
    * ``!=``
    * ``in``
    * ``not in``
    * ``|`` (union; see below)

    With the union operator:

    - ``|`` creates a new mapping from visible entries without changing either operand.
    - ``|=`` updates the left operand in place. Its hidden entries remain hidden
      unless a visible entry on the right has the same original key; that entry
      replaces the value and unhides the key. Hidden entries on the right are ignored.

    This flag does not block the accessibility (get, set) nor removal of the
    items from methods such as :py:meth:`clear() <lxdx.Dixt.clear>`,
    :py:meth:`update() <lxdx.Dixt.update>`, :py:meth:`pop() <lxdx.Dixt.pop>`.
    These functionalities and operations are preserved so that items can be
    "updated in the background".

    Assignment, ``update()`` and ``merge_update()`` preserve an existing hidden
    flag. Hidden source entries are skipped when updating from another ``Dixt``.
    An object containing only hidden items has length zero and is false in a
    boolean test. Hiding is a visibility feature, not access protection.


Supplementary Methods
*********************

:py:meth:`keymeta(*keys, **flags) <lxdx.Dixt.keymeta>`

Set flags for existing original or normalised keys. With no flags, return a
dictionary keyed by normalised names, containing each key's active flags
(``{}`` when none are set). With flags, return ``None``.
``hidden=False`` restores visibility and removes the flag.
Missing keys raise ``KeyError``; non-boolean ``hidden`` values raise ``TypeError``.
Unsupported flags are ignored. Query colliding normalised names separately.

:py:meth:`whats_hidden() <lxdx.Dixt.whats_hidden>`

Return a tuple of hidden original keys in the order they were hidden.
Nested objects' hidden keys are not included.

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

    assert dx.whats_hidden() == ('group_name', 'href')

    dx.keymeta('href', hidden=False)
    assert 'href' not in dx.whats_hidden()
    assert dx.keymeta('href') == {'href': {}}

    assert dx.keymeta('group_name') == {'group_name': {'hidden': True}}

**Updating hidden items**

.. code-block:: python

    dx = Dixt(public=1, secret=2)
    dx.keymeta('secret', hidden=True)
    dx.update(secret=3)
    assert dx.secret == 3
    assert dx.dict() == {'public': 1}

    assert dx | {'extra': 4} == {'public': 1, 'extra': 4}
    dx |= {'secret': 5}
    assert dx.secret == 5
    assert dx.whats_hidden() == ()
