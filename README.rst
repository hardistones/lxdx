lxdx
====

``lxdx`` is an "extended" Python ``dict`` with attribute-like accessibility.
Other than the usual ``dict`` operations, functions and methods,
some useful functions are incorporated as well.

Only supports Python 3.9+, due to the usage of the `union operator`_ for ``dict``.

Why this project?
-----------------
* Hobbies and curiosities. Just for the fun of programming.
* ``dataclass`` is not cut for modelling hierarchical data.
* Brackets when accessing multi-layer data is too many. `Dot notation`_ may be a cleaner way.
* Introduce utility functions like ``get_from(path)``, inspired from `JsonPath`_, for programmability.
* Ability to add metadata to the items.

Installation
------------
``lxdx`` is available in `PyPI <https://pypi.org/project/lxdx>`_, and installable via ``pip``:

.. code-block::

    pip install lxdx


Examples
--------
.. code-block:: python

    from lxdx import Dixt

    assert Dixt() == {}
    assert Dixt({1: 1, 'alpha': 'α'}) == {1: 1, 'alpha': 'α'}
    assert Dixt(alpha='α', beta='β') == {'alpha': 'α', 'beta': 'β'}
    assert Dixt(alpha='α', beta='β').is_supermap_of({'beta': 'β'})

    # data can be deeply nested
    data = {'Accept-Encoding': 'gzip', 'metadata': {'Content-Type': 'application/json'}}
    dx = Dixt(**data)

    # update dx using the union operator
    dx |= {'other': 'dict or Dixt obj'}

    # 'Normalise' the keys to use it as attributes additionally.
    assert dx['Accept-Encoding'] == dx.accept_encoding
    del dx.accept_encoding
    print(dx.metadata.CONTENT_TYPE)

    # Instead of
    dx['a-list'][1]['obj-attr'] = 'value'

    # Is way cleaner
    dx.a_list[1].obj_attr = 'value'

    # Programmatically get values
    assert dx.a_list[1].obj_attr == dx.get_from('$.a_list[1].obj_attr')

    json_str = '{"a": "JSON string"}'
    assert Dixt.from_json(json_str).json() == json_str

Documentation
-------------
Full documentation is at https://hardistones.github.io/lxdx.

Future
------
``lxdx`` is supposed to be a library of "extended" ``list`` and ``dict``. For now there's no use case for the ``list`` extension.

**To be supported**

- User-defined meta specification.

License
-------
This project and all its files are licensed under the 3-Clause BSD License.

    Copyright (c) 2021, @github.com/hardistones
    All rights reserved.

    Redistribution and use in source and binary forms, with or without modification,
    are permitted provided that the following conditions are met:

    1. Redistributions of source code must retain the above copyright notice, this
       list of conditions and the following disclaimer.

    2. Redistributions in binary form must reproduce the above copyright notice,
       this list of conditions and the following disclaimer in the documentation
       and/or other materials provided with the distribution.

    3. Neither the name of the copyright holder nor the names of its contributors
       may be used to endorse or promote products derived from this software without
       specific prior written permission.

    THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
    ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
    WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
    DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR
    ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
    (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
    LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
    ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
    (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
    SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


.. References
.. _union operator: https://www.python.org/dev/peps/pep-0584
.. _dot notation: https://en.wikipedia.org/wiki/Property_(programming)#Dot_notation
.. _JsonPath: https://github.com/json-path/JsonPath
