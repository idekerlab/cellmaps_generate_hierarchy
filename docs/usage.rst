=====
Usage
=====

The tool is designed to generate interaction network's hierarchy based on a list of embedding or coembedding files. Embedding or coembedding directories,
containing coembedding files in TSV format should be provided to generate several interactomes, which are used to create a structured hierarchy.

It can be also used to uppload hierarchy and its parent to NDEx and convert hierarchy in HCCX to HiDeF .nodes and .edges files.

In a project
--------------

To use cellmaps_generate_hierarchy in a project::

    import cellmaps_generate_hierarchy


Needed files
------------

The output directory for co-embedding (see `Cell Maps Coembedding <https://github.com/idekerlab/cellmaps_coembedding/>`__),
ppi embedding (see `Cell Maps PPI Embedding <https://github.com/idekerlab/cellmaps_ppi_embedding/>`__),
or image embedding (see `Cell Maps Image Embedding <https://github.com/idekerlab/cellmaps_image_embedding/>`__) is required


On the command line
---------------------

For information invoke :code:`cellmaps_generate_hierarchycmd.py -h`

**Usage**

.. code-block::

  cellmaps_generate_hierarchycmd.py [outdir] [--coembedding_dirs COEMBEDDINGDIRS [COEMBEDDINGDIRS ...]] [OPTIONS]

.. code-block::

  cellmaps_generate_hierarchycmd.py [outdir] [--mode ndexsave] [--ndexuser NDEXUSER] [--ndexpassword NDEXPASSWORD]


.. code-block::

  cellmaps_generate_hierarchycmd.py [outdir] [--mode convert] [--hcx_dir DIRECTORY_WITH_HCX_FILE]

**Arguments**

- ``outdir``
    The directory where the output will be written to or directory where hierarchy.cx2 and parent_hierarchy.cx2 was
    saved.

*Possible modes*

- ``--mode ['run', 'ndexsave', 'convert']``
    Processing mode. If set to ``run`` then hierarchy is generated. If set to ``ndexsave``,
    it is assumes hierarchy has been generated (named hierarchy.cx2 and parent_hierarchy.cx2) and put in ``outdir``
    passed in via the command line and this tool will save the hierarchy to NDEx using ``--ndexserver``, ``--ndexuser``,
    and ``--ndexpassword`` credentials

*Required in 'run' mode*

- ``--coembedding_dirs COEMBEDDINGDIRS [COEMBEDDINGDIRS ...]``
    Directories where coembedding, ppi embedding or image embedding was run. This is a required argument and multiple directories can be provided.
    Can be also paths to specific TSV files with embeddings.

*Required in 'ndexsave' mode*

- ``--ndexuser NDEXUSER``
    NDEx user account.

- ``--ndexpassword NDEXPASSWORD``
    NDEx password. This can either be the password itself or a path to a file containing the password.

*Required in 'convert' mode*

- ``--hcx_dir DIRECTORY_WITH_HCX_FILE``
    Input directory for convert mode with hierarchy in hcx to be converted to HiDeF .nodes and .edges files

*Optional*

- ``--ndexserver NDEXSERVER``
    Server where the hierarchy can be converted to HCX and saved. Default is ``idekerlab.ndexbio.org``.

- ``--name NAME``
    Name of this run, needed for FAIRSCAPE. If unset, the name value from the directory specified by ``--coembedding_dir`` will be used.

- ``--organization_name ORGANIZATION_NAME``
    Name of the organization running this tool. If unset, the organization name specified in ``--coembedding_dir`` directory will be used.

- ``--project_name PROJECT_NAME``
    Name of the project running this tool. If unset, the project name specified in ``--coembedding_dir`` directory will be used.

- ``--k K``
    HiDeF stability parameter. Default is 10.

- ``--algorithm ALGORITHM``
    HiDeF clustering algorithm parameter. Default algorithm is leiden.

- ``--maxres MAXRES``
    HiDeF max resolution parameter. Default value is 80.

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


Example usage
---------------------

Hierarchy generation
~~~~~~~~~~~~~~~~~~~~~

To generate hierarchy, use embeddings or co-embeddings, in the format specified in Inputs_ section.

.. code-block::

  cellmaps_generate_hierarchycmd.py ./cellmaps_generate_hierarchy_outdir --coembedding_dirs ./cellmaps_coembedding_outdir -vvvv

To generate hierarchy with a **custom name** use ``--name`` flag.

.. code-block::

  cellmaps_generate_hierarchycmd.py ./cellmaps_generate_hierarchy_outdir --coembedding_dirs ./cellmaps_coembedding_outdir --name my_hierarchy -vvvv

Uploading hierarchy to NDEx
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To upload network to NDEx, NDEx account is necessary. See `here  <https://home.ndexbio.org/create-an-ndex-account/>`__ on how to create account on NDEx.

With command line:

.. code-block:: bash

    # Example hierarchy and its interactome in examples directory in cellmaps_generate_hierarchy repository

    cellmaps_generate_hierarchycmd.py ./examples/ --mode ndexsave --ndexuser example_user_name --ndexpassword -

Programmatically:

.. code-block:: python

    import os
    import ndex2
    from ndex2.cx2 import RawCX2NetworkFactory
    from cellmaps_generate_hierarchy.ndexupload import NDExHierarchyUploader

    #Specify NDEx server
    ndexserver = 'idekerlab.ndexbio.org'

    # Specify paths to hierarchy and its parent (you can find example files in examples directory in cellmaps_generate_hierarchy_repo)
    hierarchy_path = './examples/hierarchy.cx2'
    parent_network_path = './examples/hierarchy_parent.cx2'

    # Load the hierarchy and parent network CX2 files into network objects
    factory = RawCX2NetworkFactory()
    hierarchy_network = factory.get_cx2network(hierarchy_path)
    parent_network = factory.get_cx2network(parent_network_path)

    # Initialize NDExHierarchyUploader with the specified NDEx server and credentials
    uploader = NDExHierarchyUploader(ndexserver, ndexuser, ndexpassword)

    # Upload the hierarchy and parent network to NDEx
    parent_uuid, parenturl, hierarchy_uuid, hierarchyurl = uploader.save_hierarchy_and_parent_network(hierarchy_network, parent_network)

    print(f"Parent network UUID is {parent_uuid} and its URL in NDEx is {parenturl})
    print(f"Hierarchy network UUID is {hierarchy_uuid} and its URL in NDEx is {hierarchyurl})

    # Another option is to just specify the directory where the files are placed
    _, _, _, hierarchyurl = ndex_uploader.upload_hierary_and_parent_network_from_files('./examples/')
    print(f'Hierarchy uploaded. To view the hierarchy, paste this URL in your browser: {hierarchyurl}')

Convert hierarchy to HiDeF
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::

    cellmaps_generate_hierarchycmd.py ./output_dir --mode convert --hcx_dir ./examples/


Via Docker
---------------

**Example usage**


.. code-block::

   Coming soon...


.. _Inputs: file:///Users/jlenkiewicz/Documents/repos/cellmaps_generate_hierarchy/docs/_build/html/inputs.html#inputs
