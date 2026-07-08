#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for the --weighted_edgelist / weighted_mode feature."""

import os
import json
import shutil
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import ndex2
from cellmaps_utils import constants

from cellmaps_generate_hierarchy import cellmaps_generate_hierarchycmd
from cellmaps_generate_hierarchy.hcx import HCXFromCDAPSCXHierarchy
from cellmaps_generate_hierarchy.hierarchy import CDAPSHiDeFHierarchyGenerator

WEIGHT_COL = constants.WEIGHTED_PPI_EDGELIST_WEIGHT_COL


class TestWeightedEdgelist(unittest.TestCase):
    """Tests for weighted edge list generation."""

    def setUp(self):
        self._temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self._temp_dir, ignore_errors=True)

    # ------------------------------------------------------------------ #
    # helpers
    # ------------------------------------------------------------------ #
    def _write_network(self, name, edges):
        """Builds a NiceCXNetwork with the given edges and writes it to a
        CX file, returning its prefix path (no suffix).

        :param edges: iterable of (src_name, tgt_name, weight_or_None)
        """
        net = ndex2.nice_cx_network.NiceCXNetwork()
        net.set_name(name)
        node_ids = {}
        for src, tgt, weight in edges:
            for gene in (src, tgt):
                if gene not in node_ids:
                    node_ids[gene] = net.create_node(gene)
            edge_id = net.create_edge(edge_source=node_ids[src],
                                      edge_target=node_ids[tgt])
            if weight is not None:
                net.set_edge_attribute(edge_id, WEIGHT_COL, weight)
        prefix = os.path.join(self._temp_dir, name)
        with open(prefix + constants.CX_SUFFIX, 'w') as f:
            json.dump(net.to_cx(), f)
        return prefix

    def _make_generator(self, **kwargs):
        mockprov = MagicMock()
        mockprov.register_dataset = MagicMock(
            side_effect=['id0', 'id1', 'id2', 'id3'])
        mockprov.get_default_date_format_str = MagicMock(
            return_value='%Y-%m-%d')
        return CDAPSHiDeFHierarchyGenerator(
            provenance_utils=mockprov,
            author='author',
            version='version',
            hcxconverter=HCXFromCDAPSCXHierarchy(),
            **kwargs)

    def _read_edgelist(self, prefix):
        with open(prefix + CDAPSHiDeFHierarchyGenerator.EDGELIST_TSV) as f:
            return f.read()

    # ------------------------------------------------------------------ #
    # constructor / flag storage
    # ------------------------------------------------------------------ #
    def test_weighted_mode_defaults_to_false(self):
        gen = self._make_generator()
        self.assertFalse(gen._weighted_mode)

    def test_weighted_mode_can_be_enabled(self):
        gen = self._make_generator(weighted_mode=True)
        self.assertTrue(gen._weighted_mode)

    # ------------------------------------------------------------------ #
    # edgelist output
    # ------------------------------------------------------------------ #
    def test_weighted_mode_writes_third_weight_column(self):
        """weighted_mode=True with weights present -> 3-column output."""
        prefix = self._write_network('wnet',
                                     [('n1', 'n2', 0.9), ('n2', 'n5', 0.5)])
        gen = self._make_generator(weighted_mode=True)
        gen._create_edgelist_files_for_networks([prefix])
        self.assertEqual('0\t1\t0.9\n1\t2\t0.5\n', self._read_edgelist(prefix))

    def test_default_mode_ignores_weights(self):
        """weighted_mode=False (default) -> 2 columns even when the edges
        carry Weight attributes. Guards against the feature leaking into the
        normal cutoff-based path."""
        prefix = self._write_network('wnet',
                                     [('n1', 'n2', 0.9), ('n2', 'n5', 0.5)])
        gen = self._make_generator()
        gen._create_edgelist_files_for_networks([prefix])
        self.assertEqual('0\t1\n1\t2\n', self._read_edgelist(prefix))

    def test_removed_edges_file_includes_weight_column(self):
        """The bootstrap-removed edges file must also carry the weight column
        in weighted mode. random.sample is patched so exactly the first edge
        is flagged for removal, deterministically."""
        prefix = self._write_network('wnet',
                                     [('n1', 'n2', 0.9), ('n2', 'n5', 0.5)])
        gen = self._make_generator(weighted_mode=True)
        gen._bootstrap_edges = 50  # threshold int(2 * 0.5) == 1 -> one removed

        # force the (0, 1) edge to be the one sampled for removal
        with patch('cellmaps_generate_hierarchy.hierarchy.random.sample',
                   return_value=[(0, 1)]):
            gen._create_edgelist_files_for_networks([prefix])

        removed_path = prefix + '_removed_edges.tsv'
        self.assertTrue(os.path.isfile(removed_path))
        with open(removed_path) as f:
            removed = f.read()
        # the removed edge line should have 3 tab-separated fields
        self.assertEqual(1, len(removed.strip().splitlines()))
        self.assertEqual(3, len(removed.strip().split('\t')))
        self.assertIn('0.9', removed)

    def test_weighted_mode_missing_weight_falls_back_to_two_columns(self):
        """weighted_mode=True but an edge has no Weight attribute.

        The writer already guards each line with ``edge_data[2] is not None``,
        so the documented intent is a graceful fall back to a 2-column line for
        that edge. This test pins that intent.

        NOTE: this currently FAILS on the dev branch. ``get_edge_attribute``
        returns the tuple ``(None, None)`` (not ``None``) for a missing
        attribute, which is truthy, so ``if weight_attr:`` passes and
        ``weight_attr.get('v')`` raises AttributeError. Fix in hierarchy.py,
        e.g. ``if isinstance(weight_attr, dict):`` before calling .get('v').
        """
        prefix = self._write_network('wnet',
                                     [('n1', 'n2', 0.9), ('n2', 'n5', None)])
        gen = self._make_generator(weighted_mode=True)
        gen._create_edgelist_files_for_networks([prefix])
        self.assertEqual('0\t1\t0.9\n1\t2\n', self._read_edgelist(prefix))


