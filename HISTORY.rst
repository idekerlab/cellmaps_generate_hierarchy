=======
History
=======

0.2.6 (TBD)
-----------

* Added ``--weighted_edgelist`` flag to enable generation of a single weighted edge list with cosine similarity 
  values as a third column, instead of multiple cutoff-based edge lists. When this flag is set, only the first 
  cutoff value from ``--ppi_cutoffs`` is used (defaults to parent cutoff if not specified), and the resulting edge list 
  includes edge weights that can be utilized by HiDeF for hierarchy generation.

0.2.5 (2025-10-08)
-------------------

* Remove leading spaces from name of hierarchy.

0.2.4 (2025-05-15)
-------------------

* Updated to PEP 517 compliant build system

0.2.3 (2025-03-19)
------------------

* Update requirements versions

* Increase timeout for cmd run

* Fix 'k' argument type

0.2.2 (2024-11-25)
------------------

* Added default argument for password.

0.2.1 (2024-11-08)
------------------

* Fixed types of arguments.


0.2.0 (2024-10-16)
------------------

* Added the ``--bootstrap_edges`` flag, which allows specifying the percentage of edges to be randomly removed
  from each PPI network (across networks at different PPI cutoffs).

* Added a style for proteins specified as bait.

* Refactored code and expose more methods for hierarchy generation from edgelists.


0.1.0 (2024-09-06)
------------------

* First release on PyPI.
