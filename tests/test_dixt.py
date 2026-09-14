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
import pytest

from collections import ChainMap, OrderedDict
from collections.abc import KeysView, ValuesView, ItemsView

from lxdx import Dixt
from lxdx.dixt import DixtException  # noqa


INVALID_QUERIES = {
    IndexError: [
        '$.body.e[100]',
        '$.body.e[-10]',
    ],
    KeyError: [
        '$.extra.info',
        '$.not_heading.nonexistent',
        '$.headers.nonexistent',
        '$.nonexistent[0]',
        '$.body[1:]',
    ],
    TypeError: [123, object()],
    ValueError: [
        '',
        'any.string',
        '$',
        '$.',
        '$..',
        '$[0]',
        'a.b[0]',
        '$.headers[2',
        '$.body.f[]',
    ],
}

VALID_QUERIES = [
    ('$.headers.content_type', 'application/json'),
    ('$.extra', 'info'),
    ('$.body.e[0]', 2),
    ('$.body.e[-2]', 2),
    ('$.body.e.[0]', 2),
    ('$.body.e.[-2]', 2),
    ('$.body.e[1].g', 9.806),
    ('$.body.f.y[1][0]', 8),
    ('$.body.e[1:]', [{'g': 9.806}]),
    ('$.body.e.[1:]', [{'g': 9.806}]),
]


class TestInit:

    def test_invalid_data(self):
        for data in [
            "string",
            ["non-key-value pair"],
            [('a', 'b'), 'c']
        ]:
            with pytest.raises(DixtException):
                Dixt(data)

    def test_accepts_key_value_pairs(self):
        dx = Dixt([(1, 100), ('2', '200')])
        assert dx == {1: 100, '2': '200'}

        dx = Dixt([(1, 100), ('2', '200')], a='a', b='b')
        assert dx == {1: 100, '2': '200', 'a': 'a', 'b': 'b'}

        # limitation:
        # due to the __new__ function using the zip iterator,
        # data must be wrapped first
        dx = Dixt(list(zip([1, '2'], [100, '200'])))
        assert dx == {1: 100, '2': '200'}

        dx = Dixt(tuple(zip([1, '2'], [100, '200'])))
        assert dx == {1: 100, '2': '200'}

        dx = Dixt(dict(zip([1, '2'], [100, '200'])))
        assert dx == {1: 100, '2': '200'}

    def test_accepts_another_dixt_object(self):
        dx = Dixt({1: 1})
        assert Dixt(dx) == {1: 1}

    def test_accepts_iterators(self):
        dx = Dixt(zip(['a', 'b'], [1, 2]))
        assert dx == {'a': 1, 'b': 2}

    def test_should_not_change_data_type(self):
        dx = Dixt(a=(1, 2, 3))
        assert dx == {'a': (1, 2, 3)}

        dx = Dixt(a={1, 2, 3})
        assert dx == {'a': {1, 2, 3}}

    def test_accepts_kwargs(self):
        dx = Dixt(alpha='α', beta='β', gamma='γ')
        assert dx == {'alpha': 'α', 'beta': 'β', 'gamma': 'γ'}
        assert dx.alpha == 'α'

        dx = Dixt(a_b='a b', cd=1.2, e=[2, 4], f={'x': 3, 'y': [{'p': 5}, {'q': 7}]})
        assert dx == {'a_b': 'a b', 'cd': 1.2, 'e': [2, 4], 'f': {'x': 3, 'y': [{'p': 5}, {'q': 7}]}}

    def test_kwargs_updates_data(self):
        dx = Dixt({'alpha': 'α', 'beta': 'β'})
        assert dx == {'alpha': 'α', 'beta': 'β'}

        dx = Dixt({'alpha': 'α', 'beta': 'β'}, gamma='γ', beta='veeta')
        assert dx == {'alpha': 'α', 'beta': 'veeta', 'gamma': 'γ'}

        dx = Dixt(alpha='α', beta='β')
        assert Dixt(dx, beta='beta') == {'alpha': 'α', 'beta': 'beta'}


class TestEquality:

    def test_dixt_compared_to_dixt(self):
        a = Dixt(x=1, y=2, z=3)
        b = Dixt(x=1, y=2, z=3)

        c = Dixt(**{
            'An-Attr': [1, '2', {'3': 3.14}, 4],
            'Bn-Bttr': {'X': 'x', 'c': {'Y': 'y', 'Z': 'z'}}
        })

        d = Dixt({
            'An-Attr': [1, '2', {'3': 3.14}, 4],
            'Bn-Bttr': {'c': {'Z': 'z', 'Y': 'y'}, 'X': 'x'}
        })

        assert a == b
        assert c == d
        assert b != c

    def test_dixt_compared_to_dict(self):
        dx = Dixt(x=1, y=2, z=3)
        assert dx == {'x': 1, 'y': 2, 'z': 3}

    def test_dixt_compared_to_ordered_dict(self):
        dx = Dixt(x=1, y=2)
        assert dx == OrderedDict((('y', 2), ('x', 1)))

    def test_dixt_compared_to_iterable_key_value_pairs(self):
        dx = Dixt(x=1, y=2)
        assert dx == [('x', 1), ('y', 2)]
        assert dx == (('y', 2), ('x', 1))

    def test_compare_to_other_types(self, dixt):
        assert dixt != 'string'
        assert dixt != 1234
        assert dixt != {'set'}
        assert dixt != ['not', 'key-value', 'pair']

    def test_not_operator_return_false_when_empty_and_true_otherwise(self, dixt):
        assert not Dixt()
        assert not (not dixt)
        assert dixt
        assert not Dixt()

    def test_or_operator_should_choose_the_second_option_when_first_is_empty(self, dixt):
        assert (Dixt() or 'else') == 'else'
        assert (Dixt() or {1: 1}) == {1: 1}
        assert (Dixt() or dixt) == dixt


