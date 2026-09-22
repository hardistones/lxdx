# SPDX-FileCopyrightText: 2021-2026 @github.com/hardistones
# SPDX-License-Identifier: BSD-3-Clause

import pytest
from collections import ChainMap, OrderedDict
from lxdx import Dixt


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

    def test_recursive_merge_preserves_existing_chainmap_keys(self):
        """Merge a nested ChainMap without discarding its unmatched fields."""
        dx = Dixt(a=ChainMap({'change': 2}, {'keep': 1}))
        dx.merge_update({'a': {'change': 3}})
        assert dx.a == {'change': 3, 'keep': 1}

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

    def test_recurse_lists_merges_mappings_inside_nested_lists(self):
        """Recurse through nested lists and retain unmatched mapping fields."""
        dx = Dixt(a=[[{'keep': 1, 'change': 2}]])
        dx.merge_update({'a': [[{'change': 3}]]}, recurse_lists=True)
        assert dx.dict() == {'a': [[{'keep': 1, 'change': 3}]]}

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

    @pytest.mark.parametrize('key', [1, (1, 2)])
    def test_merge_update_adds_non_string_key(self, key):
        dx = Dixt()
        dx.merge_update({key: 'value'})
        assert dx == {key: 'value'}

    def test_recursive_list_merge_accepts_chainmap_elements(self):
        dx = Dixt(a=[ChainMap({'x': 1, 'keep': 2})])
        dx.merge_update({'a': [{'x': 10, 'new': 3}]}, recurse_lists=True)
        assert dx.a[0] == {'x': 10, 'keep': 2, 'new': 3}