class TestWeightedEdgelistCmd(unittest.TestCase):
    """Tests for the --weighted_edgelist argument and its wiring in main()."""

    def test_weighted_edgelist_flag_defaults_false(self):
        res = cellmaps_generate_hierarchycmd._parse_arguments(
            'desc', ['outdir', '--coembedding_dirs', 'foo'])
        self.assertFalse(res.weighted_edgelist)

    def test_weighted_edgelist_flag_sets_true(self):
        res = cellmaps_generate_hierarchycmd._parse_arguments(
            'desc', ['outdir', '--coembedding_dirs', 'foo',
                     '--weighted_edgelist'])
        self.assertTrue(res.weighted_edgelist)

    @patch('cellmaps_generate_hierarchy.cellmaps_generate_hierarchycmd.'
           'CellmapsGenerateHierarchy')
    @patch('cellmaps_generate_hierarchy.cellmaps_generate_hierarchycmd.'
           'CDAPSHiDeFHierarchyGenerator')
    @patch('cellmaps_generate_hierarchy.cellmaps_generate_hierarchycmd.'
           'CosineSimilarityPPIGenerator')
    def test_main_collapses_cutoffs_and_passes_weighted_mode(
            self, mock_ppigen, mock_hiergen, mock_runner):
        """With --weighted_edgelist, main() must collapse ppi_cutoffs to a
        single (first) cutoff and pass weighted_mode=True to the hierarchy
        generator."""
        mock_hiergen.HIERARCHY_PARENT_CUTOFF = 0.1
        mock_runner.return_value.run.return_value = 0
        temp_dir = tempfile.mkdtemp()
        try:
            rc = cellmaps_generate_hierarchycmd.main(
                ['prog', temp_dir,
                 '--coembedding_dirs', 'foo',
                 '--ppi_cutoffs', '0.001', '0.05', '0.1',
                 '--weighted_edgelist'])
            self.assertEqual(0, rc)

            # cutoffs collapsed to just the first one
            _, ppi_kwargs = mock_ppigen.call_args
            self.assertEqual([0.001], ppi_kwargs['cutoffs'])

            # weighted_mode threaded through to the generator
            _, hier_kwargs = mock_hiergen.call_args
            self.assertTrue(hier_kwargs['weighted_mode'])
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    @patch('cellmaps_generate_hierarchy.cellmaps_generate_hierarchycmd.'
           'CellmapsGenerateHierarchy')
    @patch('cellmaps_generate_hierarchy.cellmaps_generate_hierarchycmd.'
           'CDAPSHiDeFHierarchyGenerator')
    @patch('cellmaps_generate_hierarchy.cellmaps_generate_hierarchycmd.'
           'CosineSimilarityPPIGenerator')
    def test_main_without_flag_keeps_all_cutoffs(
            self, mock_ppigen, mock_hiergen, mock_runner):
        """Without the flag, all cutoffs are preserved and weighted_mode is
        False."""
        mock_runner.return_value.run.return_value = 0
        temp_dir = tempfile.mkdtemp()
        try:
            cellmaps_generate_hierarchycmd.main(
                ['prog', temp_dir,
                 '--coembedding_dirs', 'foo',
                 '--ppi_cutoffs', '0.001', '0.05', '0.1'])
            _, ppi_kwargs = mock_ppigen.call_args
            self.assertEqual([0.001, 0.05, 0.1], ppi_kwargs['cutoffs'])
            _, hier_kwargs = mock_hiergen.call_args
            self.assertFalse(hier_kwargs['weighted_mode'])
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == '__main__':
    unittest.main()
