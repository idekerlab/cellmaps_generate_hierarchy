#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `CDAPSHierarchyGenerator`."""

import os
import io
import shutil
import tempfile
import unittest
import ndex2
from io import StringIO

from cellmaps_utils import constants
from cellmaps_generate_hierarchy.hierarchy import CDAPSHiDeFHierarchyGenerator
from cellmaps_generate_hierarchy.hierarchy import CXHierarchyGenerator


class TestCDAPSHierarchyGenerator(unittest.TestCase):
    """Tests for `CDAPSHierarchyGenerator`."""

    def setUp(self):
        """Set up test fixtures, if any."""

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_cx_hierarchy_generator(self):
        gen = CXHierarchyGenerator()
        self.assertEqual([], gen.get_generated_dataset_ids())
        try:
            gen.get_hierarchy([])
            self.fail('Expected Exception')
        except NotImplementedError as ne:
            self.assertTrue('Subclasses' in str(ne))

    def test_get_max_node_id(self):
        temp_dir = tempfile.mkdtemp()
        try:
            nodes_file = os.path.join(temp_dir, 'nodes.nodes')
            with open(nodes_file, 'w') as f:
                f.write('Cluster3-2\t5\t51 52 57 61 77\t11\n')
                f.write('Cluster2-9\t4\t0 1 19 48\t55\n')
                f.write('Cluster1-0\t4\t17 26 27 64\t11\n')

            gen = CDAPSHiDeFHierarchyGenerator()
            self.assertEqual(77, gen._get_max_node_id(nodes_file))

        finally:
            shutil.rmtree(temp_dir)

    def test_write_members_for_row(self):
        gen = CDAPSHiDeFHierarchyGenerator()
        data = ''
        out_stream = StringIO(data)
        gen.write_members_for_row(out_stream,
                                  ['', '', '0 1 19 48'], 5)
        self.assertEqual('5,0,c-m;5,1,c-m;5,19,c-m;5,48,c-m;',
                         out_stream.getvalue())

    def test_update_cluster_node_map(self):
        gen = CDAPSHiDeFHierarchyGenerator()
        cluster_node_map = {}
        max_node, cur_node = gen.update_cluster_node_map(cluster_node_map,
                                                         'Cluster-0-0', 4)
        self.assertEqual(5, max_node)
        self.assertEqual(5, cur_node)
        self.assertEqual({'Cluster-0-0': 5}, cluster_node_map)

        max_node, cur_node = gen.update_cluster_node_map(cluster_node_map,
                                                         'Cluster-0-0', 4)
        self.assertEqual(4, max_node)
        self.assertEqual(5, cur_node)
        self.assertEqual({'Cluster-0-0': 5}, cluster_node_map)

    def test_update_persistence_map(self):
        gen = CDAPSHiDeFHierarchyGenerator()
        persistence_map = {}
        gen.update_persistence_map(persistence_map, 1, 'val')
        self.assertEqual({1: 'val'}, persistence_map)

        gen.update_persistence_map(persistence_map, 1, 'val')
        self.assertEqual({1: 'val'}, persistence_map)

        gen.update_persistence_map(persistence_map, 2, '2val')
        self.assertEqual({1: 'val',
                          2: '2val'}, persistence_map)







