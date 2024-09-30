Cell Maps Generate Hierarchy

Description: {DESCRIPTION}

Version: {VERSION}

Usage

cellmaps_generate_hierarchycmd.py [-h] [--coembedding_dirs COEMBEDDING_DIRS [COEMBEDDING_DIRS ...]] [--mode [run,ndexsave,convert]] [--hcx_dir HCX_DIR] [--provenance PROVENANCE] [--name NAME] [--organization_name ORGANIZATION_NAME]
                                     [--project_name PROJECT_NAME] [--k K] [--algorithm ALGORITHM] [--maxres MAXRES] [--stability STABILITY] [--containment_threshold CONTAINMENT_THRESHOLD] [--jaccard_threshold JACCARD_THRESHOLD] [--min_diff MIN_DIFF]
                                     [--min_system_size MIN_SYSTEM_SIZE] [--ppi_cutoffs PPI_CUTOFFS [PPI_CUTOFFS ...]] [--hierarchy_parent_cutoff HIERARCHY_PARENT_CUTOFF] [--bootstrap_edges BOOTSTRAP_EDGES] [--skip_layout] [--ndexserver NDEXSERVER]
                                     [--ndexuser NDEXUSER] [--ndexpassword NDEXPASSWORD] [--visibility] [--keep_intermediate_files] [--gene_node_attributes GENE_NODE_ATTRIBUTES [GENE_NODE_ATTRIBUTES ...]] [--skip_logging] [--logconf LOGCONF] [--verbose]
                                     [--version]
                                     outdir

Outputs

The `cellmaps_generate_hierarchycmd.py` script produces a collection of output files in the specified output directory.
Each of these files serves a specific purpose in the hierarchy generation and interaction mapping processes.

CX2 Interactome and Hierarchy Outputs
----------------------------------------
These files represent the final interactome and hierarchy in CX2 format:

- hierarchy.cx2:
    The main output file containing the generated hierarchy in HCX format.

- hierarchy_parent.cx2:
    The parent or primary network used as a reference for generating the hierarchy in CX2_ format.

For examples of the two CX2 file look at: https://cellmaps-generate-hierarchy.readthedocs.io/en/latest/outputs.html

Interaction Network Outputs
---------------------------
Intermediate processing step files that represent protein-protein interaction networks at different cutoff thresholds:

- ppi_cutoff_*.cx:
    Protein-Protein Interaction networks in CX_ format. Can be omitted.

- ppi_cutoff_*.id.edgelist.tsv:
    Edgelist representation of the Protein-Protein Interaction networks.

    0	1
    2	3
    4	5
    6	1
    7	8

Other Outputs
-------------
- cdaps.json:
    A JSON file containing information about the CDAPS_ analysis. It contains the community detection results and node attributes as CX2_.
    More information about the community detection format v2 can be found `here <https://github.com/cytoscape/communitydetection-rest-server/wiki/COMMUNITYDETECTRESULTV2-format>`__

- hidef_output.edges:
    Contains the edges or interactions in the HiDeF_ generated hierarchy.

    Cluster0-0	Cluster1-0	default
    Cluster0-0	Cluster1-1	default
    Cluster0-0	Cluster1-2	default
    Cluster0-0	Cluster1-3	default
    Cluster1-0	Cluster2-0	default

- hidef_output.nodes:
    Contains the nodes or entities in the HiDeF_ generated hierarchy.

    Cluster0-0	23	0 1 10 11 12 13 14 15 16 17 18 19 2 20 21 22 3 4 5 6 7 8 9	0
    Cluster1-0	7	0 1 10 20 4 5 6	119
    Cluster1-1	5	12 13 17 18 19	171
    Cluster2-0	5	0 1 10 20 6	41
    Cluster1-2	4	2 21 3 9	177
    Cluster1-3	4	11 14 7 8	172

- hidef_output.pruned.edges:
    Contains pruned edges after certain filtering (maturing) processes on the original hierarchy.

    Cluster0-0	Cluster1-0	default
    Cluster0-0	Cluster1-1	default
    Cluster0-0	Cluster1-2	default
    Cluster0-0	Cluster1-3	default
    Cluster1-0	Cluster2-0	default

- hidef_output.pruned.nodes:
    Contains pruned nodes after certain filtering (maturing) processes on the original hierarchy.

    Cluster0-0	23	3 17 21 4 20 1 10 12 9 14 8 2 15 19 5 11 7 16 18 0 13 22 6	0
    Cluster1-0	7	20 1 5 4 10 0 6	119
    Cluster2-0	5	20 1 10 0 6	41
    Cluster1-1	5	18 19 17 12 13	171
    Cluster1-3	4	14 11 8 7	172
    Cluster1-2	4	21 3 2 9	177

- hidef_output.weaver:
    Information related to the weaving process used in generating the hierarchy.

Logs and Metadata
-----------------
- error.log:
    Contains error messages and exceptions that might have occurred during execution.

- output.log:
    Provides detailed logs about the steps performed and their outcomes.

- ro-crate-metadata.json:
    Metadata in RO-Crate format, a community effort to establish a lightweight approach to packaging research data with their metadata.

    It contains general information about the data i.a. ID, Type, Name, Description, contextual definitions,
    Software detail, as well as datasets details of each individual part of the data.

