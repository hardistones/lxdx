import pytest

from lxdx import Dixt


@pytest.fixture
def dixt():
    return Dixt({
        'headers': {
            'Accept-Encoding': 'gzip',
            'Content-Type': 'application/json'
        },
        'body': {
            'C-D': 1.2,
            'e': [2, {'g': 9.806}],
            'f': {'x': None, 'y': [{'p': 5}, [8]]}
        },
        'extra': 'info'
    })


@pytest.fixture
def dict_equiv():
    return {
        'headers': {
            'Accept-Encoding': 'gzip',
            'Content-Type': 'application/json'
        },
        'body': {
            'C-D': 1.2,
            'e': [2, {'g': 9.806}],
            'f': {'x': None, 'y': [{'p': 5}, [8]]}
        },
        'extra': 'info'
    }