class TestUnionOperator:

    def test_arg_is_dict(self):
        result = Dixt() | {}
        assert isinstance(result, Dixt)
        assert result == {}
        result = Dixt() | {1: {2: 2}}
        assert isinstance(result, Dixt)
        assert result == {1: {2: 2}}
        assert Dixt({1: 1}) | {2: 2} == {2: 2, 1: 1}

    def test_arg_is_dixt(self):
        result = Dixt({1: 1}) | Dixt()
        assert isinstance(result, Dixt)
        assert result == {1: 1}
        result = Dixt() | Dixt()
        assert isinstance(result, Dixt)
        assert result == {}
        assert Dixt() | Dixt({2: 2}) == {2: 2}
        assert Dixt({1: 1}) | Dixt({1: 100, 2: 2}) == {1: 100, 2: 2}

        result = {1: 1} | Dixt()
        assert isinstance(result, dict)
        assert result == {1: 1}
        result = {} | Dixt()
        assert isinstance(result, dict)
        assert result == {}
        assert {} | Dixt({2: 2}) == {2: 2}
        assert {1: 1} | Dixt({2: 2}) == {1: 1, 2: 2}

    def test_first_arg_is_iterable_key_value_pairs(self):
        """This will trigger __ror__"""
        result = [(1, 1), (2, 2)] | Dixt()
        assert isinstance(result, dict)
        assert result == {1: 1, 2: 2}
        result = [(1, 1), (2, 2)] | Dixt({2: 4})
        assert isinstance(result, dict)
        assert result == {1: 1, 2: 4}

    def test_in_place_operation(self):
        dx = Dixt()
        dx |= {}
        assert dx == {}
        dx |= {1: 1}
        assert dx == {1: 1}
        dx |= [(1, 100), (2, 2)]
        assert dx == {1: 100, 2: 2}

    def test_raises_error_for_non_supported_types_or_values(self):
        arguments = [
            'string',
            1234,
            ['list', 'not', 'key-value', 'pair'],
            {'this', 'is', 'set'}
        ]
        dx = Dixt()
        for arg in arguments:
            with pytest.raises(Exception):
                dx | arg   # __or__
            with pytest.raises(Exception):
                arg | dx   # __ror__
            with pytest.raises(Exception):
                dx |= arg  # __ior__


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


class TestGetx:

    def test_returns_value_of_existing_attributes(self, dixt):
        headers = {'Accept-Encoding': 'gzip',
                   'Content-Type': 'application/json'}
        assert dixt.getx('headers') == headers
        assert dixt.headers.getx('Accept-Encoding') == 'gzip'
        assert dixt.body.f.getx('x', 'y') == (None, [{'p': 5}, [8]])

    def test_returns_default_value_of_nonexistent_attributes(self, dixt):
        assert dixt.getx('ghost', default=-1) == -1
        assert dixt.headers.getx('Lost-Item', default=object) == object

        assert dixt.getx('ghost', default=[1]) == 1
        assert dixt.body.f.getx('x', default='X') is None
        assert dixt.getx('ghost', 'invisible', default=2) == (2, 2)
        assert dixt.getx('ghost', 'invisible', default=[4, 5]) == (4, 5)

    def test_raises_error_when_defaults_dont_match_with_attrs_len(self, dixt):
        with pytest.raises(ValueError):
            dixt.getx('ghost', 'invisible', default=(1, 2, 3))

        with pytest.raises(ValueError):
            dixt.getx('ghost', 'invisible', default=[3])


class TestItemAccess:

    def test_getitem_gets_value_of_existing_items(self, dixt):
        assert dixt['headers']['Accept-Encoding'] == 'gzip'
        assert dixt['body']['f']['x'] is None
        assert dixt['extra'] == 'info'

    def test_getitem_key_that_is_implicit_false(self):
        assert Dixt({0: 1})[0] == 1
        assert Dixt({False: 1})[False] == 1
        assert Dixt({(): 1})[()] == 1

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


class TestUpdate:

    def test_value_is_forced_to_be_none(self):
        dx = Dixt(a=1, b=2)
        dx.update(None)
        assert dx == Dixt(a=1, b=2)

    def test_value_is_dict(self):
        dx = Dixt(a=1, b=2)
        dx.update({'c': 3})
        assert dx == Dixt(a=1, b=2, c=3)

    def test_value_is_dixt(self):
        dx = Dixt(a=1, b=2)
        dx.update(Dixt(d=4))
        assert dx == Dixt(a=1, b=2, d=4)

    def test_value_is_in_kwargs_only(self):
        dx = Dixt(a=1, b=2)
        dx.update(x=3, y=4)
        assert dx == Dixt(a=1, b=2, x=3, y=4)

    def test_value_is_iterable_key_value_pairs(self):
        dx = Dixt(a=1, b=2)
        dx.update((('x', 24), ('y', 25)))
        assert dx == Dixt(a=1, b=2, x=24, y=25)

    def test_combination_of_dict_and_kwargs(self):
        dx = Dixt(a=1, b=2)
        dx.update({'c': 3}, d={'dd': 44})
        assert dx == Dixt(a=1, b=2, c=3, d=Dixt(dd=44))

    def test_combination_of_dixt_and_kwargs(self):
        dx = Dixt(a=1, b=2)
        dx.update(Dixt(e=5, f=Dixt(g=7)))
        assert dx == Dixt(a=1, b=2, e=5, f=Dixt(g=7))

    def test_combination_of_key_value_pairs_and_kwargs(self):
        dx = Dixt(a=1, b=2)
        dx.update((('e', 5),), x=[1, 2])
        assert dx == {'a': 1, 'b': 2, 'e': 5, 'x': [1, 2]}

    def test_raises_error_argument_is_not_iterable_key_value_pairs(self):
        for arg in ['string', ['list', 1], 1234]:
            with pytest.raises((ValueError, TypeError)):
                Dixt(a=1, b=2).update(arg, x=[1, 2])


