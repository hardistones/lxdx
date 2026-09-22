# SPDX-FileCopyrightText: 2021-2026 @github.com/hardistones
# SPDX-License-Identifier: BSD-3-Clause

import pytest
from lxdx import Dixt


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

    @pytest.mark.parametrize('key', ['items', 123], ids=['method-name', 'integer'])
    def test_returns_default_for_missing_method_name_or_integer_key(self, key):
        dx = Dixt()
        default = object()
        assert dx.getx(key, default=default) is default

    @pytest.mark.parametrize('key', ['Secret-Key', 'secret_key'])
    def test_get_and_getx_can_read_hidden_entries(self, key):
        dx = Dixt({'Secret-Key': 1})
        dx.keymeta('Secret-Key', hidden=True)
        assert dx.get(key, 'missing') == 1
        assert dx.getx(key, default='missing') == 1

    def test_raises_error_when_defaults_dont_match_with_attrs_len(self, dixt):
        with pytest.raises(ValueError):
            dixt.getx('ghost', 'invisible', default=(1, 2, 3))

        with pytest.raises(ValueError):
            dixt.getx('ghost', 'invisible', default=[3])
