#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `CDAPSHierarchyGenerator`."""

import os

import shutil
import tempfile
import unittest
import ndex2
from cellmaps_utils import constants
from cellmaps_generate_hierarchy.hierarchy import CDAPSHierarchyGenerator


class TestCDAPSHierarchyGenerator(unittest.TestCase):
    """Tests for `CDAPSHierarchyGenerator`."""

    def setUp(self):
        """Set up test fixtures, if any."""

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_get_hierarchy(self):
        gen = CDAPSHierarchyGenerator()

        net = ndex2.nice_cx_network.NiceCXNetwork()
        net.set_name('Test')
        node_a = net.create_node('A')
        node_b = net.create_node('B')
        node_c = net.create_node('C')
        node_d = net.create_node('D')

        net.create_edge(edge_source=node_a, edge_target=node_b)
        net.create_edge(edge_source=node_a, edge_target=node_c)
        net.create_edge(edge_source=node_b, edge_target=node_c)
        net.create_edge(edge_source=node_b, edge_target=node_d)

        hierarchy = gen.get_hierarchy(net)

        self.assertEqual(1, len(hierarchy.get_nodes()))


