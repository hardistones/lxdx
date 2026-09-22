# SPDX-FileCopyrightText: 2021-2026 @github.com/hardistones
# SPDX-License-Identifier: BSD-3-Clause

import json

from collections import defaultdict
from collections.abc import KeysView, ItemsView, ValuesView, MutableMapping
from jsonpath_ng import parse
from typing import Any, Dict, List, Mapping, Tuple, Union, Hashable

__all__ = ['Dixt']

_MISSING = object()


class DixtException(Exception):
    pass


class Dixt(MutableMapping):
    """``Dixt`` is an "extended" Python ``dict``, works just like ``dict``,
    but with metadata and attribute-accessibility by normalising keys.

    New methods are incorporated, such as conversion from and to JSON,
    submap/supermap comparison, and others.
    """

    # supported meta flags
    __metas__ = {'hidden': bool}

    # flags and their corresponding 'off' values.
    __meta_resets__ = {'hidden': False}

    def __init__(self, data=None, /, **kwargs):
        """Initialise an empty object, or from another mapping object,
        sequence of key-value pairs, or keyword arguments.

        :param data: Can be an iterable of key-value pairs, a ``dict``,
                     another ``Dixt`` object
        :param kwargs: Additional items which add or update ``data`` using
                       original keys or normalised aliases.

        Colliding original keys are preserved. A key already in normalised
        form owns its alias; otherwise the last colliding key owns it.
        """
        super().__init__()
        try:
            spec = dict({} if data is None else data)
        except Exception as exc:
            raise DixtException(f"Cannot convert to dict type: {data}") from exc

        # holds all normalised keys including non-str keys
        self.__dict__['__keymap__'] = {
            _normalise_key(key): (
                _normalise_key(key) if _normalise_key(key) in spec else key
            ) for key in spec
        }

        for key, value in kwargs.items():
            nkey = _normalise_key(key)
            origkey = key if key in spec else self.__keymap__.get(nkey, key)
            spec[origkey] = value
            self.__keymap__.setdefault(nkey, origkey)

        # holds all original keys and their values
        self.__dict__['__data__'] = _hype(spec)

        # container for original keys and their meta flags
        self.__dict__['__keymeta__'] = defaultdict(dict)

        # Container for hidden items as effect of the hidden flag.
        # Items in __data__ are moved here until the hidden flag is reset.
        self.__dict__['__hidden__'] = {}

        self.__dict__['__key__'] = None

        self.__dict__['__parent__'] = None

    def __contains__(self, origkey):
        """``True`` if this object contains the original (non-normalised) key,
        otherwise ``False``. This retains the original behaviour of ``dict``.
        """
        return not _contents(self.__data__, origkey)[1]

    def __delattr__(self, attr):
        """Remove the key-value entry in this object.
        Key is specified as normalised.

        :param attr: The key of the entry to be removed.

        :raises KeyError: When original key is not found.
        """
        if (origkey := self.__get_orig_key(attr)) is _MISSING:
            raise KeyError(f"Dixt object has no attribute '{attr}'")

        container = self.__hidden__ if origkey in self.__hidden__ else self.__data__
        del container[origkey]
        self.__keymeta__.pop(origkey, None)
        nkey = _normalise_key(origkey)
        owner = self.__keymap__.get(nkey, _MISSING)
        if owner is origkey or owner == origkey:
            del self.__keymap__[nkey]
            for key in (*self.__data__, *self.__hidden__):
                if _normalise_key(key) == nkey:
                    self.__keymap__[nkey] = key

    def __delitem__(self, key):
        self.__delattr__(key)

    def __eq__(self, other):
        if isinstance(other, Dixt):
            return self.__data__.__eq__(other.__data__)
        if isinstance(other, Mapping):
            return self.__data__.__eq__(other)
        if not isinstance(other, (list, tuple)):
            return False
        try:
            return self.__data__.__eq__(_dictify_kvp(other))
        except (ValueError, TypeError):
            return False

    def __getattr__(self, key):
        if (origkey := self.__get_orig_key(key)) is not _MISSING:
            if origkey in self.__hidden__:
                return self.__hidden__[origkey]
            return self.__data__[origkey]
        return super().__getattribute__(key)

    def __getitem__(self, key):
        try:
            if (_key := self.__get_orig_key(key)) is _MISSING:
                raise KeyError(key)
            if _key in self.__hidden__:
                return self.__hidden__[_key]
            return self.__data__[_key]
        except (AttributeError, TypeError) as e:
            raise KeyError(key) from e

    def __iter__(self):
        return iter(self.__data__)

    def __len__(self):
        return len(self.__data__)

    def __repr__(self):
        return self.__str__()

    def __setattr__(self, attr, value):
        nkey = _normalise_key(attr)
        if (origkey := self.__get_orig_key(attr)) is _MISSING:
            origkey = attr
        if nkey not in self.__keymap__:
            self.__keymap__[nkey] = attr

        container = self.__data__
        if not _contents(self.__hidden__, origkey)[1]:
            container = self.__hidden__

        if isinstance(value, Dixt):
            container[origkey] = value
        elif isinstance(value, dict):
            container[origkey] = Dixt(value)
        else:
            container[origkey] = _hype(value)

    def __setitem__(self, key, value):
        if (origkey := self.__get_orig_key(key)) is not _MISSING:
            if key != origkey:
                # No two keys should have the same normalised key,
                # or the new key will overwrite the other original key.
                raise KeyError(f'Cannot add "{key}" overwriting "{origkey}"')
        self.__setattr__(key, value)

    def __str__(self):
        return str(self.__data__)

    def __or__(self, other):
        """Implement union operator for this object.

        :returns: ``Dixt`` object
        """
        if isinstance(other, Dixt):
            other = other.dict()
        elif not isinstance(other, (tuple, list, Mapping)):
            raise TypeError(f'Invalid type ({type(other)}) for operation |')

        return Dixt(self.dict() | _dictify_kvp(other))

    def __ior__(self, other):
        """Update in place, preserving unmatched hidden entries on the left."""
        if isinstance(other, Dixt):
            other = other.dict()
        elif not isinstance(other, (tuple, list, Mapping)):
            raise TypeError(f'Invalid type ({type(other)}) for operation |=')

        for key, value in _dictify_kvp(other).items():
            new_key = key not in self.__data__ and key not in self.__hidden__
            if key in self.__hidden__:
                self.keymeta(key, hidden=False)
            # Union matches original keys, including colliding aliases.
            self.__data__[key] = Dixt(value) if isinstance(value, dict) else _hype(value)
            nkey = _normalise_key(key)
            if nkey == key or (new_key and nkey not in self.__data__ and nkey not in self.__hidden__):
                self.__keymap__[nkey] = key
        return self

    def __ror__(self, other) -> Dict:
        """This reverse union operator is called
        when the other object does not support union operator.
        """
        if not isinstance(other, (tuple, list, Mapping)):
            raise TypeError(f'Invalid type ({type(other)}) for operation |')

        # Call dict() to avoid maximum recursion error
        return _dictify_kvp(other) | dict(self)

    def contains(self, *keys, assert_all=True) -> Union[bool, Tuple]:
        """Evaluate if all enumerated keys exist.

        To preserve the behaviour of the operator ``in`` in Python mappings
        and sequences, this method will only accept **non-normalised** keys.

        :param keys: One or more non-normalised keys to evaluate existence of.
        :param assert_all: If ``True`` (default), assert that all keys are found,
                           returning a ``bool`` value. If ``False``, return a
                           ``tuple`` of boolean values corresponding to each
                           key whether it is found or not.
        """
        result, _ = _contents(self.__data__, *keys)
        return all(result) if assert_all else result

    def clear(self):
        """Remove all items in this object."""
        # The try-while-true mechanism is copied from Python's collections module,
        # with comment "proper disposal".
        for container in (self.__data__,
                          self.__keymap__,
                          self.__keymeta__,
                          self.__hidden__):
            try:
                while True:
                    container.popitem()
            except KeyError:
                pass

    def dict(self) -> Dict:
        """Convert this object to ``dict``, with non-normalised keys."""
        def _dictify(this):
            if isinstance(this, Dixt):
                this = this.__data__
            if isinstance(this, Mapping):
                return {key: _dictify(value)
                        for key, value
                        in this.items()}
            if isinstance(this, list):
                return [_dictify(item) for item in this]
            if isinstance(this, tuple):
                return tuple(_dictify(item) for item in this)
            return this

        return _dictify(self)

    def diff(self, other: Mapping, /) -> List[Tuple]:
        """Return the recursive difference between this object and `other`.

        Compares each key-value pair, recursing into nested ``Mapping``
        values. Equal pairs are excluded from the result.
        Keys are matched by their original form at every nesting level.
        Differences preserve each mapping's original keys. Hidden items
        (see :meth:`keymeta`) are not compared.

        ``list`` values paired on both sides are compared element-by-element:

        * a run of consecutive equal items is collapsed into a single
          ``Ellipsis`` (``...``) placeholder;
        * paired ``Mapping`` items are diffed recursively;
        * paired ``list`` items are diffed recursively as lists;
        * any other differing pair is kept as-is on both sides;
        * when the lengths differ, the surplus items are kept as-is
          on the side that has them.

        :param other: Another ``Dixt`` or any ``Mapping`` to diff against.
        :returns: A list of ``(self_diff, other_diff)`` tuples of ``Dixt``
                  objects containing only the differing entries: one pair for
                  all differing non-``Mapping`` entries (when any), followed by
                  one pair per key whose ``Mapping`` value differs.
                  An empty list is returned when the two objects are equal.
                  Non-``Mapping`` non-builtin values are represented by their
                  ``repr()``.
        :raises TypeError: If `other` is not a ``Mapping``.
        """
        if not isinstance(other, Mapping):
            raise TypeError(f'Expected Mapping, got {type(other)}')

        root_self, root_other, branches = _diff_entries(self, other)

        result = []
        if root_self or root_other:
            result.append((Dixt(root_self), Dixt(root_other)))
        result.extend((Dixt({key: sub_self}), Dixt({key: sub_other}))
                      for key, sub_self, sub_other in branches)
        return result

    def getx(self, *attrs, default=None) -> Any:
        """Get one or more items specified in `attrs`.
        Replace nonexistent item(s) with value(s) in default.

        :param attrs: One or more normalised or non-normalised keys to get items of.
        :param default: Use as replacement value for all keys not found
                        if set with a non-``list``/``tuple`` value.
                        If ``list`` or ``tuple``, a one-to-one correspondence
                        of values to `attrs` when not found.

        :returns: A ``tuple`` of associated item of the `attrs`, replacing items
                  of any key not found with the `default`.

                  Except when ``len(attrs) == 1``, in which the method
                  returns the actual item and not ``tuple``.

        :raises ValueError: When ``len(default) != len(attrs)``, only when
                            default is a ``list``/``tuple``.

        Similar method: :meth:`setdefault`.
        """
        if isinstance(default, (tuple, list)):
            if len(default) != len(attrs):
                raise ValueError(f'Length of {attrs} and {default} not equal.')
        else:
            default = [default] * len(attrs)
        result = []

        for i, key in enumerate(attrs):
            try:
                result.append(self[key])
            except KeyError:
                result.append(default[i])

        return tuple(result) if len(result) > 1 else result[0]

    def get_from(self, path: str, /) -> Any:
        """Get the item from the specified path of the key.
        Path is the 'stringified' attribute-style accessibility.

        :param path: The direction to the target item specified by
                     ``$.<key>.{...}.<target-key>``, where the required
                     ``$`` points to the object where this method is called.
                     The series of keys must be the normalised keys.

        :raises TypeError, ValueError: Invalid path.
        :raises KeyError: Key is not found.
        :raises IndexError: Invalid list index.

        Examples:
            .. code-block::

                dixt.get_from('$.group.name')          # dixt.group.name
                dixt.group.get_from('$.some.list[1]')  # dixt.group.some.list[1]

        .. note::
            - Path is only evaluated for public *attributes*.
            - Only one (1) item can be accessed from any ``list``. That is, no slicing.
        """
        _validate_path(path)
        _path = path.replace('[', '.[').strip('$.').split('.')
        value = _get_by_path(self, _path)
        if isinstance(value, Exception):
            raise value from None
        return value

    def is_submap_of(self, other: Union[Mapping, List[Tuple]]) -> bool:
        """Evaluate if all of this object's keys and values are contained
        and equal to the `other`'s, recursively. This is the opposite of
        :func:`is_supermap_of`.

        :param other: Other ``dict``, ``Dixt``, or ``Mapping`` objects to compare to.
        """
        if not isinstance(other, (tuple, list, Mapping)):
            raise TypeError(f'Invalid type ({type(other)})')
        if not isinstance(other, Dixt):
            other = _dictify_kvp(other)
        return _is_submap(self, other)

    def is_supermap_of(self, other: Union[Mapping, List[Tuple]]) -> bool:
        """Evaluate if all the `other` object's keys and values are contained
        and equal to this object's, recursively. This is the opposite of
        :func:`is_submap_of`.

        :param other: Other ``dict``, ``Dixt``, or ``Mapping`` objects to compare to.
        """
        if not isinstance(other, (tuple, list, Mapping)):
            raise TypeError(f'Invalid type ({type(other)})')
        if not isinstance(other, Mapping):
            other = _dictify_kvp(other)
        return _is_submap(other, self)

    def items(self) -> ItemsView:
        """Return a set-like object providing a view
        to this object's key-value pairs.
        """
        return ItemsView(self.__data__)

    def json(self) -> str:
        """Convert this object to JSON string."""
        return json.dumps(self.dict())

    def keymeta(self, *keys, **flags):
        """Add metadata to one or more `keys`. If no `flags` are specified,
        return all metadata for the `keys`.

        Supported flags:
            * hidden (boolean)
                Hides the item from the output/result or processing of
                some methods and operators of ``Dixt``.
                See documentation for more info.

        :raises KeyError: When any key is not found.

        .. note::
            Non-supported flags are silently bypassed.
        """
        origkeys = [self.__get_orig_key(key) for key in keys]
        if not_found := [key for key, origkey in zip(keys, origkeys) if origkey is _MISSING]:
            raise KeyError(f'Key(s not found: {not_found}')

        supported_flags = set(self.__metas__).intersection(flags)
        for flag in supported_flags:
            if not isinstance(flags[flag], self.__metas__[flag]):  # noqa
                raise TypeError(f'{flag} must be {self.__metas__[flag]}')

        retval = {}
        for key in origkeys:
            nkey = _normalise_key(key)
            retval[nkey] = self.__keymeta__[key]
            for flag in supported_flags:
                add_meta_func = f'_Dixt__add_{flag}_meta'
                getattr(self, add_meta_func)(key, flags[flag])
            self.__cleanup_meta(key)

        return retval if not flags else None

    def keys(self) -> KeysView:
        """Return a set-like object providing a view
        to this object's keys.
        """
        return KeysView(self.__data__)

    def pop(self, key, default=..., /) -> Any:
        """Get the value associated with the `key`, then remove the item.

        The `default` value will be returned if `key` is not found.

        :raises AttributeError: If the key is not found and a default value
                                (other than ``Ellipsis``) is not specified.
        """
        try:
            retval = self[key]
        except KeyError as e:
            if default is Ellipsis:
                raise AttributeError(f"Dixt object has no key '{key}'") from e
            return default
        del self[key]
        return retval

    def popitem(self) -> tuple:
        """Returns a ``tuple`` of key-value pair.
        Since this function is inherited not from `dict`,
        LIFO is not guaranteed.

        :raises KeyError: If this object is empty.
        """
        return super().popitem()

    def reverse(self):
        """Reverse the key-value map on the first layer items with hashable values.
        See `hashable <https://docs.python.org/3/glossary.html#term-hashable>`_
        for more info.

        Any item flagged as hidden will be excluded.

        :raises TypeError: If any value is non-hashable.
        """
        return Dixt({value: key for key, value in self.__data__.items()})

    def set_by_path(self, path: str, value) -> None:
        _validate_path(path)
        _path = path.replace('[', '.[').replace('..', '.').strip('$.').split('.')
        _set_by_path(self, _path, value)

    def setdefault(self, key, default=None) -> Any:
        """Get value associated with `key`. If `key` exists, return ``self[key]``;
        otherwise, set ``self[key] = default`` then return `default` value.

        Similar method: :meth:`get`.
        """
        return super().setdefault(key, default)

    def update(self, other=(), /, **kwargs):
        """Update this object from another ``Mapping`` objects (e.g., ``dict``, ``Dixt``),
        from an iterable key-value pairs, or through keyword arguments.
        """
        if not isinstance(other, Mapping):
            other = _dictify_kvp(other)

        for container in (other, kwargs):
            for k, v in container.items():
                self.__setattr__(k, v)

    def merge_update(self, other, *, recurse_lists=False):
        """Update this object with the contents of ``other`` recursively.

        Unlike :meth:`update`, nested ``Mapping`` values are merged rather than
        replaced. For ``list`` values, behaviour depends on ``recurse_lists``.

        :param other: A ``Mapping`` (e.g. ``dict``, ``Dixt``) to merge from.

        :param recurse_lists: If ``True``, merge list items element-by-element
            rather than replacing the whole list. The list is resized to match
            ``other``'s length.
            If ``False`` (default), the list in ``self`` is replaced entirely.

        :raises TypeError: If ``other`` is not a ``Mapping``.
        """
        if not isinstance(other, Mapping):
            raise TypeError(f'Expected Mapping, got {type(other)}')

        for key, other_value in other.items():
            self_value = self.get(key, _MISSING)

            if self_value is _MISSING:
                self.__setattr__(key, other_value)
            elif isinstance(self_value, Mapping) and isinstance(other_value, Mapping):
                if not isinstance(self_value, Dixt):
                    self_value = Dixt(self_value)
                    self.__setattr__(key, self_value)
                self_value.merge_update(other_value, recurse_lists=recurse_lists)
            elif isinstance(self_value, list) and isinstance(other_value, list):
                if recurse_lists:
                    _merge_list_update(self_value, other_value, recurse_lists)
                else:
                    self.__setattr__(key, other_value)
            else:
                self.__setattr__(key, other_value)

    def values(self) -> ValuesView:
        """Return a set-like object providing a view
        to this object's values.
        """
        return ValuesView(self.__data__)

    def whats_hidden(self) -> tuple:
        """Get all keys that have the ``hidden`` metadata.

        :return: Tuple of non-normalised keys.
        """
        return tuple(self.__hidden__.keys())

    @staticmethod
    def from_json(json_str, /):
        """Convert a JSON string to a ``Dixt`` object."""
        return Dixt(json.loads(json_str))  # let json handle errors

    def __get_orig_key(self, key):
        """Return the original key, or the private sentinel if not found."""
        # Copy reconstruction can query attributes before restoring state.
        state = object.__getattribute__(self, '__dict__')
        if key in state.get('__data__', {}) or key in state.get('__hidden__', {}):
            return key
        return state.get('__keymap__', {}).get(_normalise_key(key), _MISSING)

    def __add_hidden_meta(self, key, value):
        self.__keymeta__[key]['hidden'] = value
        if value == (key in self.__hidden__):
            return
        if value:
            self.__hidden__[key] = self.__data__[key]
            del self.__data__[key]
        else:
            self.__data__[key] = self.__hidden__[key]
            del self.__hidden__[key]

    def __cleanup_meta(self, key):
        """Remove empty, None, or any 'reset' values of flags
        note: key must be the original key
        """
        for flag, value in self.__meta_resets__.items():
            if self.__keymeta__[key].get(flag, 'xxx') == value:
                del self.__keymeta__[key][flag]

        # remove key completely if there's no more flags
        if not self.__keymeta__[key].keys():
            del self.__keymeta__[key]


