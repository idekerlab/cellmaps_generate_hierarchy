#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `CosineSimilarityPPIGenerator`."""

import os

import shutil
import tempfile
import unittest
from cellmaps_utils import constants
from cellmaps_generate_hierarchy.runner import CellmapsGenerateHierarchy
from cellmaps_generate_hierarchy.ppi import CosineSimilarityPPIGenerator


class TestCosineSimilarityPPIGenerator(unittest.TestCase):
    """Tests for `CosineSimilarityPPIGenerator`."""

    def setUp(self):
        """Set up test fixtures, if any."""

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def get_fake_five_line_coembedding_file(self):
        return os.path.join(os.path.dirname(__file__), 'data',
                            'fake_4_node_coembedding.tsv')

    def test_fake_five_line_coembedding(self):
        temp_dir = tempfile.mkdtemp()
        try:
            shutil.copy(self.get_fake_five_line_coembedding_file(),
                        os.path.join(temp_dir, constants.CO_EMBEDDING_FILE))
            gen = CosineSimilarityPPIGenerator(embeddingdirs=[temp_dir],
                                               cutoffs=[1.0])

            itr = gen.get_next_network()
            net = next(itr, None)
            self.assertEqual('parent interactome with 1.0 cutoff', net.get_name())
            self.assertEqual(6, len(net.get_edges()))
            self.assertEqual(4, len(net.get_nodes()))
            self.assertIsNone(next(itr, None))
        finally:
            shutil.rmtree(temp_dir)