class TestContains:

    def test_contains(self, dixt):
        assert 'extra' in dixt
        assert dixt.contains(*['headers', 'body', 'extra'])
        assert dixt.contains('headers', 'body', 'extra')
        assert 'ghost' not in dixt
        assert not dixt.contains('headers', 'body', 'ghost')

    def test_must_be_case_sensitive(self):
        dx = Dixt({1: 100, 2: 200, 'A-a': 'aa'})
        assert 1 in dx
        assert 'A-a' in dx
        assert 'a-a' not in dx
        assert dx.contains(2, 1)
        assert not dx.contains('A-a', 'a-a')

    def test_assert_all_is_false(self, dixt):
        result = dixt.contains('headers', 'body', assert_all=False)
        assert isinstance(result, tuple)
        assert all(result)

        result = dixt.contains('headers', 'ghost', assert_all=False)
        assert isinstance(result, tuple)
        assert result == (True, False)

        result = dixt.contains('nonexistent', assert_all=False)
        assert result == (False,)


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

    def test_pop(self, dixt):
        assert dixt.pop('extra') == 'info'
        assert 'extra' not in dixt
        assert 'extra' not in dixt.__keymap__
        with pytest.raises(AttributeError):
            dixt.pop('extra')
        assert dixt.pop('extra', 'default-value') == 'default-value'

    def test_clear(self, dixt):
        dixt.headers.clear()
        assert dixt.headers == {}
        assert dixt.headers == Dixt()
        assert dixt.headers.__keymap__ == {}
        dixt.body.clear()
        assert dixt == {'headers': {}, 'body': {}, 'extra': 'info'}
        assert dixt == Dixt(headers=Dixt(), body=Dixt(), extra='info')
        assert dixt.body.__keymap__ == {}

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


class TestConversion:

    def test_str_repr(self):
        dx = Dixt(a=1, b=Dixt(c=3))
        assert str(dx) == "{'a': 1, 'b': {'c': 3}}"
        assert repr(dx) == "{'a': 1, 'b': {'c': 3}}"

        dx = {'alpha': Dixt(a='a'), 'omega': Dixt(o='o')}
        assert str(dx) == "{'alpha': {'a': 'a'}, 'omega': {'o': 'o'}}"

    def test_dict_should_return_dict_object_with_non_normalised_keys(self, dixt, dict_equiv):
        assert dixt.dict() == dict_equiv
        _assert_obj_tree_has_no_dixt_object(dixt.dict())

        dixt.extra = Dixt(a=1, b=[Dixt(c=3)])
        _assert_obj_tree_has_no_dixt_object(dixt.dict())

    def test_json_conversion_to_json_format(self, dixt, dict_equiv):
        json_equivalent = json.dumps(dict_equiv)
        assert dixt.json() == json_equivalent

    def test_from_json(self, dict_equiv):
        json_string = json.dumps(dict_equiv)
        dx = Dixt.from_json(json_string)
        assert dx == dict_equiv


class TestNestedAccess:

    def test_traversals_with_nested_objects(self, dixt):
        assert dixt.body.e[1] == {"g": 9.806}
        assert dixt['body']['e'][1] == {"g": 9.806}

        assert dixt.body.e[1].g == 9.806
        assert dixt['body']['e'][1]['g'] == 9.806

        assert dixt.body.f.y[1] == [8]
        assert dixt['body']['f']['y'][1] == [8]

        assert dixt.body.f.y[1][0] == 8
        assert dixt['body']['f']['y'][1][0] == 8

    def test_operations_on_nested_objects(self, dixt):
        dixt.body.f.y[1].extend(['σ', 'φ', 'θ'])
        assert dixt.body.f.y[1] == [8, 'σ', 'φ', 'θ']

        dixt.body.e[1] = {'del-ta': 'd'}
        # AttributeError: Since the assignment is handled by the list object,
        #                 the dict is not converted to a Dixt object.
        #                 Should wrap with Dixt first
        #                 before appending/adding to the list.
        # dixt.body.e[1].del_ta = 'δ'

        dixt.body.e[1] = Dixt({'del-ta': 'δ'})
        assert dixt.body.e[1] == {'del-ta': 'δ'}
        assert dixt.body.e[1].del_ta == 'δ'

    def test_get_from(self, dixt):
        for path, expected_value in VALID_QUERIES:
            assert dixt.get_from(path) == expected_value

    def test_get_from_invalid_path(self, dixt):
        for exc, queries in INVALID_QUERIES.items():
            for path in queries:
                with pytest.raises(exc):
                    dixt.get_from(path)

    def test_set_by_path(self, dixt):
        dixt.set_by_path('$.headers.content_type', 'application/text')
        assert dixt['headers']['Content-Type'] == 'application/text'

        dixt.set_by_path('$.headers.["Content-Type"]', 'application/json')
        assert dixt['headers']['Content-Type'] == 'application/json'

        dixt.set_by_path('$.body.e[0]', 22)
        assert dixt['body']['e'][0] == 22
        assert dixt.get_from('$.body.e[0]') == 22

        dixt.set_by_path('$.body.f.x', 'xi')
        assert dixt['body']['f']['x'] == 'xi'
        assert dixt.get_from('$.body.f.x') == 'xi'

        dixt.set_by_path('$.body.f.y[0].p', 55)
        assert dixt['body']['f']['y'][0]['p'] == 55
        assert dixt.get_from('$.body.f.y[0].p') == 55

        dixt.set_by_path('$.body.f.y[1][0]', 88)
        assert dixt['body']['f']['y'][1][0] == 88
        assert dixt.get_from('$.body.f.y[1][0]') == 88

    def test_set_by_path_invalid_path(self, dixt):
        for exc, queries in INVALID_QUERIES.items():
            for path in queries:
                with pytest.raises(exc):
                    dixt.set_by_path(path, object())


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

    def test_raises_error_when_keys_are_not_found(self, dixt):
        with pytest.raises(KeyError):
            dixt.keymeta('ghost')

    def test_hidden_flag_raises_error_when_invalid_value(self, dixt):
        with pytest.raises(TypeError):
            dixt.keymeta('extra', hidden=2)


