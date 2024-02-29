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

.. code-block:: json

    [
      {
        "CXVersion": "1.0",
        "hasFragments": false
      },
      {
        "metaData": [
          {
            "elementCount": 1,
            "name": "attributeDeclarations"
          },
          {
            "elementCount": 1,
            "name": "networkAttributes"
          },
          {
            "elementCount": 3,
            "name": "nodes"
          },
          {
            "elementCount": 2,
            "name": "edges"
          }
        ]
      },
      {
        "attributeDeclarations": [removed for readability of the example]
      },
      {
        "networkAttributes": [
          {
            "name": "Sample Network",
            "description": "This is a sample network for demonstration."
            "ndexSchema": "hierarchy_v0.1",
            "HCX::modelFileCount": 2,
            "HCX::interactionNetworkName": "hierarchy_parent.cx2"
          }
        ]
      },
      {
        "nodes": [
          {
            "id": 0,
            "v": {
              "name": "Node1",
              "represents": "Data1"
              "HCX::isRoot": true,
              "HCX::members": [
                0,
                1,
                2]
            }
          },
          {
            "id": 1,
            "v": {
              "name": "Node2",
              "represents": "Data2"
              "HCX::isRoot": false,
              "HCX::members": [
                1]
            }
          },
          {
            "id": 2,
            "v": {
              "name": "Node3",
              "represents": "Data3"
              "HCX::isRoot": true,
              "HCX::members": [
                2]
            }
          }
        ]
      },
      {
        "edges": [
          {
            "id": 0,
            "s": 0,
            "t": 1
          },
          {
            "id": 1,
            "s": 0,
            "t": 2
          }
        ]
      },
      {
        "status": [
          {
            "error": "",
            "success": true
          }
        ]
      }
    ]


- ``hierarchy_parent.cx2``:
    The parent or primary network used as a reference for generating the hierarchy in CX2_ format.

.. code-block:: json

    [
        {
            "CXVersion": "2.0",
            "hasFragments": false
        },
        {
            "metaData": [
                {"elementCount": 1, "name": "attributeDeclarations"},
                {"elementCount": 1, "name": "networkAttributes"},
                {"elementCount": 3, "name": "nodes"},
                {"elementCount": 2, "name": "edges"}
            ]
        },
        {
            "attributeDeclarations": [
                {
                    "networkAttributes": {"name": {"d": "string"}, "description": {"d": "string"}},
                    "nodes": {"name": {"a": "n", "d": "string"}, "represents": {"a": "r", "d": "string"}},
                    "edges": {"interaction": {"a": "i", "d": "string"}, "Weight": {"d": "double"}}
                }
            ]
        },
        {
            "networkAttributes": [
                {"name": "Example PPI Network", "description": "Simplified Protein-Protein Interaction network example"}
            ]
        },
        {
            "nodes": [
                {"id": 0, "v": {"n": "ProteinA", "r": "ProteinA"}},
                {"id": 1, "v": {"n": "ProteinB", "r": "ProteinB"}},
                {"id": 2, "v": {"n": "ProteinC", "r": "ProteinC"}}
            ]
        },
        {
            "edges": [
                {"id": 0, "s": 0, "t": 1, "v": {"Weight": 0.5, "i": "interacts-with"}},
                {"id": 1, "s": 0, "t": 2, "v": {"Weight": 0.6, "i": "interacts-with"}},
            ]
        }
    ]


Interaction Network Outputs
---------------------------
Intermediate processing step files that represent protein-protein interaction networks at different cutoff thresholds:

- ``ppi_cutoff_*.cx``:
    Protein-Protein Interaction networks in CX_ format. Can be omitted.

- ``ppi_cutoff_*.id.edgelist.tsv``:
    Edgelist representation of the Protein-Protein Interaction networks.

.. code-block::

    0	1
    2	3
    4	5
    6	1
    7	8

