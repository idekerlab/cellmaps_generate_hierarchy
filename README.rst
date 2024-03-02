=============================
Cell Maps Generate Hierarchy
=============================


.. image:: https://img.shields.io/pypi/v/cellmaps_generate_hierarchy.svg
        :target: https://pypi.python.org/pypi/cellmaps_generate_hierarchy

.. image:: https://app.travis-ci.com/idekerlab/cellmaps_generate_hierarchy.svg?branch=main
        :target: https://app.travis-ci.com/github/idekerlab/cellmaps_generate_hierarchy

.. image:: https://readthedocs.org/projects/cellmaps-generate-hierarchy/badge/?version=latest
        :target: https://cellmaps-generate-hierarchy.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status

Generates hierarchy from `Cell Maps Coembedding <https://cellmaps-coembedding.readthedocs.io/>`__ using `HiDeF <https://github.com/fanzheng10/HiDeF/>`__

* Free software: MIT license
* Documentation: https://cellmaps-generate-hierarchy.readthedocs.io.
* Source code: https://github.com/idekerlab/cellmaps_generate_hierarchy

Dependencies
------------

* `cellmaps_utils <https://pypi.org/project/cellmaps-utils>`__
* `tqdm <https://pypi.org/project/tqdm>`__
* `pandas <https://pypi.org/project/pandas>`__
* `numpy <https://pypi.org/project/numpy>`__
* `ndex2 <https://pypi.org/project/ndex2>`__
* `HiDeF <https://pypi.org/project/hidef>`__

Compatibility
-------------

* Python 3.8+

Installation
------------

.. code-block::

   git clone https://github.com/idekerlab/cellmaps_generate_hierarchy
   cd cellmaps_generate_hierarchy
   make dist
   pip install dist/cellmaps_generate_hierarchy*whl


Run **make** command with no arguments to see other build/deploy options including creation of Docker image 

.. code-block::

   make

Output:

.. code-block::

   clean                remove all build, test, coverage and Python artifacts
   clean-build          remove build artifacts
   clean-pyc            remove Python file artifacts
   clean-test           remove test and coverage artifacts
   lint                 check style with flake8
   test                 run tests quickly with the default Python
   test-all             run tests on every Python version with tox
   coverage             check code coverage quickly with the default Python
   docs                 generate Sphinx HTML documentation, including API docs
   servedocs            compile the docs watching for changes
   testrelease          package and upload a TEST release
   release              package and upload a release
   dist                 builds source and wheel package
   install              install the package to the active Python's site-packages
   dockerbuild          build docker image and store in local repository
   dockerpush           push image to dockerhub

For developers
-------------------------------------------

To deploy development versions of this package
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Below are steps to make changes to this code base, deploy, and then run
against those changes.

#. Make changes

   Modify code in this repo as desired

#. Build and deploy

.. code-block::

    # From base directory of this repo cellmaps_generate_hierarchy
    pip uninstall cellmaps_generate_hierarchy -y ; make clean dist; pip install dist/cellmaps_generate_hierarchy*whl



Needed files
------------

The output directory for co-embedding is required (see `Cell Maps Coembedding <https://github.com/idekerlab/cellmaps_coembedding/>`__). 

Usage
-----

For information invoke :code:`cellmaps_generate_hierarchycmd.py -h`

**Example usage**

.. code-block::

   cellmaps_generate_hierarchycmd.py ./cellmaps_generate_hierarchy --coembedding_dirs ./cellmaps_coembedding_outdir 

Via Docker
~~~~~~~~~~~~~~~~~~~~~~

**Example usage**


.. code-block::

   Coming soon...

Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
.. _NDEx: http://www.ndexbio.org
