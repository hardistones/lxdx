"""
Copyright (c) 2021, @github.com/hardistones
All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its contributors
   may be used to endorse or promote products derived from this software without
   specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import json
import re

from collections import defaultdict
from collections.abc import KeysView, ItemsView, ValuesView, MutableMapping
from typing import Any, Dict, List, Mapping, Tuple, Union, Hashable

__all__ = ['Dixt']


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

    def __new__(cls, data=None, /, **kwargs):
        spec = dict(data or {}) | kwargs
        dx = super().__new__(cls)

        # holds all normalised keys including non-str keys
        dx.__dict__['__keymap__'] = {_normalise_key(key): key
                                     for key in spec.keys()}
        return dx

    def __init__(self, data=None, /, **kwargs):
        """Initialise an empty object, or from another mapping object,
        sequence of key-value pairs, or keyword arguments.

        :param data: Can be an iterable of key-value pairs, a ``dict``,
                     another ``Dixt`` object
        :param kwargs: Additional items which add or update
                       (if there are same keys) ``data``.
        """
        super().__init__()
        spec = dict(data or {}) | kwargs

        # holds all original keys and their values
        self.__dict__['__data__'] = _hype(spec)

        # container for keys and their meta flags
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
        if origkey := self.__get_orig_key(attr):
            if origkey in self.whats_hidden():
                del self.__hidden__[origkey]
                del self.__keymeta__[origkey]
            else:
                del self.__data__[origkey]
            del self.__keymap__[_normalise_key(attr)]
        else:
            raise KeyError(f"Dixt object has no attribute '{attr}'")

    def __delitem__(self, key):
        self.__delattr__(key)

    def __eq__(self, other):
        if isinstance(other, Dixt):
            return self.__data__.__eq__(other.__data__)
        if isinstance(other, Mapping):
            return self.__data__.__eq__(other)
        try:
            return self.__data__.__eq__(_dictify_kvp(other))
        except ValueError:
            return False

    def __getattr__(self, key):
        if origkey := self.__get_orig_key(key):
            if origkey in self.whats_hidden():
                return self.__hidden__[origkey]
            return self.__data__[origkey]
        return super().__getattribute__(key)

    def __getitem__(self, key):
        try:
            key = self.__get_orig_key(key) or key
            return self.__getattr__(key)
        except AttributeError as e:
            raise KeyError(key) from e

    def __iter__(self):
        return iter(self.__data__)

    def __len__(self):
        return len(self.__data__)

    def __repr__(self):
        return self.__str__()

    def __setattr__(self, attr, value):
        nkey = _normalise_key(attr)
        origkey = self.__get_orig_key(attr) or attr
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
        if origkey := self.__get_orig_key(key):
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
        # This function will also be called for in-place operations.
        # So no need to implement __ior__(). For example:
        #   dx = Dixt()
        #   dx |= <Mapping>
        #   dx |= <iterable key-value pairs>
        if isinstance(other, Dixt):
            other = other.dict()
        elif not isinstance(other, (tuple, list, Mapping)):
            raise TypeError(f'Invalid type ({type(other)}) for operation |')

        return Dixt(self.dict() | _dictify_kvp(other))

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
        try:
            while True:
                # proper disposal
                self.__data__.popitem()
        except KeyError:
            pass

        try:
            while True:
                # proper disposal
                self.__keymap__.popitem()
        except KeyError:
            pass

    def dict(self) -> Dict:
        """Convert this object to ``dict``, with non-normalised keys."""
        def _dictify(this):
            if isinstance(this, Dixt):
                return {key: _dictify(value)
                        for key, value
                        in this.__data__.items()}
            if isinstance(this, list):
                return [_dictify(item) for item in this]
            return this

        return _dictify(self)

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
                result.append(self.__getattr__(key))
            except AttributeError:
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
        if not isinstance(path, str):
            raise TypeError(f'Invalid path: {path}')
        if not path.startswith('$.'):
            raise ValueError(f'Invalid path: {path}')
        if path.strip().lstrip('$.') == '':
            raise ValueError(f'Invalid path: {path}')
        if re.match(r'^\$(\.\w+(\[\d+])*)+$', path) is None:
            raise ValueError(f'Invalid path: {path}')

        _path = path.replace('[', '.[').strip('$.').split('.')
        value = _traverse(self, _path)
        if isinstance(value, Exception):
            raise value from None
        return value

    def is_submap_of(self, other: Union[Mapping, List[Tuple]]) -> bool:
        """Evaluate if all of this object's keys and values are contained
        and equal to the `other`'s, recursively. This is the opposite of
        :func:`is_supermap_of`.

        :param other: Other ``dict``, ``Dixt``, or ``Mapping`` objects to compare to.
        """
        def _is_submap(this, reference):
            for key, value in this.items():
                if key not in reference:
                    return False
                if not hasattr(value, 'keys'):
                    if reference[key] != value:
                        return False
                elif not _is_submap(this[key], reference[key]):
                    return False
            return True

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
        return Dixt(other).is_submap_of(self)

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
                See separate documentation for more info.

        :raises KeyError: When any key is not found.

        .. note::
            Non-supported flags are silently bypassed.
        """
        nkeys = [_normalise_key(k) for k in keys]
        if not_found := _contents(self.__keymap__, *nkeys)[1]:
            raise KeyError(f'Key(s not found: {not_found}')

        supported_flags = set(self.__metas__).intersection(flags)
        for flag in supported_flags:
            if not isinstance(flags[flag], self.__metas__[flag]):  # noqa
                raise TypeError(f'{flag} must be {self.__metas__[flag]}')

        retval = {}
        for key in keys:
            nkey = _normalise_key(key)
            retval[nkey] = self.__keymeta__[nkey]
            for flag in supported_flags:
                add_meta_func = f'_Dixt__add_{flag}_meta'
                getattr(self, add_meta_func)(nkey, flags[flag])
            self.__cleanup_meta(nkey)

        return retval if not flags else None

    def keys(self) -> KeysView:
        """Return a set-like object providing a view
        to this object's keys.
        """
        return KeysView(self.__data__)

    def pop(self, key, default=..., /) -> Any:
        """Get the value associated with the `key`, then remove the item.

        The `default` value will be returned if `key` is not found.

        :raises KeyError: If attribute is not found
                          and default value (other than ``Ellipsis``)
                          is not specified.
        """
        try:
            retval = self.__getattr__(key)
            self.__delattr__(key)
            return retval
        except AttributeError as e:
            if default == Ellipsis:
                raise AttributeError(f"Dixt object has no key '{key}'") from e
            return default

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
        if not hasattr(other, 'keys'):
            other = _dictify_kvp(other)

        for container in (other, kwargs):
            for k, v in container.items():
                self.__setattr__(k, v)

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
        return self.__keymap__.get(_normalise_key(key))

    def __add_hidden_meta(self, key, value):
        self.__keymeta__[key]['hidden'] = value
        origkey = self.__get_orig_key(key)
        if value:
            self.__hidden__[origkey] = self.__data__[origkey]
            del self.__data__[origkey]
        else:
            self.__data__[origkey] = self.__hidden__[origkey]
            del self.__hidden__[origkey]

    def __cleanup_meta(self, key):
        """Remove empty, None, or any 'reset' values of flags
        note: key should be normalised beforehand
        """
        for flag, value in self.__meta_resets__.items():
            if self.__keymeta__[key].get(flag, 'xxx') == value:
                del self.__keymeta__[key][flag]

        # remove key completely if there's no more flags
        if not self.__keymeta__[key].keys():
            del self.__keymeta__[key]


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
    try:
        return dict(sequence or {})
    except (TypeError, ValueError) as e:
        msg = f'Sequence {sequence} is not ' \
              f'iterable key-value pairs'
        raise ValueError(msg) from e


def _contents(container, *keys):
    result, not_found = [], []
    for key in keys:
        if key in container:
            result.append(True)
        else:
            result.append(False)
            not_found.append(key)
    return tuple(result), not_found


def _traverse(obj, attrs: list):
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
        return _traverse(_obj, attrs)

    if isinstance(obj, Dixt):
        if attr not in obj.__data__:
            return KeyError(attr)
        return _traverse(getattr(obj, attr), attrs)

    return KeyError(attr)
