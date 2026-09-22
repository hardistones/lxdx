# SPDX-FileCopyrightText: 2021-2026 @github.com/hardistones
# SPDX-License-Identifier: BSD-3-Clause

from copy import deepcopy
from lxdx import Dixt


class TestMiscellaneous:

    def test__dixt_object__must_deep_copyable(self):
        a = Dixt(a=1, b={'c': {'d': 4}})
        copied = deepcopy(a)
        assert id(a) != id(copied)
        a.b.c.d = 2
        assert a.b.c.d != copied.b.c.d
