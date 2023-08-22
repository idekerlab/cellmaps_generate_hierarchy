=====
Usage
=====

This page should provide information on how to use cellmaps_generate_hierarchy

In a project
--------------

To use cellmaps_generate_hierarchy in a project::

    import cellmaps_generate_hierarchy


Needed files
------------

The output directory for co-embedding is required (see `Cell Maps Coembedding <https://github.com/idekerlab/cellmaps_coembedding/>`__). 


On the command line
---------------------

For information invoke :code:`cellmaps_generate_hierarchycmd.py -h`

**Example usage**

.. code-block::

   cellmaps_generate_hierarchycmd.py ./cellmaps_generate_hierarchy --coembedding_dirs ./cellmaps_coembedding_outdir 

Via Docker
---------------

**Example usage**


.. code-block::

   docker run -v `pwd`:`pwd` -w `pwd` idekerlab/cellmaps_generate_hierarchy:0.1.0 cellmaps_generate_hierarchycmd.py ./cellmaps_generate_hierarchy --coembedding_dirs ./cellmaps_coembedding_outdir 