class TestMapComparison:

    def test_submap_supermap(self, dixt):
        criteria = [
            {'body': {'e': [2, {'g': 9.806}]}},
            {'body': {'f': {'y': [{'p': 5}, [8]]}}},
            {'extra': 'info'},
            [('extra', 'info')],
            {'headers': {}, 'body': {}}
        ]
        for criterion in criteria:
            assert Dixt(criterion).is_submap_of(dixt)
            assert Dixt(dixt).is_supermap_of(criterion)

        criteria = [
            {1: 1},
            {'extra': ''},
            {'body': {'f': {'y': [None]}}},
            {'headers': {}, 'body': {}, 'nonexistent': {}}
        ]
        for criterion in criteria:
            assert not Dixt(criterion).is_submap_of(dixt)
            assert not Dixt(dixt).is_supermap_of(criterion)

        assert Dixt({1: 1}).is_submap_of([(1, 1), (2, 2)])

        for criterion in ['string', {'set'}, 123, ['non', 'key-value', 'pair']]:
            with pytest.raises(Exception):
                # noinspection PyTypeChecker
                Dixt().is_submap_of(criterion)

    def test_reverse(self):
        alpha = ['jan', 100, 1.1, (3, 5)]
        beta = ['feb', 200, 2.2, (7, 11)]
        dx = Dixt(dict(zip(alpha, beta)))
        rdx = dx.reverse()
        assert rdx == dict(zip(beta, alpha))

    def test_reverse_exclude_hidden_items(self):
        dx = Dixt(a=100, b=200)
        dx.keymeta('a', hidden=True)
        assert dx.reverse() == {200: 'b'}

    @pytest.mark.parametrize("arg", [[1, 2, 3], {2: 200}, {200, 300}])
    def test_reverse_raise_error_on_hashable_values(self, arg):
        with pytest.raises(TypeError):
            Dixt(a=100, b=arg).reverse()


