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
import unittest

from assertpy import assert_that
from collections import OrderedDict
from collections.abc import KeysView, ValuesView, ItemsView

from lxdx import Dixt


class TestDixt(unittest.TestCase):
    def setUp(self):
        self.dixt = Dixt({
            'headers': {
                'Accept-Encoding': 'gzip',
                'Content-Type': 'application/json'
            },
            'body': {
                'C-D': 1.2,
                'e': [2, {'g': 9.806}],
                'f': {'x': None, 'y': [{'p': 5}, [8]]}
            },
            'extra': 'info'
        })
        self.dict_equiv = {
            'headers': {
                'Accept-Encoding': 'gzip',
                'Content-Type': 'application/json'
            },
            'body': {
                'C-D': 1.2,
                'e': [2, {'g': 9.806}],
                'f': {'x': None, 'y': [{'p': 5}, [8]]}
            },
            'extra': 'info'
        }

    def test__init__accepts_key_value_pairs(self):
        dx = Dixt([(1, 100), ('2', '200')])
        self.assertEqual(dx, {1: 100, '2': '200'})

        dx = Dixt([(1, 100), ('2', '200')], a='a', b='b')
        self.assertEqual(dx, {1: 100, '2': '200', 'a': 'a', 'b': 'b'})

        # limitation:
        # due to the __new__ function using the zip iterator,
        # data must be wrapped first
        dx = Dixt(list(zip([1, '2'], [100, '200'])))
        self.assertEqual(dx, {1: 100, '2': '200'})

        dx = Dixt(tuple(zip([1, '2'], [100, '200'])))
        self.assertEqual(dx, {1: 100, '2': '200'})

        dx = Dixt(dict(zip([1, '2'], [100, '200'])))
        self.assertEqual(dx, {1: 100, '2': '200'})

    def test__init__accepts_another_dixt_object(self):
        dx = Dixt({1: 1})
        self.assertEqual(Dixt(dx), {1: 1})

    def test__init__should_not_change_data_type(self):
        dx = Dixt(a=(1, 2, 3))
        self.assertEqual(dx, {'a': (1, 2, 3)})

        dx = Dixt(a={1, 2, 3})
        self.assertEqual(dx, {'a': {1, 2, 3}})

    def test__init__accepts_kwargs(self):
        dx = Dixt(alpha='α', beta='β', gamma='γ')
        self.assertEqual(dx, {'alpha': 'α', 'beta': 'β', 'gamma': 'γ'})
        self.assertEqual(dx.alpha, 'α')

        dx = Dixt(a_b='a b', cd=1.2, e=[2, 4], f={'x': 3, 'y': [{'p': 5}, {'q': 7}]})
        self.assertEqual(dx, {'a_b': 'a b', 'cd': 1.2, 'e': [2, 4], 'f': {'x': 3, 'y': [{'p': 5}, {'q': 7}]}})

    def test__init__kwargs_updates_data(self):
        dx = Dixt({'alpha': 'α', 'beta': 'β'})
        self.assertEqual(dx, {'alpha': 'α', 'beta': 'β'})

        dx = Dixt({'alpha': 'α', 'beta': 'β'}, gamma='γ', beta='veeta')
        self.assertEqual(dx, {'alpha': 'α', 'beta': 'veeta', 'gamma': 'γ'})

        dx = Dixt(alpha='α', beta='β')
        self.assertEqual(Dixt(dx, beta='beta'), {'alpha': 'α', 'beta': 'beta'})

    def test__equality__dixt_compared_to_dixt(self):
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

        self.assertEqual(a, b)
        self.assertEqual(c, d)
        self.assertNotEqual(b, c)

    def test__equality__dixt_compared_to_dict(self):
        dx = Dixt(x=1, y=2, z=3)
        self.assertEqual(dx, {'x': 1, 'y': 2, 'z': 3})

    def test__equality__dixt_compared_to_ordered_dict(self):
        dx = Dixt(x=1, y=2)
        self.assertEqual(dx, OrderedDict((('y', 2), ('x', 1))))

    def test__equality__dixt_compared_to_iterable_key_value_pairs(self):
        dx = Dixt(x=1, y=2)
        self.assertEqual(dx, [('x', 1), ('y', 2)])
        self.assertEqual(dx, (('y', 2), ('x', 1)))

    def test__equality__compare_to_other_types(self):
        self.assertNotEqual(self.dixt, 'string')
        self.assertNotEqual(self.dixt, 1234)
        self.assertNotEqual(self.dixt, {'set'})
        self.assertNotEqual(self.dixt, ['not', 'key-value', 'pair'])

    def test__not_operator__return_false_when_empty_and_true_otherwise(self):
        self.assertFalse(Dixt())
        self.assertFalse(not self.dixt)
        self.assertTrue(self.dixt)
        self.assertTrue(not Dixt())

    def test__or_operator__should_choose_the_second_option_when_first_is_empty(self):
        self.assertEqual(Dixt() or 'else', 'else')
        self.assertEqual(Dixt() or {1: 1}, {1: 1})
        self.assertEqual(Dixt() or self.dixt, self.dixt)

    def test__union_operator__arg_is_dict(self):
        assert_that(Dixt() | {}).is_instance_of(Dixt).is_equal_to({})
        assert_that(Dixt() | {1: {2: 2}}).is_instance_of(Dixt).is_equal_to({1: {2: 2}})
        self.assertEqual(Dixt({1: 1}) | {2: 2}, {2: 2, 1: 1})

    def test__union_operator__arg_is_dixt(self):
        assert_that(Dixt({1: 1}) | Dixt()).is_instance_of(Dixt).is_equal_to({1: 1})
        assert_that(Dixt() | Dixt()).is_instance_of(Dixt).is_equal_to({})
        self.assertEqual(Dixt() | Dixt({2: 2}), {2: 2})
        self.assertEqual(Dixt({1: 1}) | Dixt({1: 100, 2: 2}), {1: 100, 2: 2})

        assert_that({1: 1} | Dixt()).is_instance_of(dict).is_equal_to({1: 1})
        assert_that({} | Dixt()).is_instance_of(dict).is_equal_to({})
        self.assertEqual({} | Dixt({2: 2}), {2: 2})
        self.assertEqual({1: 1} | Dixt({2: 2}), {1: 1, 2: 2})

    def test__union_operator__first_arg_is_iterable_key_value_pairs(self):
        """This will trigger __ror__"""
        assert_that([(1, 1), (2, 2)] | Dixt()).is_instance_of(dict).is_equal_to({1: 1, 2: 2})
        assert_that([(1, 1), (2, 2)] | Dixt({2: 4})).is_instance_of(dict).is_equal_to({1: 1, 2: 4})

    def test__union_operator__in_place_operation(self):
        dx = Dixt()
        dx |= {}
        self.assertEqual(dx, {})
        dx |= {1: 1}
        self.assertEqual(dx, {1: 1})
        dx |= [(1, 100), (2, 2)]
        self.assertEqual(dx, {1: 100, 2: 2})

    def test__union_operator__raises_error_for_non_supported_types_or_values(self):
        arguments = [
            'string',
            1234,
            ['list', 'not', 'key-value', 'pair'],
            {'this', 'is', 'set'}
        ]
        dx = Dixt()
        for arg in arguments:
            with self.assertRaises(Exception):
                dx | arg   # __or__
            with self.assertRaises(Exception):
                arg | dx   # __ror__
            with self.assertRaises(Exception):
                dx |= arg  # __ior__

    def test__len(self):
        self.assertEqual(len(self.dixt), 3)
        self.assertEqual(len(self.dixt.headers), 2)
        self.assertEqual(len(self.dixt.body), 3)
        self.assertEqual(len(self.dixt.body.f.y), 2)

    def test__str__repr(self):
        dx = Dixt(a=1, b=Dixt(c=3))
        self.assertEqual(str(dx), "{'a': 1, 'b': {'c': 3}}")
        self.assertEqual(repr(dx), "{'a': 1, 'b': {'c': 3}}")

        dx = {'alpha': Dixt(a='a'), 'omega': Dixt(o='o')}
        self.assertEqual(str(dx), "{'alpha': {'a': 'a'}, 'omega': {'o': 'o'}}")

    def test__getattr__dot_notation(self):
        expected = {'C-D': 1.2,
                    'e': [2, {'g': 9.806}],
                    'f': {'x': None, 'y': [{'p': 5}, [8]]}}

        self.assertEqual(self.dixt.body, expected)
        self.assertEqual(self.dixt.body.f.x, None)
        self.assertEqual(self.dixt.body.c_d, 1.2)

    def test__getattr__dot_notation__using_normalised_keys(self):
        dx = Dixt(**{'Alpha-Bravo': 'ab',
                     'CharlieDelta': 'cd',
                     'echo foxtrot': 'ef'})
        self.assertEqual(dx.alpha_bravo, 'ab')
        self.assertEqual(dx.charliedelta, 'cd')
        self.assertEqual(dx.echo_foxtrot, 'ef')

    def test__getattr__dot_notation__raises_error_when_nonexistent(self):
        self.assertRaises(KeyError, lambda: self.dixt.nonexistent)

    def test__getx__returns_value_of_existing_attributes(self):
        headers = {'Accept-Encoding': 'gzip',
                   'Content-Type': 'application/json'}
        self.assertEqual(self.dixt.getx('headers'), headers)
        self.assertEqual(self.dixt.headers.getx('Accept-Encoding'), 'gzip')
        self.assertEqual(self.dixt.body.f.getx('x', 'y'), (None, [{'p': 5}, [8]]))

    def test__getx__returns_default_value_of_nonexistent_attributes(self):
        self.assertEqual(self.dixt.getx('ghost', default=-1), -1)
        self.assertEqual(self.dixt.headers.getx('Lost-Item', default=object), object)

        self.assertEqual(self.dixt.getx('ghost', default=[1]), 1)
        self.assertEqual(self.dixt.body.f.getx('x', default='X'), None)
        self.assertEqual(self.dixt.getx('ghost', 'invisible', default=2), (2, 2))
        self.assertEqual(self.dixt.getx('ghost', 'invisible', default=[4, 5]), (4, 5))

    def test__getx__raises_error_when_defaults_dont_match_with_attrs_len(self):
        with self.assertRaises(ValueError):
            self.dixt.getx('ghost', 'invisible', default=(1, 2, 3))

        with self.assertRaises(ValueError):
            self.dixt.getx('ghost', 'invisible', default=[3])

    def test__setattr__builtin_function(self):
        setattr(self.dixt, 'name', 'value')
        self.assertEqual(self.dixt.name, 'value')
        self.assertEqual(self.dixt['name'], 'value')

    def test__setattr__builtin_function__should_normalise_attribute_name(self):
        setattr(self.dixt, 'My Name', 'value')
        self.assertEqual(self.dixt.my_name, 'value')
        self.assertEqual(self.dixt['My Name'], 'value')

    def test__setattr__dot_notation__existing_attributes(self):
        self.dixt.extra = value = 'new value'
        self.assertEqual(self.dixt.extra, value)
        self.assertEqual(self.dixt['extra'], value)

        self.dixt.body.c_d = value = 'string'
        self.assertEqual(self.dixt.body.c_d, value)
        self.assertEqual(self.dixt.body['C-D'], value)

    def test__setattr__dot_notation__nonexistent_attributes(self):
        self.dixt.name = value = 123456
        self.assertTrue('name' in self.dixt)
        self.assertEqual(self.dixt.name, value)
        self.assertEqual(self.dixt['name'], value)

    def test__setattr__dot_notation__takes_the_attribute_verbatim(self):
        self.dixt.something_new = 123456
        self.assertTrue('something_new' in self.dixt)
        self.assertTrue('something-new' not in self.dixt)
        self.assertTrue('something new' not in self.dixt)
        self.assertTrue('Something-New' not in self.dixt)

    def test__setattr__dot_notation__another_dict_or_dixt(self):
        self.dixt.extra = {'alpha': 1}
        self.assertIsInstance(self.dixt.extra, Dixt)
        self.assertEqual(self.dixt.extra, Dixt(alpha=1))
        self.assertEqual(self.dixt.extra.alpha, 1)

        self.dixt.extra = Dixt(alpha=1)
        self.assertEqual(self.dixt.extra, {'alpha': 1})
        self.assertEqual(self.dixt.extra.alpha, 1)

    def test__getitem__gets_value_of_existing_items(self):
        self.assertEqual(self.dixt['headers']['Accept-Encoding'], 'gzip')
        self.assertEqual(self.dixt['body']['f']['x'], None)
        self.assertEqual(self.dixt['extra'], 'info')

    def test__getitem__raises_attribute_error_when_missing(self):
        self.assertRaises(KeyError, lambda: self.dixt['missing_attribute'])

    def test__setitem__existing_attributes(self):
        dx = Dixt(a=1, b=2, c=3)
        dx['a'] *= 100
        dx['b'] = dx['a'] + dx['c']
        self.assertEqual(dx, {'a': 100, 'b': 103, 'c': 3})

        dx = Dixt({1: 1, 2: 2, 3: 3})
        dx[1] *= 100
        dx[2] = dx[1] + dx[3]
        self.assertEqual(dx, {1: 100, 2: 103, 3: 3})

    def test__setitem__raises_error_when_adding_similarly_formatted_keys(self):
        with self.assertRaises(KeyError):
            self.dixt.headers['content_type'] = 'new-type'

        # must not raise error
        self.dixt.headers.content_type = 'type-one'
        self.dixt.headers['Content-Type'] = 'type-two'

    def test__setitem__nonexistent_attributes(self):
        dx = Dixt()
        dx['a'] = 1
        dx['b'] = (2, 3)
        dx[123] = "cc"
        self.assertEqual(dx, {'a': 1, 'b': (2, 3), 123: 'cc'})

    def test__setattr__setitem__hype_when_value_is_dict_or_dixt(self):
        dxa = Dixt(a=1, b={'bb': 2})
        dxa.c = {'c-c': 3}
        dxb = Dixt(a=1, b=Dixt(bb=2))
        dxb['c'] = {'c-c': 3}
        self.assertEqual(dxa, dxb)
        self.assertEqual(dxa.c.c_c, 3)
        self.assertEqual(dxb.c.c_c, 3)

    def test__pop(self):
        self.assertEqual(self.dixt.pop('extra'), 'info')
        self.assertNotIn('extra', self.dixt)
        self.assertNotIn('extra', self.dixt.__keymap__)
        with self.assertRaises(KeyError):
            self.dixt.pop('extra')
        self.assertEqual(self.dixt.pop('extra', 'default-value'), 'default-value')

    def test__clear(self):
        self.dixt.headers.clear()
        self.assertEqual(self.dixt.headers, {})
        self.assertEqual(self.dixt.headers, Dixt())
        self.assertEqual(self.dixt.headers.__keymap__, {})
        self.dixt.body.clear()
        self.assertEqual(self.dixt, {'headers': {}, 'body': {}, 'extra': 'info'})
        self.assertEqual(self.dixt, Dixt(headers=Dixt(),
                                         body=Dixt(),
                                         extra='info'))
        self.assertEqual(self.dixt.body.__keymap__, {})

    def test__update__value_is_forced_to_be_none(self):
        dx = Dixt(a=1, b=2)
        dx.update(None)
        self.assertEqual(dx, Dixt(a=1, b=2))

    def test__update__value_is_dict(self):
        dx = Dixt(a=1, b=2)
        dx.update({'c': 3})
        self.assertEqual(dx, Dixt(a=1, b=2, c=3))

    def test__update__value_is_dixt(self):
        dx = Dixt(a=1, b=2)
        dx.update(Dixt(d=4))
        self.assertEqual(dx, Dixt(a=1, b=2, d=4))

    def test__update__value_is_in_kwargs_only(self):
        dx = Dixt(a=1, b=2)
        dx.update(x=3, y=4)
        self.assertEqual(dx, Dixt(a=1, b=2, x=3, y=4))

    def test__update__value_is_iterable_key_value_pairs(self):
        dx = Dixt(a=1, b=2)
        dx.update((('x', 24), ('y', 25)))
        self.assertEqual(dx, Dixt(a=1, b=2, x=24, y=25))

    def test__update__combination_of_dict_and_kwargs(self):
        dx = Dixt(a=1, b=2)
        dx.update({'c': 3}, d={'dd': 44})
        self.assertEqual(dx, Dixt(a=1, b=2, c=3, d=Dixt(dd=44)))

    def test__update__combination_of_dixt_and_kwargs(self):
        dx = Dixt(a=1, b=2)
        dx.update(Dixt(e=5, f=Dixt(g=7)))
        self.assertEqual(dx, Dixt(a=1, b=2, e=5, f=Dixt(g=7)))

    def test__update__combination_of_key_value_pairs_and_kwargs(self):
        dx = Dixt(a=1, b=2)
        dx.update((('e', 5),), x=[1, 2])
        self.assertEqual(dx, {'a': 1, 'b': 2, 'e': 5, 'x': [1, 2]})

    def test__update__raises_error__argument_is_not_iterable_key_value_pairs(self):
        for arg in ['string', ['list', 1], 1234]:
            with self.assertRaises(ValueError):
                Dixt(a=1, b=2).update(arg, x=[1, 2])

    def test__contains(self):
        self.assertTrue('extra' in self.dixt)
        self.assertTrue(self.dixt.contains(*['headers', 'body', 'extra']))
        self.assertTrue(self.dixt.contains('headers', 'body', 'extra'))
        self.assertFalse('ghost' in self.dixt)
        self.assertFalse(self.dixt.contains('headers', 'body', 'ghost'))

    def test__contains__must_be_case_sensitive(self):
        dx = Dixt({1: 100, 2: 200, 'A-a': 'aa'})
        self.assertTrue(1 in dx)
        self.assertTrue('A-a' in dx)
        self.assertTrue('a-a' not in dx)
        self.assertTrue(dx.contains(2, 1))
        self.assertFalse(dx.contains('A-a', 'a-a'))

    def test__contains__assert_all_is_false(self):
        result = self.dixt.contains('headers', 'body', assert_all=False)
        self.assertIsInstance(result, tuple)
        self.assertTrue(all(result))

        result = self.dixt.contains('headers', 'ghost', assert_all=False)
        self.assertIsInstance(result, tuple)
        self.assertEqual(result, (True, False))

        result = self.dixt.contains('nonexistent', assert_all=False)
        self.assertEqual(result, (False,))

    def test__iter(self):
        self.assertIsInstance(iter(self.dixt), type(iter({}.keys())))

    def test__delitem(self):
        del self.dixt['headers']
        self.assertNotIn('headers', self.dixt)

        self.assertIn('C-D', self.dixt.body)
        self.assertIn('c_d', self.dixt.body.__keymap__)
        del self.dixt.body['C-D']
        self.assertNotIn('C-D', self.dixt.body)
        self.assertNotIn('c_d', self.dixt.body.__keymap__)

        del self.dixt['body']
        self.assertEqual(self.dixt, Dixt(extra='info'))

    def test__delitem__should_be_case_insensitive(self):
        self.dixt['A'] = 'A'
        del self.dixt['a']
        self.assertNotIn('A', self.dixt)

        del self.dixt['Extra']
        self.assertNotIn('extra', self.dixt)

    def test__delitem__raises_error__item_is_not_found(self):
        with self.assertRaises(KeyError):
            del self.dixt['not-found']

    def test__delattr(self):
        del self.dixt.headers.content_type
        self.assertNotIn('Content-Type', self.dixt.headers)
        self.assertNotIn('content_type', self.dixt.headers)
        del self.dixt.headers
        del self.dixt.body
        self.assertEqual(self.dixt, {'extra': 'info'})

    def test__delattr__should_be_case_insensitive(self):
        del self.dixt.EXTRA
        self.assertNotIn('extra', self.dixt)

    def test__delattr__raises_error__attribute_is_not_found(self):
        with self.assertRaises(KeyError):
            del self.dixt.not_found

    def test__keys(self):
        keys = self.dixt.keys()
        self.assertIsInstance(keys, KeysView)
        self.assertEqual(list(keys), ["headers", "body", "extra"])

    def test__values(self):
        values = self.dixt.headers.values()
        self.assertIsInstance(values, ValuesView)
        self.assertEqual(list(values), ["gzip", "application/json"])

    def test__items(self):
        items = self.dixt.headers.items()
        self.assertIsInstance(items, ItemsView)
        self.assertEqual(list(items), [('Accept-Encoding', 'gzip'), ('Content-Type', 'application/json')])

    def test__dict__should_return_dict_object_with_non_normalised_keys(self):
        self.assertEqual(self.dixt.dict(), self.dict_equiv)
        self._assert_obj_tree_has_no_dixt_object(self.dixt.dict())

        self.dixt.extra = Dixt(a=1, b=[Dixt(c=3)])
        self._assert_obj_tree_has_no_dixt_object(self.dixt.dict())

    def test__traversals_with_nested_objects(self):
        self.assertEqual(self.dixt.body.e[1], {"g": 9.806})
        self.assertEqual(self.dixt['body']['e'][1], {"g": 9.806})

        self.assertEqual(self.dixt.body.e[1].g, 9.806)
        self.assertEqual(self.dixt['body']['e'][1]['g'], 9.806)

        self.assertEqual(self.dixt.body.f.y[1], [8])
        self.assertEqual(self.dixt['body']['f']['y'][1], [8])

        self.assertEqual(self.dixt.body.f.y[1][0], 8)
        self.assertEqual(self.dixt['body']['f']['y'][1][0], 8)

    def test__operations_on_nested_objects(self):
        self.dixt.body.f.y[1].extend(['σ', 'φ', 'θ'])
        self.assertEqual(self.dixt.body.f.y[1], [8, 'σ', 'φ', 'θ'])

        self.dixt.body.e[1] = {'del-ta': 'd'}
        # AttributeError: Since the assignment is handled by the list object,
        #                 the dict is not converted to a Dixt object.
        #                 Should wrap with Dixt first
        #                 before appending/adding to the list.
        # self.dixt.body.e[1].del_ta = 'δ'

        self.dixt.body.e[1] = Dixt({'del-ta': 'δ'})
        self.assertEqual(self.dixt.body.e[1], {'del-ta': 'δ'})
        self.assertEqual(self.dixt.body.e[1].del_ta, 'δ')

    def test__get_from(self):
        queries = [
            ('$.extra', 'info'),
            ('$.body.e[0]', 2),
            ('$.body.e[1].g', 9.806),
            ('$.body.f.y[1][0]', 8)
        ]
        for path, value in queries:
            self.assertEqual(self.dixt.get_from(path), value)

    def test__get_from__invalid_path(self):
        error_queries = {
            IndexError: ['$.body.e[100]'],
            KeyError: [
                '$.extra.info',
                '$.not_heading.nonexistent',
                '$.headers.nonexistent'
            ],
            TypeError: [123, object()],
            ValueError: [
                '',
                'any.string',
                '$',
                '$.',
                '$..',
                '$[0]',
                '$.body.e.[0]',
                'a.b[0]',
                '$.a[2',
                '$.a.b[]',
                '$.a[-1]',
                '$.a[1:]',
                '$.a[:1]',
                '$.a[::]'
            ],
        }

        for exc, queries in error_queries.items():
            for path in queries:
                with self.assertRaises(exc):
                    self.dixt.get_from(path)

    def test__json__conversion_to_json_format(self):
        json_equivalent = json.dumps(self.dict_equiv)
        self.assertEqual(self.dixt.json(), json_equivalent)

    def test__from_json(self):
        json_string = json.dumps(self.dict_equiv)
        dx = Dixt.from_json(json_string)
        self.assertEqual(dx, self.dict_equiv)

    def test__submap__supermap(self):
        criteria = [
            {'body': {'e': [2, {'g': 9.806}]}},
            {'body': {'f': {'y': [{'p': 5}, [8]]}}},
            {'extra': 'info'},
            [('extra', 'info')],
            {'headers': {}, 'body': {}}
        ]
        for criterion in criteria:
            self.assertTrue(Dixt(criterion).is_submap_of(self.dixt))
            self.assertTrue(Dixt(self.dixt).is_supermap_of(criterion))

        criteria = [
            {1: 1},
            {'extra': ''},
            {'body': {'f': {'y': [None]}}},
            {'headers': {}, 'body': {}, 'nonexistent': {}}
        ]
        for criterion in criteria:
            self.assertFalse(Dixt(criterion).is_submap_of(self.dixt))
            self.assertFalse(Dixt(self.dixt).is_supermap_of(criterion))

        self.assertTrue(Dixt({1: 1}).is_submap_of([(1, 1), (2, 2)]))

        for criterion in ['string', {'set'}, 123, ['non', 'key-value', 'pair']]:
            with self.assertRaises(Exception):
                # noinspection PyTypeChecker
                Dixt().is_submap_of(criterion)

    def test__popitem(self):
        """Testing inherited function from MutableMapping."""
        dx = Dixt(a=1, b=2, c=3)
        # not LIFO as with dict
        self.assertEqual(dx.popitem(), ('a', 1))

    def test__setdefault__sets_value_to_nonexistent_key_from_default_value(self):
        """Testing inherited function from MutableMapping."""
        self.assertTrue('extra-extra' not in self.dixt)
        self.dixt.setdefault('extra-extra', 'extra-value')
        self.assertEqual(self.dixt.extra_extra, 'extra-value')

        self.assertTrue('to-exist' not in self.dixt)
        self.dixt.setdefault('to-exist')
        self.assertEqual(self.dixt.to_exist, None)

    def test__setdefault__does_not_overwrite_existing_value(self):
        self.dixt.setdefault('extra', 'another-value')
        self.assertEqual(self.dixt.extra, 'info')

    def test__keymeta__hidden_flag(self):
        self.dixt.keymeta('body', hidden=True)

        self.assertTrue('body' in self.dixt.whats_hidden())
        self.assertFalse('body' in self.dixt)
        self.assertFalse(self.dixt == self.dict_equiv)

        self.assertEqual(len(self.dixt), 2)
        self.assertEqual(list(self.dixt.keys()), ['headers', 'extra'])

        body = {'f': {'x': None}}
        self.assertFalse(self.dixt.is_supermap_of({'body': body}))
        dx = self.dixt.body | {'something': 'new'}
        self.assertEqual(dx.something, 'new')
        self.assertTrue(dx.is_supermap_of(body | {'something': 'new'}))

    def test__keymeta__flag_a_non_str_key(self):
        self.dixt[123] = '123'
        self.dixt.keymeta(123, hidden=True)
        self.assertTrue(123 not in self.dixt)

    def test__keymeta__hidden_flag__can_still_get_and_set_items(self):
        self.dixt.headers.keymeta('Accept-Encoding', hidden=True)
        self.dixt.headers.accept_encoding = 'zip'
        self.assertEqual(self.dixt.headers.accept_encoding, 'zip')

        self.dixt.keymeta('headers', hidden=True)
        self.dixt.headers['Accept-Encoding'] = 'tar'
        self.assertEqual(self.dixt.headers['Accept-Encoding'], 'tar')

    def test__keymeta__able_to_flag_items_of_hidden_items(self):
        self.dixt.keymeta('body', hidden=True)
        self.dixt.body.keymeta('e', hidden=True)
        self.assertTrue('body' in self.dixt.whats_hidden())
        self.assertTrue('e' in self.dixt.body.whats_hidden())

    def test__keymeta__unsupported_flags_bypassed(self):
        self.dixt.keymeta('body', whatever='value')
        self.assertTrue('body' not in self.dixt.__keymeta__)

        self.dixt.keymeta('extra', hidden=True, whatever='value')
        self.assertTrue('whatever' not in self.dixt.__keymeta__['extra'])
        self.assertTrue('hidden' in self.dixt.__keymeta__['extra'])

    def test__keymeta__no_flags_returns_metadata_of_keys(self):
        self.dixt.keymeta('extra', 'body', hidden=True)

        expected = {'extra': {'hidden': True}}
        self.assertEqual(self.dixt.keymeta('extra'), expected)

        expected['body'] = {'hidden': True}
        self.assertEqual(self.dixt.keymeta('extra', 'body'), expected)

    def test__keymeta__remove_from_keymeta_a_deleted_flagged_item(self):
        self.dixt.keymeta('extra', hidden=True)
        del self.dixt.extra
        self.assertTrue('extra' not in self.dixt.__data__)
        self.assertTrue('extra' not in self.dixt.__keymeta__)
        self.assertTrue('extra' not in self.dixt.__hidden__)

    def test__keymeta__cleanup_of_metadata_on_reset_value(self):
        self.dixt.keymeta('body', hidden=True)
        self.assertTrue('hidden' in self.dixt.__keymeta__['body'])
        self.dixt.keymeta('body', hidden=False)  # reset value
        self.assertTrue('body' not in self.dixt.__keymeta__)

    def test__keymeta__raises_error_when_keys_are_not_found(self):
        with self.assertRaises(KeyError):
            self.dixt.keymeta('ghost')

    def test__keymeta__hidden_flag__raises_error_when_invalid_value(self):
        with self.assertRaises(TypeError):
            self.dixt.keymeta('extra', hidden=2)

    def test__reverse(self):
        alpha = ['jan', 100, 1.1, (3, 5)]
        beta = ['feb', 200, 2.2, (7, 11)]
        dx = Dixt(dict(zip(alpha, beta)))
        rdx = dx.reverse()
        self.assertEqual(rdx, dict(zip(beta, alpha)))

    def test__reverse__exclude_hidden_items(self):
        dx = Dixt(a=100, b=200)
        dx.keymeta('a', hidden=True)
        self.assertEqual(dx.reverse(), {200: 'b'})

    def test__reverse__raise_error_on_hashable_values(self):
        with self.assertRaises(TypeError):
            Dixt(a=100, b=[1, 2, 3]).reverse()

        with self.assertRaises(TypeError):
            Dixt(a=100, b={2: 200}).reverse()

        with self.assertRaises(TypeError):
            Dixt(a=100, b={200, 300}).reverse()

    def _assert_obj_tree_has_no_dixt_object(self, obj):
        self.assertNotIsInstance(obj, Dixt)
        if isinstance(obj, dict):
            for key in obj:
                self._assert_obj_tree_has_no_dixt_object(obj[key])
        elif isinstance(obj, list):
            for item in obj:
                self._assert_obj_tree_has_no_dixt_object(item)


if __name__ == '__main__':
    unittest.main()
