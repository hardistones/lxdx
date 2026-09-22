# SPDX-FileCopyrightText: 2021-2026 @github.com/hardistones
# SPDX-License-Identifier: BSD-3-Clause

import pytest
from lxdx import Dixt


class TestUpdate:

    def test_value_is_forced_to_be_none(self):
        with pytest.raises(TypeError):
            Dixt(a=1, b=2).update(None)

    def test_value_is_dict(self):
        dx = Dixt(a=1, b=2)
        dx.update({'c': 3})
        assert dx == Dixt(a=1, b=2, c=3)

    def test_value_is_dixt(self):
        dx = Dixt(a=1, b=2)
        dx.update(Dixt(d=4))
        assert dx == Dixt(a=1, b=2, d=4)

    def test_value_is_in_kwargs_only(self):
        dx = Dixt(a=1, b=2)
        dx.update(x=3, y=4)
        assert dx == Dixt(a=1, b=2, x=3, y=4)

    def test_value_is_iterable_key_value_pairs(self):
        dx = Dixt(a=1, b=2)
        dx.update((('x', 24), ('y', 25)))
        assert dx == Dixt(a=1, b=2, x=24, y=25)

    def test_accepts_zip_iterator(self):
        """Consume zipped pairs to replace existing values and add new keys."""
        dx = Dixt(a=0, keep=2)
        dx.update(zip(['a', 'b'], [1, 3]))
        assert dx.dict() == {'a': 1, 'keep': 2, 'b': 3}

    def test_accepts_generator_of_pairs(self):
        """Accept a generator of pairs without requiring list conversion."""
        dx = Dixt(a=0, keep=2)
        pairs = ((key, value) for key, value in [('a', 1), ('b', 3)])
        dx.update(pairs)
        assert dx.dict() == {'a': 1, 'keep': 2, 'b': 3}

    @pytest.mark.parametrize('input_kind', ['original-key', 'alias', 'kwargs'])
    def test_update_changes_hidden_destination_without_unhiding_it(self, input_kind):
        """Update a hidden destination by original key or alias and retain its flag."""
        dx = Dixt({'Secret-Key': {'old': 1}, 'visible': 2})
        dx.keymeta('Secret-Key', hidden=True)
        value = {'new': 3}

        if input_kind == 'original-key':
            dx.update({'Secret-Key': value})
        elif input_kind == 'alias':
            dx.update({'secret_key': value})
        else:
            dx.update(secret_key=value)

        assert isinstance(dx.secret_key, Dixt)
        assert dx['Secret-Key'] == {'new': 3}
        assert dx.dict() == {'visible': 2}
        assert dx.keymeta('Secret-Key') == {'secret_key': {'hidden': True}}

    def test_combination_of_dict_and_kwargs(self):
        dx = Dixt(a=1, b=2)
        dx.update({'c': 3}, d={'dd': 44})
        assert dx == Dixt(a=1, b=2, c=3, d=Dixt(dd=44))

    def test_combination_of_dixt_and_kwargs(self):
        dx = Dixt(a=1, b=2)
        dx.update(Dixt(e=5, f=Dixt(g=7)))
        assert dx == Dixt(a=1, b=2, e=5, f=Dixt(g=7))

    def test_combination_of_key_value_pairs_and_kwargs(self):
        dx = Dixt(a=1, b=2)
        dx.update((('e', 5),), x=[1, 2])
        assert dx == {'a': 1, 'b': 2, 'e': 5, 'x': [1, 2]}

    def test_raises_error_argument_is_not_iterable_key_value_pairs(self):
        for arg in ['string', ['list', 1], 1234]:
            with pytest.raises((ValueError, TypeError)):
                Dixt(a=1, b=2).update(arg, x=[1, 2])