Other Outputs
-------------
- ``cdaps.json``:
    A JSON file containing information about the CDAPS_ analysis. It contains the community detection results and node attributes as CX2_.
    More information about the community detection format v2 can be found `here <https://github.com/cytoscape/communitydetection-rest-server/wiki/COMMUNITYDETECTRESULTV2-format>`__

.. code-block:: json

    {
      "communityDetectionResult": "23,4,c-m;23,1,c-m;23,6,c-m;23,10,c-m;23,22,c-m;23,19,c-m;23,17,c-m;23,20,c-m;23,13,c-m;23,14,c-m;23,11,c-m;23,7,c-m;23,5,c-m;23,18,c-m;23,21,c-m;23,8,c-m;23,12,c-m;23,15,c-m;23,3,c-m;23,0,c-m;23,9,c-m;23,16,c-m;23,2,c-m;24,4,c-m;24,1,c-m;24,6,c-m;24,10,c-m;24,0,c-m;24,20,c-m;24,5,c-m;25,1,c-m;25,6,c-m;25,10,c-m;25,0,c-m;25,20,c-m;26,18,c-m;26,19,c-m;26,17,c-m;26,12,c-m;26,13,c-m;27,8,c-m;27,14,c-m;27,7,c-m;27,11,c-m;28,21,c-m;28,9,c-m;28,2,c-m;28,3,c-m;23,24,c-c;23,26,c-c;23,28,c-c;23,27,c-c;24,25,c-c;",
      "nodeAttributesAsCX2": {
        "attributeDeclarations": [
          {
            "nodes": {
              "HiDeF_persistence": {
                "d": "integer",
                "a": "p1",
                "v": 0
              }
            }
          }
        ],
        "nodes": [
          {
            "id": 23,
            "v": {
              "p1": 0
            }
          },
          {
            "id": 24,
            "v": {
              "p1": 119
            }
          },
          {
            "id": 25,
            "v": {
              "p1": 41
            }
          },
          {
            "id": 26,
            "v": {
              "p1": 171
            }
          },
          {
            "id": 27,
            "v": {
              "p1": 172
            }
          },
          {
            "id": 28,
            "v": {
              "p1": 177
            }
          }
        ]
      }
    }

- ``hidef_output.edges``:
    Contains the edges or interactions in the HiDeF_ generated hierarchy.

.. code-block::

    Cluster0-0	Cluster1-0	default
    Cluster0-0	Cluster1-1	default
    Cluster0-0	Cluster1-2	default
    Cluster0-0	Cluster1-3	default
    Cluster1-0	Cluster2-0	default

- ``hidef_output.nodes``:
    Contains the nodes or entities in the HiDeF_ generated hierarchy.

.. code-block::

    Cluster0-0	23	0 1 10 11 12 13 14 15 16 17 18 19 2 20 21 22 3 4 5 6 7 8 9	0
    Cluster1-0	7	0 1 10 20 4 5 6	119
    Cluster1-1	5	12 13 17 18 19	171
    Cluster2-0	5	0 1 10 20 6	41
    Cluster1-2	4	2 21 3 9	177
    Cluster1-3	4	11 14 7 8	172

- ``hidef_output.pruned.edges``:
    Contains pruned edges after certain filtering (maturing) processes on the original hierarchy.

.. code-block::

    Cluster0-0	Cluster1-0	default
    Cluster0-0	Cluster1-1	default
    Cluster0-0	Cluster1-2	default
    Cluster0-0	Cluster1-3	default
    Cluster1-0	Cluster2-0	default

- ``hidef_output.pruned.nodes``:
    Contains pruned nodes after certain filtering (maturing) processes on the original hierarchy.

.. code-block::

    Cluster0-0	23	3 17 21 4 20 1 10 12 9 14 8 2 15 19 5 11 7 16 18 0 13 22 6	0
    Cluster1-0	7	20 1 5 4 10 0 6	119
    Cluster2-0	5	20 1 10 0 6	41
    Cluster1-1	5	18 19 17 12 13	171
    Cluster1-3	4	14 11 8 7	172
    Cluster1-2	4	21 3 2 9	177

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
