# SPDX-FileCopyrightText: 2021-2026 @github.com/hardistones
# SPDX-License-Identifier: BSD-3-Clause

import pytest
from lxdx import Dixt


class TestAttributeAccess:

    def test_getattr_builtin(self, dixt):
        assert getattr(dixt, 'nonexistent', None) is None

    def test_getattr_dot_notation(self, dixt):
        expected = {'C-D': 1.2,
                    'e': [2, {'g': 9.806}],
                    'f': {'x': None, 'y': [{'p': 5}, [8]]}}

        assert dixt.body == expected
        assert dixt.body.f.x is None
        assert dixt.body.c_d == 1.2

    def test_getattr_dot_notation_using_normalised_keys(self):
        dx = Dixt(**{'Alpha-Bravo': 'ab',
                     'CharlieDelta': 'cd',
                     'echo foxtrot': 'ef'})
        assert dx.alpha_bravo == 'ab'
        assert dx.charliedelta == 'cd'
        assert dx.echo_foxtrot == 'ef'

    def test_getattr_dot_notation_raises_error_when_nonexistent(self, dixt):
        with pytest.raises(AttributeError):
            dixt.nonexistent

    def test_setattr_builtin_function(self, dixt):
        setattr(dixt, 'name', 'value')
        assert dixt.name == 'value'
        assert dixt['name'] == 'value'

    def test_setattr_builtin_function_should_normalise_attribute_name(self, dixt):
        setattr(dixt, 'My Name', 'value')
        assert dixt.my_name == 'value'
        assert dixt['My Name'] == 'value'

    def test_setattr_dot_notation_existing_attributes(self, dixt):
        dixt.extra = value = 'new value'
        assert dixt.extra == value
        assert dixt['extra'] == value

        dixt.body.c_d = value = 'string'
        assert dixt.body.c_d == value
        assert dixt.body['C-D'] == value

    def test_setattr_dot_notation_nonexistent_attributes(self, dixt):
        dixt.name = value = 123456
        assert 'name' in dixt
        assert dixt.name == value
        assert dixt['name'] == value

    def test_setattr_dot_notation_takes_the_attribute_verbatim(self, dixt):
        dixt.something_new = 123456
        assert 'something_new' in dixt
        assert 'something-new' not in dixt
        assert 'something new' not in dixt
        assert 'Something-New' not in dixt

    def test_setattr_dot_notation_another_dict_or_dixt(self, dixt):
        dixt.extra = {'alpha': 1}
        assert isinstance(dixt.extra, Dixt)
        assert dixt.extra == Dixt(alpha=1)
        assert dixt.extra.alpha == 1

        dixt.extra = Dixt(alpha=1)
        assert dixt.extra == {'alpha': 1}
        assert dixt.extra.alpha == 1

    def test_setattr_setitem_hype_when_value_is_dict_or_dixt(self):
        dxa = Dixt(a=1, b={'bb': 2})
        dxa.c = {'c-c': 3}
        dxb = Dixt(a=1, b=Dixt(bb=2))
        dxb['c'] = {'c-c': 3}
        assert dxa == dxb
        assert dxa.c.c_c == 3
        assert dxb.c.c_c == 3

    def test_delattr(self, dixt):
        del dixt.headers.content_type
        assert 'Content-Type' not in dixt.headers
        assert 'content_type' not in dixt.headers
        del dixt.headers
        del dixt.body
        assert dixt == {'extra': 'info'}

    def test_delattr_should_be_case_insensitive(self, dixt):
        del dixt.EXTRA
        assert 'extra' not in dixt

    def test_delattr_raises_error_attribute_is_not_found(self, dixt):
        with pytest.raises(KeyError):
            del dixt.not_found

    @pytest.mark.parametrize('key', ['A-B', 'a_b'])
    def test_delete_hidden_key_cleans_normalised_metadata(self, key):
        dx = Dixt({'A-B': 1})
        dx.keymeta('A-B', hidden=True)
        del dx[key]
        assert dx.whats_hidden() == ()
        assert dx.__keymap__ == {}
        assert dx.__keymeta__ == {}
        with pytest.raises(KeyError):
            dx['A-B']
