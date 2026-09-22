# SPDX-FileCopyrightText: 2021-2026 @github.com/hardistones
# SPDX-License-Identifier: BSD-3-Clause

import pytest
from lxdx import Dixt


class TestKeymeta:

    def test_hidden_flag(self, dixt, dict_equiv):
        dixt.keymeta('body', hidden=True)

        assert 'body' in dixt.whats_hidden()
        assert 'body' not in dixt
        assert dixt != dict_equiv

        assert len(dixt) == 2
        assert list(dixt.keys()) == ['headers', 'extra']

        body = {'f': {'x': None}}
        assert not dixt.is_supermap_of({'body': body})
        dx = dixt.body | {'something': 'new'}
        assert dx.something == 'new'
        assert dx.is_supermap_of(body | {'something': 'new'})

    def test_flag_a_non_str_key(self, dixt):
        dixt[123] = '123'
        dixt.keymeta(123, hidden=True)
        assert 123 not in dixt

    def test_whats_hidden_tracks_original_keys_on_flag_changes(self):
        """Report original spellings when flags are set or reset through aliases."""
        dx = Dixt({'Secret-Key': 1, 'group_name': 2})
        dx.keymeta('secret_key', 'group_name', hidden=True)
        assert set(dx.whats_hidden()) == {'Secret-Key', 'group_name'}

        dx.keymeta('secret_key', hidden=False)

        assert dx.whats_hidden() == ('group_name',)
        assert 'Secret-Key' in dx
        assert dx.keymeta('group_name') == {'group_name': {'hidden': True}}

    def test_hidden_flag_can_still_get_and_set_items(self, dixt):
        dixt.headers.keymeta('Accept-Encoding', hidden=True)
        dixt.headers.accept_encoding = 'zip'
        assert dixt.headers.accept_encoding == 'zip'

        dixt.keymeta('headers', hidden=True)
        dixt.headers['Accept-Encoding'] = 'tar'
        assert dixt.headers['Accept-Encoding'] == 'tar'

    def test_able_to_flag_items_of_hidden_items(self, dixt):
        dixt.keymeta('body', hidden=True)
        dixt.body.keymeta('e', hidden=True)
        assert 'body' in dixt.whats_hidden()
        assert 'e' in dixt.body.whats_hidden()

    def test_unsupported_flags_bypassed(self, dixt):
        dixt.keymeta('body', whatever='value')
        assert 'body' not in dixt.__keymeta__

        dixt.keymeta('extra', hidden=True, whatever='value')
        assert 'whatever' not in dixt.__keymeta__['extra']
        assert 'hidden' in dixt.__keymeta__['extra']

    def test_no_flags_returns_metadata_of_keys(self, dixt):
        dixt.keymeta('extra', 'body', hidden=True)

        expected = {'extra': {'hidden': True}}
        assert dixt.keymeta('extra') == expected

        expected['body'] = {'hidden': True}
        assert dixt.keymeta('extra', 'body') == expected

    def test_remove_from_keymeta_a_deleted_flagged_item(self, dixt):
        dixt.keymeta('extra', hidden=True)
        del dixt.extra
        assert 'extra' not in dixt.__data__
        assert 'extra' not in dixt.__keymeta__
        assert 'extra' not in dixt.__hidden__

    def test_cleanup_of_metadata_on_reset_value(self, dixt):
        dixt.keymeta('body', hidden=True)
        assert 'hidden' in dixt.__keymeta__['body']
        dixt.keymeta('body', hidden=False)  # reset value
        assert 'body' not in dixt.__keymeta__

    @pytest.mark.parametrize('data', [
        {'A-B': 'secret', 'a_b': 'public'},
        {'a_b': 'public', 'A-B': 'secret'},
    ])
    def test_hidden_flag_targets_original_key_when_alias_collides(self, data):
        """Hide the requested original key while leaving its collision visible."""
        dx = Dixt(data)

        dx.keymeta('A-B', hidden=True)

        assert dx.whats_hidden() == ('A-B',)
        assert dx.dict() == {'a_b': 'public'}
        assert dx['A-B'] == 'secret'

        dx.keymeta('A-B', hidden=False)
        assert dx.whats_hidden() == ()
        assert dx.dict() == data

    @pytest.mark.parametrize('first, second', [('A-B', 'a_b'), ('a_b', 'A-B')])
    def test_colliding_original_keys_have_independent_hidden_flags(self, first, second):
        dx = Dixt({'A-B': 1, 'a_b': 2})
        dx.keymeta(first, hidden=True)
        assert dx.keymeta(second) == {'a_b': {}}
        assert dx.keymeta(first) == {'a_b': {'hidden': True}}

        dx.keymeta(second, hidden=True)
        dx.keymeta(first, hidden=False)
        del dx[first]

        assert dx.whats_hidden() == (second,)
        assert dx.keymeta(second) == {'a_b': {'hidden': True}}
        dx.keymeta(second, hidden=False)
        assert dx.a_b == dx[second]

    @pytest.mark.parametrize('hidden', [False, True])
    @pytest.mark.parametrize('data', [
        {'A-B': 1, 'a_b': 2},
        {'a_b': 2, 'A-B': 1},
    ])
    def test_setting_same_hidden_flag_is_idempotent(self, hidden, data):
        dx = Dixt(data)
        dx.keymeta('a_b', hidden=hidden)
        dx.keymeta('a_b', hidden=hidden)
        assert dx['A-B'] == 1
        assert dx['a_b'] == dx.a_b == 2
        assert 'A-B' in dx
        assert dx.whats_hidden() == (('a_b',) if hidden else ())
        assert ('a_b' in dx) is (not hidden)
        assert dx.dict() == ({'A-B': 1} if hidden else data)
        assert dx.__keymap__ == {'a_b': 'a_b'}

    def test_raises_error_when_keys_are_not_found(self, dixt):
        with pytest.raises(KeyError):
            dixt.keymeta('ghost')

    def test_hidden_flag_raises_error_when_invalid_value(self, dixt):
        with pytest.raises(TypeError):
            dixt.keymeta('extra', hidden=2)
