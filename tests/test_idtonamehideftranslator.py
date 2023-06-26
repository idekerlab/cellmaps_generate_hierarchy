#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `IDToNameHiDeFTranslator`."""

import os
import string
import io
import csv
from datetime import date
import shutil
import tempfile
import unittest
from unittest.mock import MagicMock
import json
import ndex2
from io import StringIO

from cellmaps_utils import constants
import cellmaps_generate_hierarchy
from cellmaps_generate_hierarchy.hierarchy import IDToNameHiDeFTranslator
from cellmaps_generate_hierarchy.exceptions import CellmapsGenerateHierarchyError
from cellmaps_generate_hierarchy.hierarchy import CXHierarchyGenerator


class TestIDToNameHiDeFTranslator(unittest.TestCase):
    """Tests for `CDAPSHierarchyGenerator`."""

    def setUp(self):
        """Set up test fixtures, if any."""

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_translate_hidef_output(self):
        temp_dir = tempfile.mkdtemp()
        try:
            net = ndex2.nice_cx_network.NiceCXNetwork()
            clust_one_nodes = []
            c_index = 0
            for x in range(4):

                clust_one_nodes.append(str(net.create_node(string.ascii_lowercase[c_index])))
                c_index+=1

            clust_two_nodes = []
            for x in range(3):
                clust_two_nodes.append(str(net.create_node(string.ascii_lowercase[c_index])))
                c_index += 1

            nodes_file = os.path.join(temp_dir, 'hidef.nodes')
            with open(nodes_file, 'w', newline='') as f:
                writer = csv.writer(f, delimiter='\t')
                row = ['cluster1-0', str(len(clust_one_nodes))]
                row.append(' '.join(clust_one_nodes))
                row.append('76')
                writer.writerow(row)

                row = ['cluster1-1', str(len(clust_two_nodes))]
                row.append(' '.join(clust_two_nodes))
                row.append('55')
                writer.writerow(row)

            edges_file = os.path.join(temp_dir, 'hidef.edges')
            with open(edges_file, 'w', newline='') as f:
                writer = csv.writer(f, delimiter='\t')
                writer.writerow(['cluster1-0', 'cluster1-1', 'default'])

            mockprov = MagicMock()
            mockprov.register_dataset = MagicMock()
            mockprov.register_dataset.side_effect = ['1', '2']

            translator = IDToNameHiDeFTranslator(network=net,
                                                 provenance_utils=mockprov)
            res = translator.translate_hidef_output(hidef_nodes=nodes_file,
                                                    hidef_edges=edges_file,
                                                    dest_prefix=os.path.join(temp_dir, 'result'))
            self.assertEqual(['1', '2'], res)

            with open(os.path.join(temp_dir, 'result.nodes'), 'r') as f:
                reader = csv.reader(f, delimiter='\t')

                res = [a for a in reader]
                self.assertEqual(2, len(res))
                self.assertEqual(['cluster1-0', '4', 'a b c d', '76'], res[0])
                self.assertEqual(['cluster1-1', '3', 'e f g', '55'], res[1])
        finally:
            shutil.rmtree(temp_dir)


