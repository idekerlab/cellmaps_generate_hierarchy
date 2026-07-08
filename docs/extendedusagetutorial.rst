==========================
Extended usage tutorial
==========================

The :doc:`usage` page covers every command-line flag, but many workflows combine
those options in specific ways. This tutorial ties the arguments together by
walking through common hierarchy-generation scenarios, showing what to pass to
``cellmaps_generate_hierarchycmd.py`` and why.

Standard hierarchy generation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use this flow when you want to generate a hierarchy from one or more embedding
directories and inspect the results locally.

#. Prepare the required inputs described in :doc:`inputs`.
#. Pick or create an output directory (it does not need to exist beforehand).
#. Run:

   .. code-block:: bash

      cellmaps_generate_hierarchycmd.py ./my_output \\
          --coembedding_dirs ./fold1 ./fold2

The command builds cosine-similarity networks for each cutoff in the default
``--ppi_cutoffs`` list, runs HiDeF, and writes ``hierarchy.cx2`` plus the parent
interactome.

Single weighted edgelist workflow
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Certain  tools prefer a single weighted edgelist instead of multiple cutoff-based networks.
Enable ``--weighted_edgelist`` to collapse the run into a single TSV that
contains ``node_a node_b weight`` columns:

.. code-block:: bash

   cellmaps_generate_hierarchycmd.py ./weighted_run \\
       --coembedding_dirs ./fold1 ./fold2 \\
       --weighted_edgelist \\
       --ppi_cutoffs 0.05

When ``--weighted_edgelist`` is set, only one cutoff is used (``0.05``above). If more cutoffs are provided, the first one is used. 
If no cutoffs are provided, the tool falls back to ``--hierarchy_parent_cutoff``.

Bootstrap-driven stability checks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use ``--bootstrap_edges`` to quantify how sensitive your hierarchy is to noisy
edges. The argument accepts a percentage from 0 to 99 and randomly removes that
portion of edges from each cutoff-specific network before running HiDeF.

.. code-block:: bash

   cellmaps_generate_hierarchycmd.py ./bootstrap_run \\
       --coembedding_dirs ./embeddings \\
       --bootstrap_edges 10 \\
       --ppi_cutoffs 0.02 0.05 0.1

Repeat the run a few times and compare the resulting hierarchies to gauge robustness.

Enriching hierarchies with custom attributes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Merge additional annotations into nodes by supplying one or more RO-Crates or
TSV files via ``--gene_node_attributes``:

.. code-block:: bash

   cellmaps_generate_hierarchycmd.py ./annotated_run \\
       --coembedding_dirs ./coembeddings \\
       --gene_node_attributes ./downloads/ppi_rocrate ./downloads/img_rocrate

Uploading to NDEx
~~~~~~~~~~~~~~~~~~~~~

After validating a run, push the hierarchy and its parent interactome to NDEx by
reusing the output directory in ``ndexsave`` mode. Credentials can be provided
directly or via environment variables; if you pass ``--ndexpassword -`` the
command prompts interactively.

.. code-block:: bash

   cellmaps_generate_hierarchycmd.py ./my_output \\
       --mode ndexsave \\
       --ndexserver idekerlab.ndexbio.org \\
       --ndexuser <USER> --ndexpassword -

Run this mode only after the hierarchy exists at ``./my_output``; otherwise the
uploader cannot find ``hierarchy.cx2`` and ``hierarchy_parent.cx2``.

Converting to HiDeF files
~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``convert`` mode produces HiDeF ``.nodes`` and ``.edges`` files from a
previously generated hierarchy. This is useful when feeding the hierarchy into
tools that expect native HiDeF outputs.

.. code-block:: bash

   cellmaps_generate_hierarchycmd.py ./hidef_files \\
       --mode convert --hcx_dir ./my_output

If ``--hcx_dir`` is omitted, the converter expects ``hierarchy.cx2`` inside the
``outdir``.
