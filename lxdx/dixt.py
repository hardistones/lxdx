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

from collections.abc import KeysView, ItemsView, ValuesView, MutableMapping
from dataclasses import MISSING
from typing import Any, Dict, Mapping, Union, Tuple


__all__ = ['Dixt']


class Dixt(MutableMapping):
    """``Dixt`` is an "extended" Python ``dict``, works just like a ``dict``,
    but with attribute-accessible keys by normalising keys and metadata.

    New methods are incorporated, such as conversion from and to JSON,
    submap/supermap comparison, and others.
    """

    def __new__(cls, data=None, /, **kwargs):
        spec = dict(data or {}) | kwargs
        dx = super().__new__(cls)
        dx.__dict__['keymap'] = {_normalise_key(key): key
                                 for key in spec.keys()}
        return dx

    def __init__(self, data=None, /, **kwargs):
        """Initialise an empty object, or from another mapping object,
        sequence of key-value pairs, or keyword arguments.

        :param data: Can be a iterable of key-value pairs, a ``dict``,
                     another ``Dixt`` object
        :param kwargs: Additional items which add or update
                       (if there are same keys) ``data``.
        """
        super().__init__()
        spec = dict(data or {}) | kwargs
        self.__dict__['data'] = _hype(spec)

    def __contains__(self, origkey):
        """``True`` if the this object contains the original (non-normalised) key,
        otherwise ``False``. This retains the original behaviour of ``dict``.
        """
        return origkey in self.__dict__['data']

    def __delattr__(self, attr):
        """Remove the key-value entry in this object.
        Key is specified as normalised.

        :param attr: The key of the entry to be removed.

        :raises KeyError: When original key is not found.
        """
        if origkey := self._get_orig_key(attr):
            del self.__dict__['data'][origkey]
            del self.__dict__['keymap'][_normalise_key(attr)]
        else:
            raise KeyError(f"{self.__class__.__name__} "
                           f"object has no attribute '{attr}'")

    def __delitem__(self, key):
        self.__delattr__(key)

    def __eq__(self, other):
        if isinstance(other, Dixt):
            return self.__dict__['data'].__eq__(other.__dict__['data'])
        if isinstance(other, Mapping):
            return self.__dict__['data'].__eq__(other)
        try:
            return self.__dict__['data'].__eq__(_dictify_kvp(other))
        except ValueError:
            return False

    def __getattr__(self, key):
        if origkey := self._get_orig_key(key):
            return self.__dict__['data'][origkey]

        try:
            return super().__getattribute__(key)
        except AttributeError:
            raise KeyError(key)

    def __getitem__(self, key):
        key = self._get_orig_key(key) or key
        return self.__getattr__(key)

    def __iter__(self):
        return iter(self.__dict__['data'])

    def __len__(self):
        return len(self.__dict__['data'])

    def __repr__(self):
        return self.__str__()

    def __setattr__(self, attr, value):
        if value is MISSING:
            try:
                self.__delitem__(attr)
            finally:
                return

        self.__dict__['keymap'][_normalise_key(attr)] = attr
        if isinstance(value, Dixt):
            self.__dict__['data'][attr] = value
        elif isinstance(value, dict):
            self.__dict__['data'][attr] = Dixt(value)
        else:
            self.__dict__['data'][attr] = _hype(value)

    def __setitem__(self, key, value):
        if origkey := self._get_orig_key(key):
            if key != origkey:
                # No two keys should have the same normalised key,
                # or the new key will overwrite the other original key.
                raise KeyError(f'Cannot add "{key}" overwriting "{origkey}"')
        self.__setattr__(key, value)

    def __str__(self):
        return str(self.__dict__['data'])

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
        result = (self.__contains__(k) for k in keys)
        return all(result) if assert_all else tuple(result)

    def clear(self):
        """Remove all items in this object."""
        try:
            while True:
                # proper disposal
                self.__dict__['data'].popitem()
        except KeyError:
            pass

        try:
            while True:
                # proper disposal
                self.__dict__['keymap'].popitem()
        except KeyError:
            pass

    def dict(self) -> Dict:
        """Convert this object to ``dict``, with non-normalised keys."""
        def _dictify(this):
            if isinstance(this, Dixt):
                return {key: _dictify(value)
                        for key, value
                        in this.__dict__['data'].items()}
            elif isinstance(this, list):
                return [_dictify(item) for item in this]
            return this

        return _dictify(self)

    def get(self, *attrs, default=None) -> Any:
        """Get the items from a sequence of `attrs`.

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

        default = [default] * len(attrs)
        result = []

        for i, key in enumerate(attrs):
            try:
                result.append(self.__getattr__(key))
            except KeyError:
                result.append(default[i])

        return result if len(result) > 1 else result[0]

    def get_from(self, path: str, /) -> Any:
        """Get the item from the specified path of the key.
        Path is the 'stringified' attribute-style accessibility.

        :param path: The direction to the target item specified by
                     ``$.<key>.{...}.<target-key>``, where
                     ``$`` points to the object where this method is called.
                     The series of keys must be the normalised keys.

        :raises TypeError, ValueError: Invalid path.
        :raises KeyError: When key is not found.

        Examples:
            .. code-block::

                dixt.get_from('$.group.name')  # $ points to dixt
                dixt.group.get_from('$.name')  # $ points to group
        """
        if not isinstance(path, str):
            raise TypeError(f'Invalid path: {path}')
        if not path.startswith('$.'):
            raise ValueError(f'Invalid path: {path}')
        return eval(f"{path.replace('$', 'self')}")

    def is_submap_of(self, other) -> bool:
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

    def is_supermap_of(self, other) -> bool:
        """Evaluate if all of the `other` object's keys and values are contained
        and equal to this object's, recursively. This is the opposite of
        :func:`is_submap_of`.

        :param other: Other ``dict``, ``Dixt``, or ``Mapping`` objects to compare to.
        """
        return Dixt(other).is_submap_of(self)

    def items(self) -> ItemsView:
        """Return a set-like object providing a view
        to this object's key-value pairs.
        """
        return ItemsView(self.__dict__['data'])

    def json(self) -> str:
        """Convert this object to JSON string."""
        return json.dumps(self.dict())

    def keys(self) -> KeysView:
        """Return a set-like object providing a view
        to this object's keys.
        """
        return KeysView(self.__dict__['data'])

    def pop(self, key, default=..., /) -> Any:
        """Get the value associated with the `key`, then remove the item.

        The `default` value will be returned if `key` is not found.

        :raises KeyError: If attribute is not found
                          and default value (other than ``Ellipsis``)
                          is not specified.
        """
        if retval := self.get(key):
            self.__delattr__(key)
            return retval
        if default == Ellipsis:
            raise KeyError(f"Dixt object has no key '{key}'")
        return default

    def popitem(self) -> tuple:
        """Returns a ``tuple`` of key-value pair.
        Since this function is inherited not from `dict`,
        LIFO is not guaranteed.

        :raises KeyError: If this object is empty.
        """
        return super().popitem()


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
        return ValuesView(self.__dict__['data'])

    @staticmethod
    def from_json(json_str, /):
        """Convert a JSON string to a ``Dixt`` object."""
        return Dixt(json.loads(json_str))  # let json handle errors

    def _get_orig_key(self, key):
        return self.__dict__['keymap'].get(_normalise_key(key))


def _hype(spec):
    if isinstance(spec, Dixt):
        return spec

    if isinstance(spec, (list, tuple)):
        return [Dixt(**item)
                if isinstance(item, dict) else _hype(item)
                for item in spec]

    if issubclass(type(spec), dict):
        data = {}
        for key, value in spec.items():
            if issubclass(type(value), dict):
                data[key] = Dixt(value)
            elif isinstance(value, (list, tuple)):
                data[key] = _hype(value)
            elif value is not MISSING:
                data[key] = value
        return data

    if spec is not MISSING:
        return spec


def _normalise_key(item):
    """Internal dict handles the incoming keys,
    so the item's hashability is not checked here.
    """
    if isinstance(item, str):
        return item.strip().replace(' ', '_').replace('-', '_').lower()
    return item


def _dictify_kvp(sequence):
    try:
        return dict(sequence or {})
    except (TypeError, ValueError):
        raise ValueError(f'Sequence {sequence} is not iterable key-value pairs')
