# SPDX-FileCopyrightText: 2021-2026 @github.com/hardistones
# SPDX-License-Identifier: BSD-3-Clause

import pytest
from collections import ChainMap, OrderedDict
from lxdx import Dixt


class TestDiff:

    @pytest.mark.parametrize('in_list', [False, True])
    def test_nested_mapping_order_does_not_create_differences(self, in_list):
        left = ChainMap({'nested': OrderedDict([('a', 1), ('b', 2)])})
        right = ChainMap({'nested': OrderedDict([('b', 2), ('a', 1)])})
        # OrderedDict equality is order-sensitive; mapping diffs are not.
        assert left != right
        if in_list:
            left, right = [left], [right]
        assert Dixt(value=left).diff({'value': right}) == []

    def test_equal_mappings_inside_nested_lists_do_not_create_differences(self):
        """Collapse equal mappings through nested lists without false differences."""
        left = ChainMap({'nested': OrderedDict([('a', 1), ('b', 2)])})
        right = ChainMap({'nested': OrderedDict([('b', 2), ('a', 1)])})
        assert Dixt(value=[[left]]).diff({'value': [[right]]}) == []

    def test_equal_dicts_return_empty_list(self):
        a = Dixt(x=1, y=2)
        b = Dixt(x=1, y=2)
        assert a.diff(b) == []

    @pytest.mark.parametrize('same_object', [True, False], ids=['self', 'shared-nan'])
    def test_equal_mappings_with_shared_nan_have_no_difference(self, same_object):
        """Respect mapping equality when both sides contain the same NaN object."""
        value = float('nan')
        left = Dixt(value=value)
        right = left if same_object else Dixt(value=value)
        assert left == right
        assert left.diff(right) == []

    def test_equal_empty_dicts_return_empty_list(self):
        assert Dixt().diff(Dixt()) == []
        assert Dixt().diff({}) == []

    @pytest.mark.parametrize('left, right', [
        ({}, None),
        (None, {}),
    ], ids=['mapping-to-none', 'none-to-mapping'])
    def test_reports_empty_mapping_and_none_as_different(self, left, right):
        """Report changes between an empty mapping and None in either direction."""
        result = Dixt(a=left).diff({'a': right})
        assert len(result) == 1
        self_diff, other_diff = result[0]
        assert self_diff.dict() == {'a': left}
        assert other_diff.dict() == {'a': right}

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
        b = {'x': 1, 'nested': {'p': 10, 'same': 'val'}}
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

    @pytest.mark.parametrize('container', ['list', 'mapping'])
    @pytest.mark.parametrize('side', ['self', 'other'])
    def test_non_builtin_in_one_sided_container_uses_repr(self, container, side):
        """Convert custom leaves to repr even when their whole container is added or removed."""
        class CustomValue:
            def __repr__(self):
                return 'CustomValue()'

        value = CustomValue()
        if container == 'list':
            data = {'value': [value]}
            expected = {'value': ['CustomValue()']}
        else:
            data = {'value': {'leaf': value}}
            expected = {'value': {'leaf': 'CustomValue()'}}

        left, right = Dixt(data), Dixt()
        expected_left, expected_right = expected, {}
        if side == 'other':
            left, right = right, left
            expected_left, expected_right = expected_right, expected_left

        result = left.diff(right)
        assert len(result) == 1
        self_diff, other_diff = result[0]
        assert self_diff.dict() == expected_left
        assert other_diff.dict() == expected_right

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

    @pytest.mark.parametrize('invalid', ['string', 123, [1, 2], {1, 2}, object()])
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

    @pytest.mark.parametrize('left, right', [
        ([], [Ellipsis]),
        ([Ellipsis], []),
        ([[Ellipsis]], [[]]),
    ])
    def test_literal_ellipsis_in_list_does_not_hide_a_length_difference(self, left, right):
        result = Dixt(x=left).diff({'x': right})

        assert len(result) == 1
        assert result[0][0].dict() == {'x': left}
        assert result[0][1].dict() == {'x': right}

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

    @pytest.mark.parametrize('list_depth', [0, 1, 2], ids=['mapping', 'list', 'nested-list'])
    def test_nested_hidden_values_are_never_compared(self, list_depth):
        """Skip hidden values even when their equality method would raise."""
        class HiddenValue:
            def __eq__(self, other):
                raise AssertionError('Hidden values must not be compared')

        left = Dixt(visible=1, secret=HiddenValue())
        right = Dixt(visible=1, secret=HiddenValue())
        left.keymeta('secret', hidden=True)
        right.keymeta('secret', hidden=True)
        for _ in range(list_depth):
            left, right = [left], [right]

        assert Dixt(value=left).diff({'value': right}) == []

    @pytest.mark.parametrize('hidden_side', [0, 1], ids=['self-hidden', 'other-hidden'])
    def test_visible_key_does_not_match_equal_hidden_value(self, hidden_side):
        """Report a visible key even when its hidden counterpart has the same value."""
        left, right = Dixt(secret=2), Dixt(secret=2)
        (left, right)[hidden_side].keymeta('secret', hidden=True)

        result = Dixt(rows=[[left]]).diff({'rows': [[right]]})

        assert len(result) == 1
        assert result[0][hidden_side].dict() == {'rows': [[{}]]}
        assert result[0][1 - hidden_side].dict() == {'rows': [[{'secret': 2}]]}

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
