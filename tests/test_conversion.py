# SPDX-FileCopyrightText: 2021-2026 @github.com/hardistones
# SPDX-License-Identifier: BSD-3-Clause

import json
import pytest
from lxdx import Dixt


class TestConversion:

    @pytest.mark.parametrize('convert', [str, repr], ids=['str', 'repr'])
    def test_text_conversion_skips_hidden_values_at_each_level(self, convert):
        """Render nested visible data without invoking hidden values' repr methods."""
        class HiddenValue:
            def __repr__(self):
                raise AssertionError('Hidden values must not be rendered')

        child = Dixt(visible=1, secret=HiddenValue())
        child.keymeta('secret', hidden=True)
        dx = Dixt(secret=HiddenValue(), child=child, rows=[child], pair=(child,))
        dx.keymeta('secret', hidden=True)
        expected = {'child': {'visible': 1}, 'rows': [{'visible': 1}],
                    'pair': ({'visible': 1},)}
        assert convert(dx) == convert(expected)

    @pytest.mark.parametrize('conversion', ['dict', 'json'])
    def test_data_conversion_skips_hidden_values_at_each_level(self, conversion):
        """Exclude hidden values from nested mappings, lists, and tuples."""
        child = Dixt(visible=1, secret=object())
        child.keymeta('secret', hidden=True)
        dx = Dixt(secret=object(), child=child, rows=[child], pair=(child,))
        dx.keymeta('secret', hidden=True)
        expected = {'child': {'visible': 1}, 'rows': [{'visible': 1}],
                    'pair': ({'visible': 1},)}

        if conversion == 'dict':
            assert dx.dict() == expected
        else:
            expected['pair'] = [{'visible': 1}]
            assert json.loads(dx.json()) == expected

    @pytest.mark.parametrize('conversion', ['dict', 'json'])
    def test_conversion_handles_hidden_child_in_plain_dict_inserted_into_list(self, conversion):
        """Convert hidden-bearing Dixt children inside plain dictionaries added to lists."""
        child = Dixt(visible=1, secret=2)
        child.keymeta('secret', hidden=True)
        dx = Dixt(rows=[])
        dx.rows.append({'child': child})

        result = dx.dict() if conversion == 'dict' else json.loads(dx.json())

        assert type(result['rows'][0]['child']) is dict
        assert result == {'rows': [{'child': {'visible': 1}}]}

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

    def test_dict_converts_mapping_inside_tuple(self):
        dx = Dixt(a=({'x': 1},))
        result = dx.dict()
        assert isinstance(result['a'], tuple)
        assert type(result['a'][0]) is dict
        assert result == {'a': ({'x': 1},)}

    def test_json_conversion_to_json_format(self, dixt, dict_equiv):
        json_equivalent = json.dumps(dict_equiv)
        assert dixt.json() == json_equivalent

    def test_from_json(self, dict_equiv):
        json_string = json.dumps(dict_equiv)
        dx = Dixt.from_json(json_string)
        assert dx == dict_equiv

    def test_json_converts_mapping_inside_tuple(self):
        dx = Dixt(a=({'x': 1},))
        assert json.loads(dx.json()) == {'a': [{'x': 1}]}


def _assert_obj_tree_has_no_dixt_object(obj):
    assert not isinstance(obj, Dixt)
    if isinstance(obj, dict):
        for key in obj:
            _assert_obj_tree_has_no_dixt_object(obj[key])
    elif isinstance(obj, list):
        for item in obj:
            _assert_obj_tree_has_no_dixt_object(item)
