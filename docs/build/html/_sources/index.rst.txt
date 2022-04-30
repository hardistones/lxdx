.. lxdx documentation master file, created by
   sphinx-quickstart on Mon Oct  4 12:26:30 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

lxdx
====

.. meta::
   :description: lxdx documentation
   :keywords: lxdx, Dixt, dict, extended, metadata, python

.. toctree::
   :hidden:
   :maxdepth: 2
   :caption: Contents:

   getting-started
   Reference <modules>


.. toctree::
   :hidden:
   :caption: Project

   Changelog <changelog>
   License <license>
   Github <https://github.com/hardistones/lxdx>


lxdx is a library containing an "extended" ``dict`` called ``Dixt``.

``Dixt`` is compatible to ``dict``, i.e., ``Dixt`` can do what ``dict`` can -- but not the opposite.
``Dixt`` includes more useful methods and operations, see `examples`_.


Why this project?
-----------------

* Hobbies and curiosities. Just for the fun of programming.
* ``dataclass`` is not cut for modelling hierarchical data.
* Brackets when accessing multi-layer data is too many. `Dot notation`_ may be a cleaner way.
* Introduce utility methods like ``get_from(path)``, inspired from `JsonPath`_, for programmability.

Supported Python version
------------------------
lxdx only supports **Python 3.9+**, due to the usage of the `union operator`_ for ``dict``.


Installation
------------
lxdx is available in `PyPI <https://pypi.org/project/lxdx>`_, and installable via ``pip``:

.. code-block:: bash

   pip install lxdx
..

|

For bugs, feature, and pull requests:

- `Github Issues <https://github.com/hardistones/lxdx/issues>`_

.. _dot notation: https://en.wikipedia.org/wiki/Property_(programming)#Dot_notation
.. _JsonPath: https://github.com/json-path/JsonPath
.. _union operator: https://www.python.org/dev/peps/pep-0584
.. _examples: ../html/examples.html

..
   Indices and tables
   ------------------

   * :ref:`genindex`
   * :ref:`modindex`
   * :ref:`search`
