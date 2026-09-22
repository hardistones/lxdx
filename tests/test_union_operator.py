# SPDX-FileCopyrightText: 2021-2026 @github.com/hardistones
# SPDX-License-Identifier: BSD-3-Clause

import pytest
from lxdx import Dixt


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

    @pytest.mark.parametrize('nested', [False, True], ids=['root', 'nested'])
    def test_union_excludes_hidden_left_values_from_result(self, nested):
        hidden = Dixt(secret=1)
        hidden.keymeta('secret', hidden=True)
        left = Dixt(child=hidden) if nested else hidden

        result = left | {'extra': 3}

        merged = result.child if nested else result
        assert 'secret' not in merged
        with pytest.raises(KeyError):
            merged['secret']
        assert merged.whats_hidden() == ()
        assert result['extra'] == 3
        assert result is not left
        assert left.dict() == ({'child': {}} if nested else {})
        assert hidden['secret'] == 1
        assert hidden.whats_hidden() == ('secret',)

    @pytest.mark.parametrize('left_type', [dict, Dixt], ids=['dict', 'dixt'])
    def test_union_does_not_preserve_hidden_right_values(self, left_type):
        right = Dixt(secret=2, hidden_only=3)
        right.keymeta('secret', 'hidden_only', hidden=True)

        result = left_type(secret=1) | right

        assert result == {'secret': 1}
        with pytest.raises(KeyError):
            result['hidden_only']
        if isinstance(result, Dixt):
            assert result.whats_hidden() == ()
        assert right['secret'] == 2
        assert right['hidden_only'] == 3
        assert set(right.whats_hidden()) == {'secret', 'hidden_only'}

    def test_union_excludes_matching_entries_hidden_on_both_sides(self):
        left = Dixt(secret=1, visible=2)
        right = Dixt(secret=3)
        left.keymeta('secret', hidden=True)
        right.keymeta('secret', hidden=True)

        result = left | right

        assert result.dict() == {'visible': 2}
        assert 'secret' not in result
        with pytest.raises(KeyError):
            result['secret']
        assert result.whats_hidden() == ()
        assert left['secret'] == 1
        assert left.whats_hidden() == ('secret',)
        assert right['secret'] == 3
        assert right.whats_hidden() == ('secret',)

    @pytest.mark.parametrize('right_type', [dict, Dixt], ids=['dict', 'dixt'])
    def test_union_uses_visible_right_value_without_changing_hidden_left_entry(self, right_type):
        left = Dixt(secret=1, visible=2)
        left.keymeta('secret', hidden=True)
        right = right_type(secret=3)

        result = left | right

        assert result['secret'] == 3
        assert 'secret' in result
        assert result.whats_hidden() == ()
        assert result.dict() == {'secret': 3, 'visible': 2}
        assert left['secret'] == 1
        assert left.whats_hidden() == ('secret',)

    def test_in_place_operation(self):
        dx = Dixt()
        dx |= {}
        assert dx == {}
        dx |= {1: 1}
        assert dx == {1: 1}
        dx |= [(1, 100), (2, 2)]
        assert dx == {1: 100, 2: 2}

    @pytest.mark.parametrize('left_type', [dict, Dixt], ids=['dict', 'dixt'])
    def test_in_place_union_does_not_preserve_hidden_right_values(self, left_type):
        right = Dixt(secret=2, hidden_only=3)
        right.keymeta('secret', 'hidden_only', hidden=True)
        dx = left_type(secret=1)

        dx |= right

        assert dx == {'secret': 1}
        with pytest.raises(KeyError):
            dx['hidden_only']
        if isinstance(dx, Dixt):
            assert dx.whats_hidden() == ()
        assert right['secret'] == 2
        assert right['hidden_only'] == 3
        assert set(right.whats_hidden()) == {'secret', 'hidden_only'}

    @pytest.mark.parametrize('right_type', [dict, Dixt], ids=['dict', 'dixt'])
    def test_in_place_union_makes_hidden_left_entry_visible_when_right_key_is_visible(self, right_type):
        dx = Dixt(secret=1, visible=2)
        dx.keymeta('secret', hidden=True)
        right = right_type(secret=3)

        dx |= right

        assert dx['secret'] == 3
        assert 'secret' in dx
        assert dx.whats_hidden() == ()
        assert dx.dict() == {'secret': 3, 'visible': 2}

    def test_in_place_union_preserves_left_entry_when_matching_right_entry_is_hidden(self):
        dx = Dixt(secret=1, visible=2)
        right = Dixt(secret=3)
        dx.keymeta('secret', hidden=True)
        right.keymeta('secret', hidden=True)

        dx |= right

        assert dx.dict() == {'visible': 2}
        assert dx['secret'] == 1
        assert 'secret' not in dx
        assert dx.whats_hidden() == ('secret',)
        assert dx.keymeta('secret') == {'secret': {'hidden': True}}
        assert right['secret'] == 3
        assert right.whats_hidden() == ('secret',)

    @pytest.mark.parametrize('other', [{}, {'extra': 3}], ids=['empty', 'add-key'])
    def test_in_place_union_preserves_unmatched_hidden_entries_in_left_operand(self, other):
        dx = Dixt(secret=1, visible=2)
        dx.keymeta('secret', hidden=True)

        dx |= other

        assert dx['secret'] == 1
        assert 'secret' not in dx
        assert dx.whats_hidden() == ('secret',)
        assert dx.keymeta('secret') == {'secret': {'hidden': True}}
        assert dx.dict() == {'visible': 2, **other}

    def test_in_place_union_updates_existing_references(self):
        """Mutate the original object so existing references see the union."""
        dx = Dixt(visible=1)
        reference = dx

        dx |= {'extra': 2}

        assert dx is reference
        assert reference.dict() == {'visible': 1, 'extra': 2}

    @pytest.mark.parametrize('left, right', [
        ({'A-B': 1}, {'a_b': 2}),
        ({'a_b': 1}, {'A-B': 2}),
        ({'A-B': 1}, {'A B': 2}),
        ({'A-B': 1, 'A B': 2}, {'A-B': 3}),
    ])
    def test_in_place_union_preserves_original_keys_and_alias_ownership(self, left, right):
        dx = Dixt(left)
        expected = Dixt(left | right)

        dx |= right

        assert dx.dict() == expected.dict()
        assert dx.a_b == expected.a_b

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
