# SPDX-FileCopyrightText: 2021-2026 @github.com/hardistones
# SPDX-License-Identifier: BSD-3-Clause

import pytest
from collections.abc import KeysView, ValuesView, ItemsView
from lxdx import Dixt


class TestCollectionOps:

    def test_len(self, dixt):
        assert len(dixt) == 3
        assert len(dixt.headers) == 2
        assert len(dixt.body) == 3
        assert len(dixt.body.f.y) == 2

    def test_iter(self, dixt):
        assert isinstance(iter(dixt), type(iter({}.keys())))

    def test_keys(self, dixt):
        keys = dixt.keys()
        assert isinstance(keys, KeysView)
        assert list(keys) == ["headers", "body", "extra"]

    def test_values(self, dixt):
        values = dixt.headers.values()
        assert isinstance(values, ValuesView)
        assert list(values) == ["gzip", "application/json"]

    def test_items(self, dixt):
        items = dixt.headers.items()
        assert isinstance(items, ItemsView)
        assert list(items) == [('Accept-Encoding', 'gzip'), ('Content-Type', 'application/json')]

    def test_collection_views_track_hidden_flag_changes(self):
        """Keep length, iteration, and existing views in sync with hidden flags."""
        dx = Dixt(visible=1, secret=2)
        keys, items, values = dx.keys(), dx.items(), dx.values()

        for hidden, expected in [
            (True, {'visible': 1}),
            (False, {'visible': 1, 'secret': 2}),
        ]:
            dx.keymeta('secret', hidden=hidden)
            assert len(dx) == len(expected)
            assert list(dx) == list(expected)
            assert list(keys) == list(expected.keys())
            assert list(items) == list(expected.items())
            assert list(values) == list(expected.values())

    def test_pop(self, dixt):
        assert dixt.pop('extra') == 'info'
        assert 'extra' not in dixt
        assert 'extra' not in dixt.__keymap__
        with pytest.raises(AttributeError):
            dixt.pop('extra')
        assert dixt.pop('extra', 'default-value') == 'default-value'

    @pytest.mark.parametrize('key', ['items', 123], ids=['method-name', 'integer'])
    def test_pop_returns_default_for_missing_method_name_or_integer_key(self, key):
        """Return the default instead of raising for absent methods or integers."""
        dx = Dixt()
        default = object()
        assert dx.pop(key, default) is default
        assert dx.dict() == {}

    @pytest.mark.parametrize('original_key, lookup_key', [
        ('Secret-Key', 'Secret-Key'),
        ('Secret-Key', 'secret_key'),
        ('items', 'items'),
        (123, 123),
    ], ids=['original-key', 'alias', 'method-name', 'integer'])
    def test_pop_removes_hidden_entry_and_metadata(self, original_key, lookup_key):
        """Pop hidden entries through supported key forms and remove their metadata."""
        dx = Dixt({original_key: 2, 'visible': 1})
        dx.keymeta(original_key, hidden=True)

        assert dx.pop(lookup_key) == 2
        assert dx.dict() == {'visible': 1}
        assert dx.whats_hidden() == ()
        assert dx.__keymeta__ == {}
        with pytest.raises(KeyError):
            dx[original_key]

    def test_clear(self, dixt):
        dixt.headers.clear()
        assert dixt.headers == {}
        assert dixt.headers == Dixt()
        assert dixt.headers.__keymap__ == {}
        dixt.body.clear()
        assert dixt == {'headers': {}, 'body': {}, 'extra': 'info'}
        assert dixt == Dixt(headers=Dixt(), body=Dixt(), extra='info')
        assert dixt.body.__keymap__ == {}

    def test_clear_removes_hidden_values_and_metadata(self):
        dx = Dixt(visible=1, hidden=2)
        dx.keymeta('hidden', hidden=True)
        dx.clear()
        assert dx == {}
        assert dx.whats_hidden() == ()
        assert dx.__keymap__ == {}
        assert dx.__keymeta__ == {}
        with pytest.raises(KeyError):
            dx['hidden']

    def test_clear_removes_entries_when_every_key_is_hidden(self):
        """Clear an apparently empty mapping and release its hidden key aliases."""
        dx = Dixt({'Secret-Key': 1})
        dx.keymeta('Secret-Key', hidden=True)
        assert len(dx) == 0

        dx.clear()

        assert dx.whats_hidden() == ()
        with pytest.raises(KeyError):
            dx['Secret-Key']
        dx['secret_key'] = 2
        assert dx.dict() == {'secret_key': 2}

    def test_reinsert_after_clear_is_visible(self):
        dx = Dixt(a=1)
        dx.keymeta('a', hidden=True)
        dx.clear()
        dx['a'] = 2
        assert dx.dict() == {'a': 2}
        assert dx['a'] == 2
        assert dx.whats_hidden() == ()

    def test_popitem(self):
        """Testing inherited function from MutableMapping."""
        dx = Dixt(a=1, b=2, c=3)
        # not LIFO as with dict
        assert dx.popitem() == ('a', 1)

    def test_setdefault_sets_value_to_nonexistent_key_from_default_value(self, dixt):
        """Testing inherited function from MutableMapping."""
        assert 'extra-extra' not in dixt
        dixt.setdefault('extra-extra', 'extra-value')
        assert dixt.extra_extra == 'extra-value'

        assert 'to-exist' not in dixt
        dixt.setdefault('to-exist')
        assert dixt.to_exist is None

    def test_setdefault_does_not_overwrite_existing_value(self, dixt):
        dixt.setdefault('extra', 'another-value')
        assert dixt.extra == 'info'

    @pytest.mark.parametrize('key', ['items', 'get', 'clear'])
    def test_setdefault_inserts_missing_method_name(self, key):
        dx = Dixt()
        assert dx.setdefault(key, 42) == 42
        assert dx[key] == 42
        assert key in dx