class TestMergeUpdate:

    def test_replaces_non_mapping_value_for_matching_key(self):
        dx = Dixt(a=1, b=2)
        dx.merge_update({'a': 10})
        assert dx == {'a': 10, 'b': 2}

    def test_adds_key_not_in_self(self):
        dx = Dixt(a=1)
        dx.merge_update({'b': 2})
        assert dx == {'a': 1, 'b': 2}

    def test_recursive_mapping_merge_preserves_unmatched_keys(self):
        dx = Dixt(a={'x': 1, 'y': 2})
        dx.merge_update({'a': {'x': 10}})
        assert dx == {'a': {'x': 10, 'y': 2}}

    def test_differs_from_update_which_replaces_nested_mapping(self):
        dx_merge = Dixt(a={'x': 1, 'y': 2})
        dx_update = Dixt(a={'x': 1, 'y': 2})
        dx_merge.merge_update({'a': {'x': 10}})
        dx_update.update({'a': {'x': 10}})
        assert dx_merge == {'a': {'x': 10, 'y': 2}}
        assert dx_update == {'a': {'x': 10}}

    def test_deep_recursive_merge(self):
        dx = Dixt(a={'b': {'c': 1, 'd': 2}, 'e': 3})
        dx.merge_update({'a': {'b': {'c': 10}}})
        assert dx == {'a': {'b': {'c': 10, 'd': 2}, 'e': 3}}

    def test_accepts_dixt_as_other(self):
        dx = Dixt(a=1, b={'x': 1})
        dx.merge_update(Dixt(b={'y': 2}, c=3))
        assert dx == {'a': 1, 'b': {'x': 1, 'y': 2}, 'c': 3}

    def test_mapping_replaced_by_non_mapping(self):
        dx = Dixt(a={'x': 1})
        dx.merge_update({'a': 'string'})
        assert dx == {'a': 'string'}

    def test_non_mapping_replaced_by_mapping(self):
        dx = Dixt(a='string')
        dx.merge_update({'a': {'x': 1}})
        assert dx == {'a': {'x': 1}}

    def test_list_same_length_non_mapping_items_replaced(self):
        dx = Dixt(a=[1, 2, 3])
        dx.merge_update({'a': [10, 20, 30]})
        assert dx == {'a': [10, 20, 30]}

    def test_list_default_replaces_list_with_mapping_items_entirely(self):
        dx = Dixt(a=[{'x': 1, 'y': 2}])
        dx.merge_update({'a': [{'x': 10}]})
        assert dx == {'a': [{'x': 10}]}  # 'y' gone — list replaced wholesale

    def test_list_same_length_mapping_items_merged(self):
        dx = Dixt(a=[{'x': 1, 'y': 2}])
        dx.merge_update({'a': [{'x': 10}]}, recurse_lists=True)
        assert dx == {'a': [{'x': 10, 'y': 2}]}

    def test_list_other_shorter_truncates_self(self):
        dx = Dixt(a=[1, 2, 3])
        dx.merge_update({'a': [10]})
        assert dx == {'a': [10]}

    def test_list_other_shorter_truncates_mapping_items(self):
        dx = Dixt(a=[{'x': 1}, {'y': 2}, {'z': 3}])
        dx.merge_update({'a': [{'x': 10}]})
        assert dx == {'a': [{'x': 10}]}

    def test_list_other_longer_appends_non_mapping_to_self(self):
        dx = Dixt(a=[1, 2])
        dx.merge_update({'a': [10, 20, 30]})
        assert dx == {'a': [10, 20, 30]}

    def test_list_other_longer_appends_mapping_items_as_dixt(self):
        dx = Dixt(a=[{'x': 1}])
        dx.merge_update({'a': [{'x': 10}, {'y': 2}]})
        assert dx == {'a': [{'x': 10}, {'y': 2}]}
        assert isinstance(dx.a[1], Dixt)

    def test_list_mixed_mapping_and_non_mapping_items(self):
        dx = Dixt(a=[{'x': 1}, 2, {'z': 3}])
        dx.merge_update({'a': [{'x': 10}, 20, {'z': 30, 'w': 40}]})
        assert dx == {'a': [{'x': 10}, 20, {'z': 30, 'w': 40}]}

    def test_list_self_non_mapping_other_mapping_replaces_with_dixt(self):
        dx = Dixt(a=[1, 2])
        dx.merge_update({'a': [{'x': 1}, 2]})
        assert dx == {'a': [{'x': 1}, 2]}
        assert isinstance(dx.a[0], Dixt)

    def test_list_self_mapping_other_non_mapping_replaces(self):
        dx = Dixt(a=[{'x': 1}])
        dx.merge_update({'a': [42]})
        assert dx == {'a': [42]}

    def test_normalised_key_matching(self):
        dx = Dixt({'my-key': {'x': 1, 'y': 2}})
        dx.merge_update({'my_key': {'x': 10}})
        assert dx.my_key == {'x': 10, 'y': 2}

    def test_recursive_merge_into_nested_mapping_with_lists(self):
        dx = Dixt(a={'items': [{'x': 1, 'y': 2}, {'z': 3}, {'extra': 99}], 'name': 'foo'})
        dx.merge_update({'a': {'items': [{'x': 10}]}}, recurse_lists=True)
        # 'name' preserved; list shortened to match other; overlapping mapping item merged
        assert dx == {'a': {'items': [{'x': 10, 'y': 2}], 'name': 'foo'}}

        dx = Dixt(a={'items': [{'x': 1, 'y': 2}, {'z': 3}], 'name': 'foo'})
        dx.merge_update({'a': {'items': [{'x': 10}, {'z': 30, 'w': 40}]}}, recurse_lists=True)
        assert dx == {'a': {'items': [{'x': 10, 'y': 2}, {'z': 30, 'w': 40}], 'name': 'foo'}}

    def test_other_is_ordered_dict(self):
        dx = Dixt(a=1, b={'x': 1, 'y': 2})
        dx.merge_update(OrderedDict(b={'x': 10}, c=3))
        assert dx == {'a': 1, 'b': {'x': 10, 'y': 2}, 'c': 3}

    def test_other_is_chain_map(self):
        dx = Dixt(a=1, b={'x': 1})
        dx.merge_update(ChainMap({'b': {'y': 2}}, {'c': 3}))
        assert dx == {'a': 1, 'b': {'x': 1, 'y': 2}, 'c': 3}

    def test_list_recurse_lists_non_mapping_pair_replaced(self):
        # self[0] is Mapping, other[0] is not → replacement; self[1] is not, other[1] is dict → Dixt
        dx = Dixt(a=[{'x': 1, 'y': 2}, 99])
        dx.merge_update({'a': [42, {'new': 1}]}, recurse_lists=True)
        assert dx == {'a': [42, {'new': 1}]}
        assert isinstance(dx.a[1], Dixt)

    def test_list_recurse_lists_other_longer_appends(self):
        dx = Dixt(a=[{'x': 1, 'y': 2}])
        dx.merge_update({'a': [{'x': 10}, {'z': 3}]}, recurse_lists=True)
        assert dx == {'a': [{'x': 10, 'y': 2}, {'z': 3}]}
        assert isinstance(dx.a[1], Dixt)

    @pytest.mark.parametrize('other', ['string', 123, [('a', 2)]])
    def test_raises_error_for_non_mapping(self, other):
        dx = Dixt(a=1)
        with pytest.raises(TypeError):
            dx.merge_update(other)


