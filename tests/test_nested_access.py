# SPDX-FileCopyrightText: 2021-2026 @github.com/hardistones
# SPDX-License-Identifier: BSD-3-Clause

import pytest
from lxdx import Dixt


INVALID_QUERIES = {
    IndexError: [
        '$.body.e[100]',
        '$.body.e[-10]',
    ],
    KeyError: [
        '$.extra.info',
        '$.not_heading.nonexistent',
        '$.headers.nonexistent',
        '$.nonexistent[0]',
        '$.body[1:]',
    ],
    TypeError: [123, object()],
    ValueError: [
        '',
        'any.string',
        '$',
        '$.',
        '$..',
        '$[0]',
        'a.b[0]',
        '$.headers[2',
        '$.body.f[]',
    ],
}


VALID_QUERIES = [
    ('$.headers.content_type', 'application/json'),
    ('$.extra', 'info'),
    ('$.body.e[0]', 2),
    ('$.body.e[-2]', 2),
    ('$.body.e.[0]', 2),
    ('$.body.e.[-2]', 2),
    ('$.body.e[1].g', 9.806),
    ('$.body.f.y[1][0]', 8),
    ('$.body.e[1:]', [{'g': 9.806}]),
    ('$.body.e.[1:]', [{'g': 9.806}]),
]


class TestNestedAccess:

    def test_traversals_with_nested_objects(self, dixt):
        assert dixt.body.e[1] == {"g": 9.806}
        assert dixt['body']['e'][1] == {"g": 9.806}

        assert dixt.body.e[1].g == 9.806
        assert dixt['body']['e'][1]['g'] == 9.806

        assert dixt.body.f.y[1] == [8]
        assert dixt['body']['f']['y'][1] == [8]

        assert dixt.body.f.y[1][0] == 8
        assert dixt['body']['f']['y'][1][0] == 8

    def test_operations_on_nested_objects(self, dixt):
        dixt.body.f.y[1].extend(['σ', 'φ', 'θ'])
        assert dixt.body.f.y[1] == [8, 'σ', 'φ', 'θ']

        dixt.body.e[1] = {'del-ta': 'd'}
        # AttributeError: Since the assignment is handled by the list object,
        #                 the dict is not converted to a Dixt object.
        #                 Should wrap with Dixt first
        #                 before appending/adding to the list.
        # dixt.body.e[1].del_ta = 'δ'

        dixt.body.e[1] = Dixt({'del-ta': 'δ'})
        assert dixt.body.e[1] == {'del-ta': 'δ'}
        assert dixt.body.e[1].del_ta == 'δ'

    def test_get_from(self, dixt):
        for path, expected_value in VALID_QUERIES:
            assert dixt.get_from(path) == expected_value

    def test_get_from_invalid_path(self, dixt):
        for exc, queries in INVALID_QUERIES.items():
            for path in queries:
                with pytest.raises(exc):
                    dixt.get_from(path)

    def test_set_by_path(self, dixt):
        dixt.set_by_path('$.headers.content_type', 'application/text')
        assert dixt['headers']['Content-Type'] == 'application/text'

        dixt.set_by_path('$.headers.["Content-Type"]', 'application/json')
        assert dixt['headers']['Content-Type'] == 'application/json'

        dixt.set_by_path('$.body.e[0]', 22)
        assert dixt['body']['e'][0] == 22
        assert dixt.get_from('$.body.e[0]') == 22

        dixt.set_by_path('$.body.f.x', 'xi')
        assert dixt['body']['f']['x'] == 'xi'
        assert dixt.get_from('$.body.f.x') == 'xi'

        dixt.set_by_path('$.body.f.y[0].p', 55)
        assert dixt['body']['f']['y'][0]['p'] == 55
        assert dixt.get_from('$.body.f.y[0].p') == 55

        dixt.set_by_path('$.body.f.y[1][0]', 88)
        assert dixt['body']['f']['y'][1][0] == 88
        assert dixt.get_from('$.body.f.y[1][0]') == 88

    def test_set_by_path_invalid_path(self, dixt):
        for exc, queries in INVALID_QUERIES.items():
            for path in queries:
                with pytest.raises(exc):
                    dixt.set_by_path(path, object())
