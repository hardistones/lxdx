# SPDX-FileCopyrightText: 2021-2026 @github.com/hardistones
# SPDX-License-Identifier: BSD-3-Clause

import pytest
from collections import OrderedDict
from lxdx import Dixt


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

    def test_empty_mapping_is_not_equal_to_none(self):
        dx = Dixt()
        other = None
        assert dx != other
        assert other != dx

    @pytest.mark.parametrize('nested', [False, True], ids=['root', 'nested'])
    def test_hidden_values_are_excluded_from_equality(self, nested):
        class HiddenValue:
            def __eq__(self, other):
                raise AssertionError('Hidden values must not be compared')

            def __ne__(self, other):
                raise AssertionError('Hidden values must not be compared')

        left = Dixt(visible=1, secret=HiddenValue())
        right = Dixt(visible=1, secret=HiddenValue())
        left.keymeta('secret', hidden=True)
        right.keymeta('secret', hidden=True)
        expected = {'visible': 1}
        if nested:
            left, right = Dixt(child=left), Dixt(child=right)
            expected = {'child': expected}

        assert left == right
        assert not (left != right)
        assert left == expected
        assert expected == left
        assert not (left != expected)
        assert not (expected != left)

    def test_visible_entry_does_not_equal_matching_hidden_entry(self):
        visible, hidden = Dixt(secret=1), Dixt(secret=1)
        hidden.keymeta('secret', hidden=True)
        assert visible != hidden
        assert hidden != visible
        assert not (visible == hidden)
        assert not (hidden == visible)

    def test_not_operator_return_false_when_empty_and_true_otherwise(self, dixt):
        assert not Dixt()
        assert not (not dixt)
        assert dixt
        assert not Dixt()

    def test_or_operator_should_choose_the_second_option_when_first_is_empty(self, dixt):
        assert (Dixt() or 'else') == 'else'
        assert (Dixt() or {1: 1}) == {1: 1}
        assert (Dixt() or dixt) == dixt
