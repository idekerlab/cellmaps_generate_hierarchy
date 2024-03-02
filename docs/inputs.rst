=======
Inputs
=======

- ``embeddings dictionaries``
    One or more RO-Crates that contain coembedding (output of ``cellmaps_coembedding``),
    image embedding (output of ``cellmaps_image_embedding``) or ppi embedding (output of ``cellmaps_ppi_embedding``).
    The first column in the files contains identifiers (either gene symbols or sample IDs) while the subsequent
    columns contain embedding values. The directory should also contain metadata in ``ro-crate-metadata.json`` file.

.. code-block::

            1	2	3	4
    AURKB	-0.06713819	-0.027032608	-0.117943764	-0.14860943
    BAZ1B	0.100407355	0.1299548	-0.011916596	0.02393107
    BRD7	0.07245989	0.12707146	-0.000744308	0.023155764
    CBX3	-0.115645304	-0.1549612	-0.08860879	-0.038656197
    CHD1	0.016580202	0.11743456	-0.009839832	-0.008252605