def _is_submap(this, reference):
    """Compare keys and values recursively against a reference mapping."""
    if not isinstance(reference, Mapping):
        return False
    for key, value in this.items():
        if key not in reference:
            return False
        other_value = reference[key]
        if isinstance(value, Mapping):
            if not _is_submap(value, other_value):
                return False
        elif other_value is not value and other_value != value:
            return False
    return True


def _to_repr_if_nonbuiltin(value):
    if isinstance(value, Mapping):
        return Dixt({key: _to_repr_if_nonbuiltin(item) for key, item in value.items()})
    if isinstance(value, list):
        return [_to_repr_if_nonbuiltin(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_to_repr_if_nonbuiltin(item) for item in value)
    if value is Ellipsis:
        return value
    if isinstance(value, (bool, int, float, complex, str, bytes, bytearray,
                          set, frozenset, type(None))):
        return value
    return repr(value)


def _diff_entries(self_dixt, other):
    """Compare two mappings key by key, matching their original keys.

    :returns: A ``(root_self, root_other, branches)`` tuple, where the roots are
              ``dict``s of all differing non-``Mapping`` entries, and `branches`
              is a list of ``(key, self_diff, other_diff)`` tuples, one per key
              whose ``Mapping`` value differs.
    """
    other_dixt = other if isinstance(other, Dixt) else Dixt(other)
    self_data, other_data = self_dixt.__data__, other_dixt.__data__

    root_self: dict = {}
    root_other: dict = {}
    branches: list = []

    for key in self_data:
        if key not in other_data:
            root_self[key] = _to_repr_if_nonbuiltin(self_data[key])
            continue

        sv, ov = self_data[key], other_data[key]
        if sv is ov or sv == ov:
            continue

        if isinstance(sv, Mapping) and isinstance(ov, Mapping):
            sub = _diff_mappings(sv, ov)
            if sub is not None:
                branches.append((key, *sub))
        elif isinstance(sv, list) and isinstance(ov, list):
            sub = _diff_lists(sv, ov)
            if sub is not None:
                root_self[key], root_other[key] = sub
        else:
            root_self[key] = _to_repr_if_nonbuiltin(sv)
            root_other[key] = _to_repr_if_nonbuiltin(ov)

    root_other.update(
        (key, _to_repr_if_nonbuiltin(value))
        for key, value in other_data.items() if key not in self_data
    )

    return root_self, root_other, branches


def _diff_mappings(self_map, other_map):
    """Consolidate the recursive diff of two ``Mapping`` objects into
    a single ``(self_diff, other_diff)`` pair of ``Dixt`` objects,
    or ``None`` when the two mappings are equal.
    """
    self_dixt = self_map if isinstance(self_map, Dixt) else Dixt(self_map)
    sd, od, branches = _diff_entries(self_dixt, other_map)

    for key, sub_self, sub_other in branches:
        sd[key], od[key] = sub_self, sub_other

    if sd or od:
        return Dixt(sd), Dixt(od)
    return None


def _diff_lists(self_list, other_list):
    """Diff two lists element-by-element, collapsing runs of equal items
    into a single ``Ellipsis``, and keeping the surplus items of the
    longer list as-is.

    :returns: A ``(self_diff, other_diff)`` tuple of ``list`` objects,
              or ``None`` when there are no visible differences.
    """
    def _collapse(container):
        if not container or container[-1] is not Ellipsis:
            container.append(...)

    sd: list = []
    od: list = []
    different = len(self_list) != len(other_list)
    min_len = min(len(self_list), len(other_list))

    for i in range(min_len):
        sv, ov = self_list[i], other_list[i]
        if sv is ov or sv == ov:
            _collapse(sd)
            _collapse(od)
        elif isinstance(sv, Mapping) and isinstance(ov, Mapping):
            sub = _diff_mappings(sv, ov)
            if sub is None:
                _collapse(sd)
                _collapse(od)
            else:
                different = True
                sd.append(sub[0])
                od.append(sub[1])
        elif isinstance(sv, list) and isinstance(ov, list):
            sub = _diff_lists(sv, ov)
            if sub is None:
                _collapse(sd)
                _collapse(od)
            else:
                different = True
                sd.append(sub[0])
                od.append(sub[1])
        else:
            different = True
            sd.append(_to_repr_if_nonbuiltin(sv))
            od.append(_to_repr_if_nonbuiltin(ov))

    sd.extend(_to_repr_if_nonbuiltin(item) for item in self_list[min_len:])
    od.extend(_to_repr_if_nonbuiltin(item) for item in other_list[min_len:])

    return (sd, od) if different else None


def _hype(spec):
    if isinstance(spec, Dixt):
        return spec

    if isinstance(spec, (list, tuple)):
        return spec.__class__(
            Dixt(item)
            if isinstance(item, dict) else _hype(item)
            for item in spec)

    if issubclass(type(spec), dict):
        data = {}
        for key, value in spec.items():
            if issubclass(type(value), dict):
                data[key] = Dixt(value)
                data[key].__dict__['__key__'] = key
            elif isinstance(value, (list, tuple)):
                data[key] = _hype(value)
            else:
                data[key] = value
        return data

    return spec


def _merge_list_update(self_list, other_list, recurse_lists):
    min_len = min(len(self_list), len(other_list))

    for i in range(min_len):
        if isinstance(self_list[i], Mapping) and isinstance(other_list[i], Mapping):
            if not isinstance(self_list[i], Dixt):
                self_list[i] = Dixt(self_list[i])
            self_list[i].merge_update(other_list[i], recurse_lists=recurse_lists)
        elif recurse_lists and isinstance(self_list[i], list) and isinstance(other_list[i], list):
            _merge_list_update(self_list[i], other_list[i], recurse_lists)
        else:
            self_list[i] = Dixt(other_list[i]) if isinstance(other_list[i], dict) else _hype(other_list[i])

    if len(other_list) < len(self_list):
        del self_list[min_len:]
    elif len(other_list) > len(self_list):
        for item in other_list[min_len:]:
            self_list.append(Dixt(item) if isinstance(item, dict) else _hype(item))


def _normalise_key(key: Hashable) -> Hashable:
    """Internal dict handles the incoming keys,
    so the item's hashability is not checked here.
    """
    if isinstance(key, str):
        return key.strip()\
                  .replace(' ', '_')\
                  .replace('-', '_')\
                  .lower()
    return key


def _dictify_kvp(sequence):
    err_msg = f'Sequence {sequence} is not iterable key-value pairs'
    try:
        iter(sequence)
    except TypeError as e:
        raise TypeError(err_msg) from e
    if isinstance(sequence, (str, bytes, bytearray)):
        raise TypeError(err_msg)
    try:
        return dict(sequence)
    except (TypeError, ValueError) as e:
        raise ValueError(err_msg) from e


def _contents(container, *keys):
    result, not_found = [], []
    for key in keys:
        if key in container:
            result.append(True)
        else:
            result.append(False)
            not_found.append(key)
    return tuple(result), not_found


def _validate_path(path):
    if not isinstance(path, str):
        raise TypeError(f'Invalid path: {path}')
    if not path.startswith('$.'):
        raise ValueError(f'JSON path must start with "$.": {path}')
    if path.strip().lstrip('$.') == '':
        raise ValueError(f'Invalid path: {path}')

    try:
        parse(path)
    except Exception:
        raise ValueError(f'Invalid JSON path: {path}')


def _get_by_path(obj: Dixt, attrs: list):
    if not attrs:
        # We have successfully got obj from previous call
        # so obj must be the correct value.
        return obj

    attr = attrs.pop(0)

    if isinstance(obj, (list, tuple)):
        try:
            _obj = eval('obj' + attr)
        except IndexError as e:
            return e
        return _get_by_path(_obj, attrs)

    if isinstance(obj, Dixt):
        if obj.getx(attr, default=...) is Ellipsis:
            return KeyError(attr)
        return _get_by_path(getattr(obj, attr), attrs)

    return KeyError(attr)


def _set_by_path(obj: Dixt, attrs: list, value):
    attr = attrs.pop(0)

    if isinstance(obj, (list, tuple)):
        try:
            _obj = eval('obj' + attr)
        except IndexError as e:
            raise e

        if not attrs:
            obj[int(attr.strip('[]'))] = value
        else:
            _set_by_path(_obj, attrs, value)

    elif isinstance(obj, Dixt):
        if attr.startswith('["') and attr.endswith('"]'):
            # Support access like '$.headers.["Content-Type"]'
            attr = attr[2:-2]
        if obj.getx(attr, default=...) is Ellipsis:
            raise KeyError(attr)
        if not attrs:
            setattr(obj, attr, value)
        else:
            _set_by_path(getattr(obj, attr), attrs, value)

    else:
        raise KeyError(attr)
