#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `MatureHierarchy`."""

import os
import shutil
import tempfile
import unittest
import pandas as pd
from cellmaps_generate_hierarchy.maturehierarchy import HiDeFHierarchyRefiner


class TestMatureHierarchy(unittest.TestCase):
    """Tests for `CDAPSHierarchyGenerator`."""

    def setUp(self):
        """Set up test fixtures, if any."""

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_jaccard(self):
        a = {1}
        b = {1}
        self.assertEqual(1.0, HiDeFHierarchyRefiner._jaccard(a, b))
        self.assertEqual(1.0, HiDeFHierarchyRefiner._jaccard(b, a))

        a = {1}
        b = {1, 2}
        self.assertEqual(0.5, HiDeFHierarchyRefiner._jaccard(list(a), list(b)))
        self.assertEqual(0.5, HiDeFHierarchyRefiner._jaccard(b, a))

    def test_get_node_table_from_hidef(self):
        temp_dir = tempfile.mkdtemp()
        try:
            nodes_file = os.path.join(temp_dir, 'foo.nodes')
            with open(nodes_file, 'w') as f:
                f.write('Cluster1-406\t4\t4669 649 700 809\t10\n')
                f.write('Cluster1-407\t4\t123 3146 3251 3991\t10\n')
                f.write('Cluster1-408\t4\t1528 2310 2666 4273\t10\n')
            node_table = HiDeFHierarchyRefiner._get_node_table_from_hidef(nodes_file)
            self.assertEqual(3, len(node_table))
            self.assertEqual({'Cluster1-406',
                              'Cluster1-407',
                              'Cluster1-408'}, set(node_table[HiDeFHierarchyRefiner.TERMS_COL].values))
            self.assertEqual({4}, set(node_table[HiDeFHierarchyRefiner.TSIZE_COL].values))
        finally:
            shutil.rmtree(temp_dir)

    def test_edge_table_from_hidef(self):
        temp_dir = tempfile.mkdtemp()
        try:
            edges_file = os.path.join(temp_dir, 'foo.edges')
            with open(edges_file, 'w') as f:
                f.write('Cluster1-43\tCluster2-4\tdefault\n')
                f.write('Cluster1-51\tCluster2-16\tdefault\n')
                f.write('Cluster1-66\tCluster2-8\tdefault\n')

            edge_table = HiDeFHierarchyRefiner._get_edge_table_from_hidef(edges_file)
            self.assertEqual(3, len(edge_table))
            self.assertEqual({'Cluster1-43',
                               'Cluster1-51',
                               'Cluster1-66'}, set(edge_table[HiDeFHierarchyRefiner.PARENT_COL].values))

        finally:
            shutil.rmtree(temp_dir)

    def test_get_node_table_filtered_by_term_size(self):
        node_table = pd.DataFrame.from_dict({HiDeFHierarchyRefiner.TERMS_COL: ['one', 'two'],
                                             HiDeFHierarchyRefiner.TSIZE_COL: [3, 5]})

        res = HiDeFHierarchyRefiner._get_node_table_filtered_by_term_size(node_table)
        self.assertEqual(1, len(res))
        self.assertEqual({'two'}, set(res[HiDeFHierarchyRefiner.TERMS_COL].values))

        res = HiDeFHierarchyRefiner._get_node_table_filtered_by_term_size(node_table,
                                                                          min_term_size=3)
        self.assertEqual(2, len(res))
        self.assertEqual({'one', 'two'}, set(res[HiDeFHierarchyRefiner.TERMS_COL].values))

    def test_get_edge_table_filtered_by_node_set(self):
        edge_table = pd.DataFrame.from_dict({HiDeFHierarchyRefiner.PARENT_COL: ['Cluster1-43', 'Cluster1-51'],
                                             HiDeFHierarchyRefiner.CHILD_COL: ['Cluster2-4', 'Cluster2-16']})

        res = HiDeFHierarchyRefiner._get_edge_table_filtered_by_node_set(edge_table,
                                                                         node_set={'Cluster1-43', 'Cluster2-4'})
        self.assertEqual(1, len(res))

        res = HiDeFHierarchyRefiner._get_edge_table_filtered_by_node_set(edge_table,
                                                                         node_set={'Cluster1-43'})
        self.assertEqual(0, len(res))

    def test_get_leaves_from_edge_table(self):
        edge_table = pd.DataFrame.from_dict({HiDeFHierarchyRefiner.PARENT_COL: ['Cluster1-1', 'Cluster1-2'],
                                             HiDeFHierarchyRefiner.CHILD_COL: ['Cluster1-2', 'Cluster1-3']})
        res = HiDeFHierarchyRefiner._get_leaves_from_edge_table(edge_table)
        self.assertEqual({'Cluster1-3'}, res)

    def get_genes_from_node_table_for_term(self):
        node_table = pd.DataFrame.from_dict({HiDeFHierarchyRefiner.TERMS_COL: ['one', 'two'],
                                             HiDeFHierarchyRefiner.GENES_COL: ['genea geneb genec',
                                                         'gened genee genef']})

        res = HiDeFHierarchyRefiner._get_genes_from_node_table_for_term(node_table, 'one')
        self.assertEqual(['genea', 'geneb', 'genec'], res)

    def test_get_leaf_genes_to_add(self):
        node_table = pd.DataFrame.from_dict({HiDeFHierarchyRefiner.TERMS_COL: ['one', 'two'],
                                             HiDeFHierarchyRefiner.GENES_COL: ['genea geneb genec',
                                                         'gened genee genef']})
        refiner = HiDeFHierarchyRefiner()
        res = refiner._get_leaf_genes_to_add(node_table=node_table,
                                             leaves=['two'])
        self.assertEqual(3, len(res))
        self.assertTrue(['two', 'gened', HiDeFHierarchyRefiner.GENE_TYPE] in res)
        self.assertTrue(['two', 'genee', HiDeFHierarchyRefiner.GENE_TYPE] in res)
        self.assertTrue(['two', 'genef', HiDeFHierarchyRefiner.GENE_TYPE] in res)
