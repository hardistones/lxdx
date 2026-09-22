# SPDX-FileCopyrightText: 2021-2026 @github.com/hardistones
# SPDX-License-Identifier: BSD-3-Clause

import pytest
from lxdx import Dixt


class TestItemAccess:

    @pytest.mark.parametrize('key', [[], {}])
    def test_unhashable_key_raises_key_error(self, key):
        with pytest.raises(KeyError) as exc:
            Dixt(a=1)[key]
        assert exc.value.args == (key,)
        assert isinstance(exc.value.__cause__, TypeError)

    def test_getitem_gets_value_of_existing_items(self, dixt):
        assert dixt['headers']['Accept-Encoding'] == 'gzip'
        assert dixt['body']['f']['x'] is None
        assert dixt['extra'] == 'info'

    def test_getitem_key_that_is_implicit_false(self):
        assert Dixt({0: 1})[0] == 1
        assert Dixt({False: 1})[False] == 1
        assert Dixt({(): 1})[()] == 1

    def test_ellipsis_key_supports_lookup_update_and_delete(self):
        dx = Dixt({Ellipsis: 1})
        assert dx[Ellipsis] == dx.getx(Ellipsis) == 1
        dx[Ellipsis] = 2
        dx.keymeta(Ellipsis, hidden=True)

        assert dx.pop(Ellipsis) == 2
        assert dx.whats_hidden() == ()
        assert dx.__keymap__ == dx.__keymeta__ == {}
        with pytest.raises(KeyError):
            dx[Ellipsis]

    def test_getitem_raises_key_error_when_missing(self, dixt):
        with pytest.raises(KeyError):
            dixt['missing_attribute']
        with pytest.raises(KeyError):
            dixt[False]
        with pytest.raises(KeyError):
            dixt[0]
        with pytest.raises(KeyError):
            dixt[()]

    def test_setitem_existing_attributes(self):
        dx = Dixt(a=1, b=2, c=3)
        dx['a'] *= 100
        dx['b'] = dx['a'] + dx['c']
        assert dx == {'a': 100, 'b': 103, 'c': 3}

        dx = Dixt({1: 1, 2: 2, 3: 3})
        dx[1] *= 100
        dx[2] = dx[1] + dx[3]
        assert dx == {1: 100, 2: 103, 3: 3}

    def test_setitem_raises_error_when_adding_similarly_formatted_keys(self, dixt):
        with pytest.raises(KeyError):
            dixt.headers['content_type'] = 'new-type'

        # must not raise error
        dixt.headers.content_type = 'type-one'
        dixt.headers['Content-Type'] = 'type-two'

    def test_setitem_nonexistent_attributes(self):
        dx = Dixt()
        dx['a'] = 1
        dx['b'] = (2, 3)
        dx[123] = "cc"
        assert dx == {'a': 1, 'b': (2, 3), 123: 'cc'}

    def test_delitem(self, dixt):
        del dixt['headers']
        assert 'headers' not in dixt

        assert 'C-D' in dixt.body
        assert 'c_d' in dixt.body.__keymap__
        del dixt.body['C-D']
        assert 'C-D' not in dixt.body
        assert 'c_d' not in dixt.body.__keymap__

        del dixt['body']
        assert dixt == Dixt(extra='info')

    def test_delitem_should_be_case_insensitive(self, dixt):
        dixt['A'] = 'A'
        del dixt['a']
        assert 'A' not in dixt

        del dixt['Extra']
        assert 'extra' not in dixt

    def test_delitem_raises_error_item_is_not_found(self, dixt):
        with pytest.raises(KeyError):
            del dixt['not-found']

    @pytest.mark.parametrize('data', [
        {'A-B': 1, 'a_b': 2},
        {'a_b': 2, 'A-B': 1},
    ])
    def test_delete_alias_owner_preserves_remaining_alias(self, data):
        """Reassign a deleted owner's alias to the surviving original key."""
        dx = Dixt(data)

        del dx['a_b']

        assert dx.dict() == {'A-B': 1}
        assert dx.a_b == 1
        assert dx['a_b'] == 1

    def test_deleting_a_hidden_item(self):
        dx = Dixt(a=1, b=2)
        dx.keymeta('a', hidden=True)
        reference = dx

        del dx['a']

        assert dx == dx.dict() == {'b': 2}
        assert dx.b == dx['b'] == 2
        assert dx is reference

        dx['a'] = 3
        assert dx.whats_hidden() == ()
        assert dx == dx.dict() == {'a': 3, 'b': 2}

    @pytest.mark.parametrize('key', ['items', 'get', 'clear'])
    def test_missing_method_name_is_not_a_mapping_entry(self, key):
        dx = Dixt()
        assert key not in dx
        with pytest.raises(KeyError):
            dx[key]
