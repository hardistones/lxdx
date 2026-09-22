# SPDX-FileCopyrightText: 2021-2026 @github.com/hardistones
# SPDX-License-Identifier: BSD-3-Clause

from lxdx import Dixt


class TestContains:

    def test_membership_and_contains_follow_hidden_flag_changes(self):
        """Exclude hidden keys from membership checks and restore them on reset."""
        dx = Dixt({'Secret-Key': 1, 'visible': 2})
        dx.keymeta('Secret-Key', hidden=True)
        assert 'Secret-Key' not in dx
        assert not ('Secret-Key' in dx)
        assert not dx.contains('Secret-Key')
        assert not dx.contains('visible', 'Secret-Key')
        assert dx.contains('visible', 'Secret-Key', assert_all=False) == (True, False)

        dx.keymeta('Secret-Key', hidden=False)
        assert 'Secret-Key' in dx
        assert not ('Secret-Key' not in dx)
        assert dx.contains('visible', 'Secret-Key')
        assert dx.contains('visible', 'Secret-Key', assert_all=False) == (True, True)

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
