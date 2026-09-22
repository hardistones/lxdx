# SPDX-FileCopyrightText: 2021-2026 @github.com/hardistones
# SPDX-License-Identifier: BSD-3-Clause

import pytest
from lxdx import Dixt


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

    @pytest.mark.parametrize('nested', [{}, {'x': 1}])
    def test_mapping_is_not_submap_of_scalar(self, nested):
        assert Dixt(a=nested).is_submap_of({'a': 2}) is False

    @pytest.mark.parametrize('nested', [{}, {'x': 1}])
    def test_scalar_is_not_supermap_of_mapping(self, nested):
        assert Dixt(a=2).is_supermap_of({'a': nested}) is False

    @pytest.mark.parametrize('nested', [False, True], ids=['root', 'nested'])
    @pytest.mark.parametrize('hide_submap, hide_supermap, expected', [
        (True, True, True),
        (True, False, True),
        (False, True, False),
    ], ids=['both-hidden', 'submap-hidden', 'supermap-hidden'])
    def test_hidden_fields_are_excluded_from_map_comparison(
            self, nested, hide_submap, hide_supermap, expected):
        """Ignore hidden requirements; hidden reference keys cannot satisfy visible ones."""
        class HiddenValue:
            def __eq__(self, other):
                raise AssertionError('Hidden values must not be compared')

            def __ne__(self, other):
                raise AssertionError('Hidden values must not be compared')

        submap = Dixt(visible=1, secret=HiddenValue())
        supermap = Dixt(visible=1, secret=HiddenValue())
        if hide_submap:
            submap.keymeta('secret', hidden=True)
        if hide_supermap:
            supermap.keymeta('secret', hidden=True)
        if nested:
            submap, supermap = Dixt(child=submap), Dixt(child=supermap)

        assert submap.is_submap_of(supermap) is expected
        assert supermap.is_supermap_of(submap) is expected

    @pytest.mark.parametrize('method', ['is_submap_of', 'is_supermap_of'])
    def test_map_comparison_rejects_none_argument(self, method):
        """Reject None instead of silently treating it as an empty mapping."""
        with pytest.raises(TypeError):
            getattr(Dixt(a=1), method)(None)

    @pytest.mark.parametrize('method', ['is_submap_of', 'is_supermap_of'])
    def test_mapping_type_values_are_compared_as_scalars(self, method):
        """Compare the dict type as a value, rather than a mapping instance."""
        dx = Dixt(value=dict)
        assert getattr(dx, method)({'value': dict}) is True

    @pytest.mark.parametrize('method', ['is_submap_of', 'is_supermap_of'])
    def test_scalar_with_keys_attribute_does_not_match_mapping(self, method):
        """Return False rather than recursing into a scalar with a keys attribute."""
        class ValueWithKeys:
            keys = ('data',)

        submap = Dixt(value=ValueWithKeys())
        supermap = Dixt(value={})
        if method == 'is_submap_of':
            assert submap.is_submap_of(supermap) is False
        else:
            assert supermap.is_supermap_of(submap) is False

    @pytest.mark.parametrize('method', ['is_submap_of', 'is_supermap_of'])
    def test_mapping_with_nan_is_its_own_submap_and_supermap(self, method):
        """Preserve reflexive containment for mappings with the same NaN object."""
        dx = Dixt(value=float('nan'))
        assert dx == dx
        assert getattr(dx, method)(dx) is True

    @pytest.mark.parametrize('method', ['is_submap_of', 'is_supermap_of'])
    def test_map_comparison_supports_ellipsis_key(self, method):
        """Accept Ellipsis as a stored key instead of treating it as missing."""
        dx = Dixt({Ellipsis: 1})
        assert getattr(dx, method)(dx) is True

    @pytest.mark.parametrize('method', ['is_submap_of', 'is_supermap_of'])
    @pytest.mark.parametrize('hide_contents', [False, True], ids=['empty', 'hidden-only'])
    def test_none_value_does_not_match_empty_visible_mapping(self, method, hide_contents):
        """Keep None distinct from an empty mapping, including one with hidden contents."""
        child = Dixt(secret=1) if hide_contents else Dixt()
        if hide_contents:
            child.keymeta('secret', hidden=True)
        submap, supermap = Dixt(value=None), Dixt(value=child)

        if method == 'is_submap_of':
            assert submap.is_submap_of(supermap) is False
        else:
            assert supermap.is_supermap_of(submap) is False

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

    def test_reverse_does_not_hash_hidden_values(self):
        """Skip hidden unhashable values instead of processing them during reversal."""
        dx = Dixt(visible=7, secret={'nested': 1})
        dx.keymeta('secret', hidden=True)
        assert dx.reverse().dict() == {7: 'visible'}
        assert dx.whats_hidden() == ('secret',)

    @pytest.mark.parametrize("arg", [[1, 2, 3], {2: 200}, {200, 300}])
    def test_reverse_raise_error_on_hashable_values(self, arg):
        with pytest.raises(TypeError):
            Dixt(a=100, b=arg).reverse()
