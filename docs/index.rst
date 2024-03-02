=============================
Cell Maps Generate Hierarchy
=============================


.. image:: https://img.shields.io/pypi/v/cellmaps_generate_hierarchy.svg
        :target: https://pypi.python.org/pypi/cellmaps_generate_hierarchy

.. image:: https://app.travis-ci.com/idekerlab/cellmaps_generate_hierarchy.svg?branch=main
        :target: https://app.travis-ci.com/idekerlab/cellmaps_generate_hierarchy

The Cell Maps Generate Hierarchy Tool generates hierarchy from `Cell Maps Coembedding <https://cellmaps-coembedding.readthedocs.io/>`__ using `HiDeF <https://github.com/fanzheng10/HiDeF/>`__.
It accepts one or more coembedding directories corresponding to multiple folds of the same data.

The tool creates an output directory where results are stored and registered within `Research Object Crates (RO-Crate) <https://www.researchobject.org/ro-crate>`__ using
the `FAIRSCAPE-cli <https://pypi.org/project/fairscape-cli>`__.

Overview of Cell Maps Generate Hierarchy

.. image:: images/generate_hierarchy_overview.png
  :alt: Overview of Cell Maps Generate Hierarchy which calculating cosine similarities for embeddings followed by protein to protein interaction networks creation, HiDeF invocation to generate hierarchy, and finally hierarchy "maturation"

..
    The generate_hierarchy_overview.png image is from this google doc: https://docs.google.com/drawings/d/1zx4Sv3e1iUNSlN4hixKJbtmVtPMlYv3tfvmgreB7ork/edit

* Free software: MIT license
* Source code: https://github.com/idekerlab/cellmaps_generate_hierarchy


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   usage
   inputs
   outputs
   modules
   developer
   authors
   history

Indices and tables
==================
* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