class TestDiff:

    def test_equal_dicts_return_empty_list(self):
        a = Dixt(x=1, y=2)
        b = Dixt(x=1, y=2)
        assert a.diff(b) == []

    def test_equal_empty_dicts_return_empty_list(self):
        assert Dixt().diff(Dixt()) == []
        assert Dixt().diff({}) == []

    def test_flat_value_differs(self):
        a = Dixt(x=1, y=2)
        b = Dixt(x=1, y=99)
        result = a.diff(b)
        assert len(result) == 1
        self_diff, other_diff = result[0]
        assert self_diff == {'y': 2}
        assert other_diff == {'y': 99}

    def test_key_only_in_self(self):
        a = Dixt(x=1, z=3)
        b = Dixt(x=1)
        result = a.diff(b)
        assert len(result) == 1
        self_diff, other_diff = result[0]
        assert self_diff == {'z': 3}
        assert other_diff == {}

    def test_key_only_in_other(self):
        a = Dixt(x=1)
        b = Dixt(x=1, w=4)
        result = a.diff(b)
        assert len(result) == 1
        self_diff, other_diff = result[0]
        assert self_diff == {}
        assert other_diff == {'w': 4}

    def test_mix_of_differing_and_unique_keys(self):
        a = Dixt(x=1, y=2, z=3)
        b = Dixt(x=1, y=99, w=4)
        result = a.diff(b)
        assert len(result) == 1
        self_diff, other_diff = result[0]
        assert self_diff == {'y': 2, 'z': 3}
        assert other_diff == {'y': 99, 'w': 4}

    def test_nested_equal_keys_are_excluded(self):
        a = Dixt(nested={'p': 10, 'q': 20, 'same': 'val'})
        b = Dixt(nested={'p': 10, 'q': 99, 'same': 'val'})
        result = a.diff(b)
        assert len(result) == 1
        self_diff, other_diff = result[0]
        assert self_diff == {'nested': {'q': 20}}
        assert other_diff == {'nested': {'q': 99}}

    def test_equal_nested_mapping_excluded_entirely(self):
        a = Dixt(x=1, nested={'p': 10, 'same': 'val'})
        b = {'x':1, 'nested':{'p': 10, 'same': 'val'}}
        assert a.diff(b) == []

    def test_deeply_nested_diff(self):
        a = Dixt(a={'b': {'c': 1, 'd': 2}})
        result = a.diff({'a': {'b': {'c': 1, 'd': 99}}})
        assert len(result) == 1
        self_diff, other_diff = result[0]
        assert self_diff == {'a': {'b': {'d': 2}}}
        assert other_diff == {'a': {'b': {'d': 99}}}

    def test_mixed_flat_and_nested_diffs(self):
        a = Dixt(x=1, nested={'p': 10, 'q': 20}, z=3)
        b = Dixt(x=100, nested={'p': 10, 'q': 99}, z=3)
        result = a.diff(b)
        assert len(result) == 2
        flat = next((sd, od) for sd, od in result if 'x' in sd or 'x' in od)
        nested = next((sd, od) for sd, od in result if 'nested' in sd or 'nested' in od)
        sd, od = flat
        assert sd == {'x': 1}
        assert od == {'x': 100}
        sd, od = nested
        assert sd == {'nested': {'q': 20}}
        assert od == {'nested': {'q': 99}}

    def test_mapping_only_in_other_wrapped_as_dixt(self):
        a = Dixt(x=1)
        b = Dixt(x=1, nested={'y': 2})
        result = a.diff(b)
        assert len(result) == 1
        self_diff, other_diff = result[0]
        assert self_diff == {}
        assert other_diff == {'nested': {'y': 2}}
        assert isinstance(other_diff['nested'], Dixt)

    def test_mapping_only_in_self_wrapped_as_dixt(self):
        a = Dixt(x=1, nested={'y': 2})
        b = Dixt(x=1)
        result = a.diff(b)
        assert len(result) == 1
        self_diff, other_diff = result[0]
        assert self_diff == {'nested': {'y': 2}}
        assert isinstance(self_diff['nested'], Dixt)
        assert other_diff == {}

    def test_non_builtin_value_uses_repr(self):
        class Foo:
            def __repr__(self):
                return 'Foo()'

        obj = Foo()
        a = Dixt(x=obj)
        b = Dixt(x=1)
        result = a.diff(b)
        assert len(result) == 1
        self_diff, other_diff = result[0]
        assert self_diff == {'x': 'Foo()'}
        assert other_diff == {'x': 1}

    def test_non_builtin_only_in_one_side_uses_repr(self):
        class Bar:
            def __repr__(self):
                return 'Bar()'

        obj = Bar()
        a = Dixt(x=obj)
        b = Dixt(y=1)
        result = a.diff(b)
        self_diff, other_diff = result[0]
        assert self_diff == {'x': 'Bar()'}
        assert other_diff == {'y': 1}

    def test_result_contains_dixt_objects(self):
        a = Dixt(x=1, y=2)
        b = Dixt(x=1, y=99)
        result = a.diff(b)
        assert isinstance(result[0][0], Dixt)
        assert isinstance(result[0][1], Dixt)

    def test_list_values_that_differ_included(self):
        a = Dixt(x=[1, 2, 3])
        b = Dixt(x=[1, 2, 99])
        result = a.diff(b)
        assert len(result) == 1
        self_diff, other_diff = result[0]
        assert self_diff == {'x': [..., 3]}
        assert other_diff == {'x': [..., 99]}

    def test_list_values_with_mappings(self):
        a = Dixt(x=[1, 2, {'a': 1, 'b': {'c': 3, 'd': 4}}, {'same': 0}])
        b = Dixt(x=[1, 2, {'a': 1, 'b': {'c': 3, 'd': 9}}, {'same': 0}])
        result = a.diff(b)
        assert len(result) == 1
        self_diff, other_diff = result[0]
        assert self_diff == {'x': [..., {'b': {'d': 4}}, ...]}
        assert other_diff == {'x': [..., {'b': {'d': 9}}, ...]}

    def test_none_value_differs(self):
        a = Dixt(x=None, y=2)
        b = Dixt(x=None, y=None)
        result = a.diff(b)
        assert len(result) == 1
        self_diff, other_diff = result[0]
        assert self_diff == {'y': 2}
        assert other_diff == {'y': None}

    def test_completely_disjoint_keys(self):
        a = Dixt(x=1)
        b = Dixt(y=2)
        result = a.diff(b)
        assert len(result) == 1
        self_diff, other_diff = result[0]
        assert self_diff == {'x': 1}
        assert other_diff == {'y': 2}

    def test_accepts_plain_dict(self):
        a = Dixt(x=1, y=2)
        result = a.diff({'x': 1, 'y': 99})
        assert len(result) == 1
        self_diff, other_diff = result[0]
        assert self_diff == {'y': 2}
        assert other_diff == {'y': 99}

    def test_accepts_ordered_dict(self):
        from collections import OrderedDict
        a = Dixt(x=1, y=2)
        result = a.diff(OrderedDict([('x', 1), ('y', 99)]))
        assert len(result) == 1
        self_diff, other_diff = result[0]
        assert self_diff == {'y': 2}
        assert other_diff == {'y': 99}

    @pytest.mark.parametrize('invalid', ['string', 123, [1,2], {1,2}, object()])
    def test_raises_type_error_for_non_mapping(self, invalid):
        a = Dixt(x=1)
        with pytest.raises(TypeError):
            a.diff(invalid)

    def test_non_str_keys_supported(self):
        a = Dixt({1: 'a', 2: 'b'})
        b = Dixt({1: 'a', 2: 'Z'})
        result = a.diff(b)
        assert len(result) == 1
        self_diff, other_diff = result[0]
        assert self_diff == {2: 'b'}
        assert other_diff == {2: 'Z'}

    def test_flat_and_two_nested_branches_yield_three_pairs(self):
        a = Dixt(x=1, b1={'a': 1, 'same': 0}, b2={'c': 3, 'c2': {'d2': 50, 'same': 0}})
        b = Dixt(x=2, b1={'a': 9, 'same': 0}, b2={'c': 9, 'c2': {'d2': 23, 'same': 0, 'extra': 1}})
        result = a.diff(b)
        assert len(result) == 3
        flat = next((sd, od) for sd, od in result if 'x' in sd or 'x' in od)
        p1 = next((sd, od) for sd, od in result if 'b1' in sd or 'b1' in od)
        p2 = next((sd, od) for sd, od in result if 'b2' in sd or 'b2' in od)
        sd, od = flat
        assert sd == {'x': 1}
        assert od == {'x': 2}
        sd, od = p1
        assert sd == {'b1': {'a': 1}}
        assert od == {'b1': {'a': 9}}
        sd, od = p2
        assert sd == {'b2': {'c': 3, 'c2': {'d2': 50}}}
        assert od == {'b2': {'c': 9, 'c2': {'d2': 23, 'extra': 1}}}

    def test_one_mapping_one_scalar_for_same_key(self):
        a = Dixt(x={'nested': 1})
        b = Dixt(x='scalar')
        result = a.diff(b)
        assert len(result) == 1
        self_diff, other_diff = result[0]
        assert isinstance(self_diff['x'], Dixt)
        assert other_diff['x'] == 'scalar'

    def test_list_consecutive_differing_items_not_collapsed(self):
        a = Dixt(x=[1, 2, 3])
        b = Dixt(x=[9, 8, 3])
        self_diff, other_diff = a.diff(b)[0]
        assert self_diff == {'x': [1, 2, ...]}
        assert other_diff == {'x': [9, 8, ...]}

    def test_list_all_items_differ(self):
        a = Dixt(x=[1, 2])
        b = Dixt(x=[3, 4])
        self_diff, other_diff = a.diff(b)[0]
        assert self_diff == {'x': [1, 2]}
        assert other_diff == {'x': [3, 4]}

    def test_list_self_longer_keeps_surplus_items(self):
        a = Dixt(x=[1, 2, 3, 4])
        b = Dixt(x=[1, 2])
        self_diff, other_diff = a.diff(b)[0]
        assert self_diff == {'x': [..., 3, 4]}
        assert other_diff == {'x': [...]}

    def test_list_other_longer_keeps_surplus_items(self):
        a = Dixt(x=[1])
        b = Dixt(x=[1, 2, {'y': 3}])
        self_diff, other_diff = a.diff(b)[0]
        assert self_diff == {'x': [...]}
        assert other_diff == {'x': [..., 2, {'y': 3}]}
        assert isinstance(other_diff['x'][2], Dixt)

    def test_list_empty_versus_non_empty(self):
        a = Dixt(x=[])
        b = Dixt(x=[1, 2])
        self_diff, other_diff = a.diff(b)[0]
        assert self_diff == {'x': []}
        assert other_diff == {'x': [1, 2]}

    def test_nested_lists_diffed_recursively(self):
        a = Dixt(x=[[1, 2], [3], [4]])
        b = Dixt(x=[[1, 99], [3], [4]])
        self_diff, other_diff = a.diff(b)[0]
        assert self_diff == {'x': [[..., 2], ...]}
        assert other_diff == {'x': [[..., 99], ...]}

    def test_list_mapping_item_paired_with_non_mapping(self):
        a = Dixt(x=[{'y': 1}, 2])
        b = Dixt(x=[5, 2])
        self_diff, other_diff = a.diff(b)[0]
        assert self_diff == {'x': [{'y': 1}, ...]}
        assert isinstance(self_diff['x'][0], Dixt)
        assert other_diff == {'x': [5, ...]}

    def test_list_non_builtin_item_uses_repr(self):
        class Baz:
            def __repr__(self):
                return 'Baz()'

        a = Dixt(x=[1, Baz()])
        b = Dixt(x=[1, 2])
        self_diff, other_diff = a.diff(b)[0]
        assert self_diff == {'x': [..., 'Baz()']}
        assert other_diff == {'x': [..., 2]}

    def test_list_of_mappings_with_different_lengths(self):
        a = Dixt(x=[{'y': 1}, {'z': 2}])
        b = Dixt(x=[{'y': 1}])
        self_diff, other_diff = a.diff(b)[0]
        assert self_diff == {'x': [..., {'z': 2}]}
        assert other_diff == {'x': [...]}

    def test_tuple_values_not_diffed_element_by_element(self):
        a = Dixt(x=(1, 2, 3))
        b = Dixt(x=(1, 2, 99))
        self_diff, other_diff = a.diff(b)[0]
        assert self_diff == {'x': (1, 2, 3)}
        assert other_diff == {'x': (1, 2, 99)}

    def test_empty_self_versus_non_empty_other(self):
        self_diff, other_diff = Dixt().diff({'x': 1})[0]
        assert self_diff == {}
        assert other_diff == {'x': 1}

    @pytest.mark.parametrize('other_value', [1, 99])
    def test_keys_are_matched_by_original_form(self, other_value):
        assert Dixt({'A-B': 1}).diff({'a_b': other_value}) == [
            ({'A-B': 1}, {'a_b': other_value})
        ]

    @pytest.mark.parametrize('nested_in_list', [False, True])
    def test_nested_keys_are_matched_by_original_form(self, nested_in_list):
        left, right = {'C D': 1}, {'c_d': 1}
        if nested_in_list:
            left, right = [left], [right]
        assert Dixt({'A-B': left}).diff({'A-B': right}) == [
            ({'A-B': left}, {'A-B': right})
        ]

    def test_hidden_items_are_not_compared(self):
        a = Dixt(x=1, y=2)
        b = Dixt(x=1, y=99)
        a.keymeta('y', hidden=True)
        b.keymeta('y', hidden=True)
        assert a.diff(b) == []

    def test_item_hidden_in_self_only_is_reported_as_other_only(self):
        a = Dixt(x=1, y=2)
        b = Dixt(x=1, y=99)
        a.keymeta('y', hidden=True)
        self_diff, other_diff = a.diff(b)[0]
        assert self_diff == {}
        assert other_diff == {'y': 99}

    def test_order_of_pairs_follows_insertion_order(self):
        a = Dixt(b2={'c': 1}, x=1, b1={'a': 1})
        b = Dixt(b2={'c': 2}, x=2, b1={'a': 2})
        result = a.diff(b)
        assert len(result) == 3
        assert [list(sd.keys()) for sd, _ in result] == [['x'], ['b2'], ['b1']]
        assert a.diff(b) == result  # deterministic across calls

    def test_diff_preserves_original_mapping_keys_inside_nested_lists(self):
        dx = Dixt(x=[[{'A-B': 1}]])
        assert dx.diff({'x': [[{'a_b': 1}]]}) == [
            ({'x': [[{'A-B': 1}]]}, {'x': [[{'a_b': 1}]]})
        ]


