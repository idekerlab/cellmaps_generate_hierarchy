=====
Usage
=====

The tool is designed to generate interaction network's hierarchy based on a list of coembedding files. Coembedding directories,
containing coembedding files in TSV format should be provided to generate several interactomes, which are used to create a structured hierarchy.

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

**Usage**

.. code-block::

  cellmaps_generate_hierarchycmd.py [outdir] [--coembedding_dirs COEMBEDDINGDIRS [COEMBEDDINGDIRS ...]] [OPTIONS]

.. code-block::

  cellmaps_generate_hierarchycmd.py [outdir] [--mode ndexsave] [--ndexuser NDEXUSER] [--ndexpassword NDEXPASSWORD]

**Arguments**

- ``outdir``
    The directory where the output will be written to or directory where hierarchy.cx2 and parent_hierarchy.cx2 was
    saved.

*Possible modes*

- ``--mode ['run', 'ndexsave']``
    Processing mode. If set to ``run`` then hierarchy is generated. If set to ``ndexsave``,
    it is assumes hierarchy has been generated (named hierarchy.cx2 and parent_hierarchy.cx2) and put in ``outdir``
    passed in via the command line and this tool will save the hierarchy to NDEx using ``--ndexserver``, ``--ndexuser``,
    and ``--ndexpassword`` credentials

*Required in 'run' mode*

- ``--coembedding_dirs COEMBEDDINGDIRS [COEMBEDDINGDIRS ...]``
    Directories where coembedding was run. This is a required argument and multiple directories can be provided.

*Required in 'ndexsave' mode*

- ``--ndexuser NDEXUSER``
    NDEx user account.

- ``--ndexpassword NDEXPASSWORD``
    NDEx password. This can either be the password itself or a path to a file containing the password.

*Optional*

- ``--ndexserver NDEXSERVER``
    Server where the hierarchy can be converted to HCX and saved. Default is ``idekerlab.ndexbio.org``.

- ``--name NAME``
    Name of this run, needed for FAIRSCAPE. If unset, the name value from the directory specified by ``--coembedding_dir`` will be used.

- ``--organization_name ORGANIZATION_NAME``
    Name of the organization running this tool. If unset, the organization name specified in ``--coembedding_dir`` directory will be used.

- ``--project_name PROJECT_NAME``
    Name of the project running this tool. If unset, the project name specified in ``--coembedding_dir`` directory will be used.

- ``--containment_threshold``
    Containment index threshold for pruning hierarchy. Default is ``0.75``.

- ``--jaccard_threshold``
    Jaccard index threshold for merging similar clusters. Default is ``0.9``.

- ``--min_diff``
    Minimum difference in number of proteins for every parent-child pair. Default is ``1``.

- ``--min_system_size``
    Minimum number of proteins each system must have to be kept. Default is ``4``.

- ``--ppi_cutoffs PPI_CUTOFFS [PPI_CUTOFFS ...]``
    Cutoffs used to generate PPI input networks. Default cutoffs are provided in the code.

- ``--skip_layout``
    If set, skips the layout of hierarchy step.

- ``--visibility``
    If set, the Hierarchy and interactome network loaded onto NDEx will be publicly visible.

- ``--logconf LOGCONF``
    Path to python logging configuration file. Setting this overrides ``-v`` parameter which uses the default logger.

- ``--verbose`` or ``-v``
    Increases verbosity of logger. Multiple levels of verbosity can be set.

- ``--version``
    Shows the version of the program.


**Example usage**

.. code-block::

  cellmaps_generate_hierarchycmd.py ./cellmaps_generate_hierarchy_outdir --coembedding_dirs ./cellmaps_coembedding_outdir -vvvv

Via Docker
---------------

**Example usage**


.. code-block::

   Coming soon...

