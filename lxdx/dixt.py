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
from typing import Union, Mapping, TypeVar


__all__ = ['Dixt']

IterableKeyValuePairs = TypeVar('IterableKeyValuePairs', tuple, list)


class Dixt(MutableMapping):

    def __new__(cls, data=None, /, **kwargs):
        spec = dict(data or {}) | kwargs
        dx = super().__new__(cls)
        dx.__dict__['keymap'] = {_normalise_key(key): key
                                 for key in spec.keys()}
        return dx

    def __init__(self, data=None, /, **kwargs):
        """Initialise this object with dict,
        a sequence of key-value pairs, or keyword arguments.

        :param data: Can be a iterable of key-value pairs,
                     a dict, another Dixt object
        """
        super().__init__()
        spec = dict(data or {}) | kwargs
        self.__dict__['data'] = _hype(spec)

    def __contains__(self, origkey):
        return origkey in self.__dict__['data']

    def __delattr__(self, attr):
        if origkey := self._get_orig_key(attr):
            del self.__dict__['data'][origkey]
            del self.__dict__['keymap'][_normalise_key(attr)]
        else:
            raise AttributeError(f"{self.__class__.__name__} object has no attribute '{attr}'")

    def __delitem__(self, key):
        try:
            self.__delattr__(key)
        except AttributeError:
            raise KeyError(key)

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

        # This lets the super class handle the attribute error
        return super().__getattribute__(key)

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
        self.__setattr__(key, value)

    def __str__(self):
        return str(self.__dict__['data'])

    def __or__(self, other: Union[Mapping, IterableKeyValuePairs]):
        """Implement union operator for this object.

        :returns: Dixt object
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

    def __ror__(self, other: Union[Mapping, IterableKeyValuePairs]) -> dict:
        """This reverse union operator is called
        when the other object does not support union operator.
        """
        if not isinstance(other, (tuple, list, Mapping)):
            raise TypeError(f'Invalid type ({type(other)}) for operation |')

        # Call dict() to avoid maximum recursion error
        return _dictify_kvp(other) | dict(self)

    def contains(self, *keys) -> bool:
        """Evaluate if all enumerated keys exist."""
        return all(self.__contains__(k) for k in keys)

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

    def dict(self):
        """Convert this object to dict, with non-normalised keys."""
        def _dictify(this):
            if isinstance(this, Dixt):
                return {key: _dictify(value)
                        for key, value
                        in this.__dict__['data'].items()}
            elif isinstance(this, list):
                return [_dictify(item) for item in this]
            return this

        return _dictify(self)

    def get(self, attr, default=None):
        """Get the value of the key specified by `attr`.
        If not found, return the default.
        """
        try:
            return self.__getattr__(attr)
        except (KeyError, AttributeError):
            return default or None

    def get_from(self, path: str, /):
        """Get the value associated from the specified path.

        Paths specs ($ is required):
            $.root_attr
            $.normalised_attr.get_value_from_this_second_attr
            $.some_list[1].attr_from_dixt_object_inside_some_list
        """
        if not isinstance(path, str):
            raise TypeError(f'Invalid path: {path}')
        if not path.startswith('$.'):
            raise ValueError(f'Invalid path: {path}')
        return eval(f"{path.replace('$', 'self')}")

    def is_submap_of(self, other: Union[Mapping, IterableKeyValuePairs]):
        """Evaluate if all of this object's keys and values
        are equal to the other, recursively.
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

    def is_supermap_of(self, other: Union[Mapping, IterableKeyValuePairs]):
        """Evaluate if all of the other object's keys and values
        are equal to this object, recursively.
        """
        return Dixt(other).is_submap_of(self)

    def items(self):
        """Return a set-like object providing a view
        to this object's key-value pairs.
        """
        return ItemsView(self.__dict__['data'])

    def json(self):
        """Convert this object to JSON string."""
        return json.dumps(self.dict())

    def keys(self):
        """Return a set-like object providing a view
        to this object's keys.
        """
        return KeysView(self.__dict__['data'])

    def pop(self, attr, default=...):
        """Get the value of the attribute, then remove the entry.

        :param attr: The attribute to get.
        :param default: Will be returned if attribute is not found.
        :raises AttributeError: If attribute is not found
                                and default value is not specified.
        """
        if retval := self.get(attr):
            self.__delattr__(attr)
            return retval
        if default == Ellipsis:
            raise AttributeError(f"Dixt object has no attribute '{attr}'")
        return default

    def set(self, attr, value, /):
        """Set new or existing `attr` with new `value`.

        :param attr: Name of the attribute to modify.
        :param value: The new value of the attribute.
        """
        self.__setattr__(attr, value)

    def update(self, other: Union[Mapping, IterableKeyValuePairs] = (), /, **kwargs):
        """Update this object from another Mapping objects (e.g., dict, Dixt),
        or from an iterable key-value pairs.
        """
        if not hasattr(other, 'keys'):
            other = _dictify_kvp(other)

        for container in (other, kwargs):
            for k, v in container.items():
                self.__setattr__(k, v)

    def values(self):
        """Return a set-like object providing a view
        to this object's values.
        """
        return ValuesView(self.__dict__['data'])

    @staticmethod
    def from_json(json_str, /):
        """Converts a JSON string to a Dixt object."""
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