class TestEdgeCaseRegressions:

    @pytest.mark.skip
    @pytest.mark.parametrize('use_kwargs', [False, True])
    def test_constructor_rejects_normalised_key_collisions(self, use_kwargs):
        # Match __setitem__: distinct original keys must not share an alias.
        with pytest.raises(KeyError):
            if use_kwargs:
                Dixt({'A-B': 1}, a_b=2)
            else:
                Dixt({'A-B': 1, 'a_b': 2})

    @pytest.mark.skip
    @pytest.mark.parametrize('hidden', [False, True])
    def test_setting_same_hidden_flag_is_idempotent(self, hidden):
        dx = Dixt({'A-B': 1})
        dx.keymeta('A-B', hidden=hidden)
        dx.keymeta('a_b', hidden=hidden)
        assert dx['A-B'] == 1
        assert dx.whats_hidden() == (('A-B',) if hidden else ())
        assert ('A-B' in dx) is (not hidden)

    @pytest.mark.parametrize('key', ['items', 'get', 'clear'])
    def test_missing_method_name_is_not_a_mapping_entry(self, key):
        dx = Dixt()
        assert key not in dx
        with pytest.raises(KeyError):
            dx[key]

    @pytest.mark.parametrize('key', ['items', 'get', 'clear'])
    def test_setdefault_inserts_missing_method_name(self, key):
        dx = Dixt()
        assert dx.setdefault(key, 42) == 42
        assert dx[key] == 42
        assert key in dx

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

    def test_reinsert_after_clear_is_visible(self):
        dx = Dixt(a=1)
        dx.keymeta('a', hidden=True)
        dx.clear()
        dx['a'] = 2
        assert dx.dict() == {'a': 2}
        assert dx['a'] == 2
        assert dx.whats_hidden() == ()

    def test_constructor_accepts_generator_of_pairs(self):
        pairs = ((key, value) for key, value in [('a', 1), ('b', 2)])
        assert Dixt(pairs) == {'a': 1, 'b': 2}

    def test_constructor_preserves_identity_based_keys(self):
        key = object()
        dx = Dixt({key: 1})
        assert dx[key] == 1
        assert next(iter(dx)) is key

    @pytest.mark.parametrize('key', [1, (1, 2)])
    def test_merge_update_adds_non_string_key(self, key):
        dx = Dixt()
        dx.merge_update({key: 'value'})
        assert dx == {key: 'value'}

    def test_recursive_list_merge_accepts_chainmap_elements(self):
        dx = Dixt(a=[ChainMap({'x': 1, 'keep': 2})])
        dx.merge_update({'a': [{'x': 10, 'new': 3}]}, recurse_lists=True)
        assert dx.a[0] == {'x': 10, 'keep': 2, 'new': 3}

    def test_dict_converts_mapping_inside_tuple(self):
        dx = Dixt(a=({'x': 1},))
        result = dx.dict()
        assert isinstance(result['a'], tuple)
        assert type(result['a'][0]) is dict
        assert result == {'a': ({'x': 1},)}

    def test_json_converts_mapping_inside_tuple(self):
        dx = Dixt(a=({'x': 1},))
        assert json.loads(dx.json()) == {'a': [{'x': 1}]}

    @pytest.mark.parametrize('nested', [{}, {'x': 1}])
    def test_mapping_is_not_submap_of_scalar(self, nested):
        assert Dixt(a=nested).is_submap_of({'a': 2}) is False

    @pytest.mark.parametrize('nested', [{}, {'x': 1}])
    def test_scalar_is_not_supermap_of_mapping(self, nested):
        assert Dixt(a=2).is_supermap_of({'a': nested}) is False


def _assert_obj_tree_has_no_dixt_object(obj):
    assert not isinstance(obj, Dixt)
    if isinstance(obj, dict):
        for key in obj:
            _assert_obj_tree_has_no_dixt_object(obj[key])
    elif isinstance(obj, list):
        for item in obj:
            _assert_obj_tree_has_no_dixt_object(item)
