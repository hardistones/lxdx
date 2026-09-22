# SPDX-FileCopyrightText: 2021-2026 @github.com/hardistones
# SPDX-License-Identifier: BSD-3-Clause

import pytest
from lxdx import Dixt
from lxdx.dixt import DixtException  # noqa


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

    def test_accepts_generator_of_pairs(self):
        pairs = ((key, value) for key, value in [('a', 1), ('b', 2)])
        assert Dixt(pairs) == {'a': 1, 'b': 2}

    def test_preserves_identity_based_keys(self):
        key = object()
        dx = Dixt({key: 1})
        assert dx[key] == 1
        assert next(iter(dx)) is key

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

    def test_kwargs_update_normalised_alias(self):
        data = {'A-B': 1}
        dx = Dixt(data, a_b=2)
        assert dx.dict() == {'A-B': 2}
        assert dx['A-B'] == dx.a_b == 2
        assert data == {'A-B': 1}

    @pytest.mark.parametrize('data', [
        {'A-B': 1, 'a_b': 2},
        {'a_b': 2, 'A-B': 1},
    ])
    def test_preserves_colliding_original_keys(self, data):
        dx = Dixt(data)
        assert dx.dict() == data
        assert dx['A-B'] == 1
        assert dx['a_b'] == dx.a_b == 2
        assert dx.__keymap__ == {'a_b': 'a_b'}
        assert Dixt(dx).dict() == data
        dx['A-B'] = 3
        assert dx['A-B'] == 3
        assert dx.a_b == 2
        del dx['A-B']
        assert dx.dict() == {'a_b': 2}
        assert dx.a_b == 2
