=======
Outputs
=======

The `cellmaps_generate_hierarchycmd.py` script produces a collection of output files in the specified output directory.
Each of these files serves a specific purpose in the hierarchy generation and interaction mapping processes.

CX2_ Interactome and Hierarchy Outputs
----------------------------------------
These files represent the final interactome and hierarchy in CX2_ format:

- ``hierarchy.cx2``:
    The main output file containing the generated hierarchy in HCX_ format.

- ``hierarchy_parent.cx2``:
    The parent or primary network used as a reference for generating the hierarchy in CX2_ format.

Interaction Network Outputs
---------------------------
Intermediate processing step files that represent protein-protein interaction networks at different cutoff thresholds:

- ``ppi_cutoff_*.cx``:
    Protein-Protein Interaction networks in CX_ format.

- ``ppi_cutoff_*.id.edgelist.tsv``:
    Edgelist representation of the Protein-Protein Interaction networks.

Other Outputs
-------------
- ``cdaps.json``:
    A JSON file containing information about the CDAPS_ analysis. It contains the community detection results and node attributes as CX2_.
    More information about the community detection format v2 can be found `here <https://github.com/cytoscape/communitydetection-rest-server/wiki/COMMUNITYDETECTRESULTV2-format>`__

- ``hidef_output.edges``:
    Contains the edges or interactions in the HiDeF_ generated hierarchy.

- ``hidef_output.nodes``:
    Contains the nodes or entities in the HiDeF_ generated hierarchy.

- ``hidef_output.pruned.edges``:
    Contains pruned edges after certain filtering (maturing) processes on the original hierarchy.

- ``hidef_output.pruned.nodes``:
    Contains pruned nodes after certain filtering (maturing) processes on the original hierarchy.

- ``hidef_output.weaver``:
    Information related to the weaving process used in generating the hierarchy.

Logs and Metadata
-----------------
- ``error.log``:
    Contains error messages and exceptions that might have occurred during execution.

- ``output.log``:
    Provides detailed logs about the steps performed and their outcomes.

- ``ro-crate-metadata.json``:
    Metadata in RO-Crate_ format, a community effort to establish a lightweight approach to packaging research data with their metadata.

    It contains general information about the data i.a. ID, Type, Name, Description, contextual definitions,
    Software detail, as well as datasets details of each individual part of the data.

    For example, the metadata for the content of hierarchy.cx provides unique id, context, type, url, name, keywords, etc.
    The url can be used to view the hierarchy in Cytoscape_ Web.

    .. code-block:: json

        {
          "@id": "00000000-0000-0000-0000-000000000000:dataset::4.hierarchy",
          "@context": {
            "@vocab": "https://schema.org/",
            "evi": "https://w3id.org/EVI#"
          },
          "metadataType": "https://w3id.org/EVI#Dataset",
          "url": "https://idekerlab.ndexbio.org/cytoscape/network/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
          "name": "Output Dataset",
          "keywords": [
            "CM4AI",
            "Example",
            "interactome",
            "ppi",
            "network",
            "CX2",
            "file",
            "hierarchy",
            "network",
            "HCX"
          ],
          "description": "CM4AI Example Example input dataset AP-MS edgelist download|IF microscopy merged embedding AP-MS edgelist download|IF microscopy Example input dataset hierarchy model Hierarchy network file",
          "author": "cellmaps_generate_hierarchy",
          "datePublished": "2023-09-21",
          "version": "0.1.0a11",
          "associatedPublication": null,
          "additionalDocumentation": null,
          "format": "HCX",
          "schema": {},
          "generatedBy": [],
          "derivedFrom": [],
          "usedBy": [],
          "contentUrl": "path/hierarchy.hcx"
        }

    Additionally, it contains Computation Details, name, description, Run By etc.

.. _CX: https://cytoscape.org/cx/specification/cytoscape-exchange-format-specification-(version-1)
.. _CX2: https://cytoscape.org/cx/cx2/specification/cytoscape-exchange-format-specification-(version-2)
.. _HCX: https://cytoscape.org/cx/cx2/hcx-specification
.. _CDAPS: https://cdaps.readthedocs.io
.. _HiDeF: https://hidef.readthedocs.io
.. _RO-Crate: https://www.researchobject.org/ro-crate
.. _Cytoscape: https://cytoscape.org/
