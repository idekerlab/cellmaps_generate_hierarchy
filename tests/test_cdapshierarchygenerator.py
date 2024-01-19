#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `CDAPSHierarchyGenerator`."""

import os
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
from cellmaps_generate_hierarchy.hcx import HCXFromCDAPSCXHierarchy
from cellmaps_generate_hierarchy.hierarchy import CDAPSHiDeFHierarchyGenerator
from cellmaps_generate_hierarchy.exceptions import CellmapsGenerateHierarchyError
from cellmaps_generate_hierarchy.hierarchy import HierarchyGenerator


class TestCDAPSHierarchyGenerator(unittest.TestCase):
    """Tests for `CDAPSHierarchyGenerator`."""

    def setUp(self):
        """Set up test fixtures, if any."""

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_cx_hierarchy_generator(self):
        gen = HierarchyGenerator()
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

            converter = HCXFromCDAPSCXHierarchy()
            gen = CDAPSHiDeFHierarchyGenerator(hcxconverter=converter)
            self.assertEqual(77, gen._get_max_node_id(nodes_file))

        finally:
            shutil.rmtree(temp_dir)

    def test_write_members_for_row(self):
        converter = HCXFromCDAPSCXHierarchy()
        gen = CDAPSHiDeFHierarchyGenerator(hcxconverter=converter)
        data = ''
        out_stream = StringIO(data)
        gen.write_members_for_row(out_stream,
                                  ['', '', '0 1 19 48'], 5)
        self.assertEqual('5,0,c-m;5,1,c-m;5,19,c-m;5,48,c-m;',
                         out_stream.getvalue())

    def test_update_cluster_node_map(self):
        converter = HCXFromCDAPSCXHierarchy()
        gen = CDAPSHiDeFHierarchyGenerator(hcxconverter=converter)
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
        converter = HCXFromCDAPSCXHierarchy()
        gen = CDAPSHiDeFHierarchyGenerator(hcxconverter=converter)
        persistence_map = {}
        gen.update_persistence_map(persistence_map, 1, 'val')
        self.assertEqual({1: 'val'}, persistence_map)

        gen.update_persistence_map(persistence_map, 1, 'val')
        self.assertEqual({1: 'val'}, persistence_map)

        gen.update_persistence_map(persistence_map, 2, '2val')
        self.assertEqual({1: 'val',
                          2: '2val'}, persistence_map)

    def test_convert_hidef_output_to_cdaps(self):
        temp_dir = tempfile.mkdtemp()
        try:
            shutil.copy(os.path.join(os.path.dirname(__file__), 'data', 'hidef_output.nodes'),
                        os.path.join(temp_dir, 'hidef_output.pruned.nodes'))
            shutil.copy(os.path.join(os.path.dirname(__file__), 'data', 'hidef_output.edges'),
                        os.path.join(temp_dir, 'hidef_output.pruned.edges'))
            data = ''
            out_stream = StringIO(data)
            converter = HCXFromCDAPSCXHierarchy()
            gen = CDAPSHiDeFHierarchyGenerator(hcxconverter=converter)
            self.assertIsNone(gen.convert_hidef_output_to_cdaps(out_stream,
                                                                temp_dir))

            res = json.loads(out_stream.getvalue())
            self.assertEqual('77,22,c-m;77,23,c-m;77,72,c-m;77,74,c-m;77,'
                             '75,c-m;77,76,c-m;78,72,c-m;78,74,c-m;78,75,'
                             'c-m;78,76,c-m;77,78,c-c;', res['communityDetectionResult'])
            self.assertEqual([{'nodes': {'HiDeF_persistence': {'d': 'integer',
                                                               'a': 'p1',
                                                               'v': 0}}}],
                             res['nodeAttributesAsCX2']['attributeDeclarations'])
            self.assertEqual([{'id': 77, 'v': {'p1': 36}},
                              {'id': 78, 'v': {'p1': 33}}],
                             res['nodeAttributesAsCX2']['nodes'])
        finally:
            shutil.rmtree(temp_dir)

    def test_create_edgelist_files_for_networks(self):
        temp_dir = tempfile.mkdtemp()
        try:
            cx_networks = []
            one_edge_net = ndex2.nice_cx_network.NiceCXNetwork()
            one_edge_net.set_name('one')
            n_one = one_edge_net.create_node('n1')
            n_two = one_edge_net.create_node('n2')
            one_edge_net.set_network_attribute(name='cutoff', values=0.7)
            one_edge_net.create_edge(edge_source=n_one, edge_target=n_two)
            one_edge_net_file = os.path.join(temp_dir, 'one_edge')
            cx_networks.append(one_edge_net_file)
            with open(one_edge_net_file + constants.CX_SUFFIX, 'w') as f:
                json.dump(one_edge_net.to_cx(), f)

            two_edge_net = ndex2.nice_cx_network.NiceCXNetwork()
            two_edge_net.set_name('two')
            n_one = two_edge_net.create_node('n1')
            n_two = two_edge_net.create_node('n2')
            n_three = two_edge_net.create_node('n5')
            two_edge_net.create_edge(edge_source=n_one, edge_target=n_two)
            two_edge_net.create_edge(edge_source=n_two, edge_target=n_three)
            two_edge_net_file = os.path.join(temp_dir, 'two_edge')
            cx_networks.append(two_edge_net_file)
            with open(two_edge_net_file + constants.CX_SUFFIX, 'w') as f:
                json.dump(two_edge_net.to_cx(), f)

            mockprov = MagicMock()
            mockprov.register_dataset = MagicMock()
            mockprov.register_dataset.side_effect = ['XXX', 'YYY']
            mockprov.get_default_date_format_str = MagicMock(return_value='%Y-%m-%d')
            converter = HCXFromCDAPSCXHierarchy()
            gen = CDAPSHiDeFHierarchyGenerator(provenance_utils=mockprov,
                                               author='author',
                                               version='version',
                                               hcxconverter=converter)
            (parent_net_path, parent_network, largest_net, net_paths) = gen._create_edgelist_files_for_networks(cx_networks)
            self.assertEqual(one_edge_net_file + '.cx', parent_net_path)
            self.assertEqual('one', parent_network.get_name())
            self.assertEqual(2, len(net_paths))
            self.assertTrue(one_edge_net_file +
                            CDAPSHiDeFHierarchyGenerator.EDGELIST_TSV in net_paths)
            self.assertTrue(two_edge_net_file +
                            CDAPSHiDeFHierarchyGenerator.EDGELIST_TSV in net_paths)

            with open(one_edge_net_file +
                      CDAPSHiDeFHierarchyGenerator.EDGELIST_TSV, 'r') as f:
                self.assertEqual('0\t1\n', f.read())

            with open(two_edge_net_file +
                      CDAPSHiDeFHierarchyGenerator.EDGELIST_TSV, 'r') as f:
                self.assertEqual('0\t1\n1\t2\n', f.read())
            self.assertEqual(2, len(gen.get_generated_dataset_ids()))
            self.assertTrue('XXX' in gen.get_generated_dataset_ids())
            self.assertTrue('YYY' in gen.get_generated_dataset_ids())

            data_dict = {'name': os.path.basename(one_edge_net_file) +
                                 CDAPSHiDeFHierarchyGenerator.EDGELIST_TSV +
                                 ' PPI id edgelist file',
                         'description': 'PPI id edgelist file',
                         'data-format': 'tsv',
                         'author': 'author',
                         'version': 'version',
                         'date-published': date.today().strftime('%Y-%m-%d')}
            mockprov.register_dataset.assert_any_call(temp_dir,
                                                      source_file=one_edge_net_file +
                                                                  CDAPSHiDeFHierarchyGenerator.EDGELIST_TSV,
                                                      data_dict=data_dict)

            data_dict = {'name': os.path.basename(two_edge_net_file) +
                                 CDAPSHiDeFHierarchyGenerator.EDGELIST_TSV +
                         ' PPI id edgelist file',
                         'description': 'PPI id edgelist file',
                         'data-format': 'tsv',
                         'author': 'author',
                         'version': 'version',
                         'date-published': date.today().strftime('%Y-%m-%d')}
            mockprov.register_dataset.assert_any_call(temp_dir,
                                                      source_file=two_edge_net_file +
                                                      CDAPSHiDeFHierarchyGenerator.EDGELIST_TSV,
                                                      data_dict=data_dict)
            self.assertEqual(2, mockprov.register_dataset.call_count)
        finally:
            shutil.rmtree(temp_dir)

    def test_register_hidef_output_files(self):
        temp_dir = tempfile.mkdtemp()
        try:
            mockprov = MagicMock()
            mockprov.register_dataset = MagicMock()
            mockprov.register_dataset.side_effect = ['X', 'Y', 'Z']
            mockprov.get_default_date_format_str = MagicMock(return_value='%Y-%m-%d')
            converter = HCXFromCDAPSCXHierarchy()
            gen = CDAPSHiDeFHierarchyGenerator(provenance_utils=mockprov, hcxconverter=converter)
            gen._register_hidef_output_files(temp_dir)
            self.assertEqual(['X', 'Y', 'Z'], gen.get_generated_dataset_ids())

            data_dict = {'name': CDAPSHiDeFHierarchyGenerator.HIDEF_OUT_PREFIX +
                         '.nodes HiDeF output nodes file',
                         'description': ' HiDeF output nodes file',
                         'data-format': 'tsv',
                         'author': 'cellmaps_generate_hierarchy',
                         'version': cellmaps_generate_hierarchy.__version__,
                         'date-published': date.today().strftime('%Y-%m-%d')}
            mockprov.register_dataset.assert_any_call(temp_dir,
                                                      source_file=os.path.join(temp_dir,
                                                                               CDAPSHiDeFHierarchyGenerator.HIDEF_OUT_PREFIX +
                                                                               '.nodes'),
                                                      data_dict=data_dict)
            self.assertEqual(3, mockprov.register_dataset.call_count)
        finally:
            shutil.rmtree(temp_dir)

    def test_get_hierarchy_hidef_fails(self):
        temp_dir = tempfile.mkdtemp()
        try:
            cx_networks = []
            one_edge_net = ndex2.nice_cx_network.NiceCXNetwork()
            one_edge_net.set_name('one')
            n_one = one_edge_net.create_node('n1')
            n_two = one_edge_net.create_node('n2')
            one_edge_net.set_network_attribute(name='cutoff', values=0.7)
            one_edge_net.create_edge(edge_source=n_one, edge_target=n_two)
            one_edge_net_file = os.path.join(temp_dir, 'one_edge')
            cx_networks.append(one_edge_net_file)
            with open(one_edge_net_file + constants.CX_SUFFIX, 'w') as f:
                json.dump(one_edge_net.to_cx(), f)

            two_edge_net = ndex2.nice_cx_network.NiceCXNetwork()
            two_edge_net.set_name('two')
            n_one = two_edge_net.create_node('n1')
            n_two = two_edge_net.create_node('n2')
            n_three = two_edge_net.create_node('n5')
            two_edge_net.create_edge(edge_source=n_one, edge_target=n_two)
            two_edge_net.create_edge(edge_source=n_two, edge_target=n_three)
            two_edge_net_file = os.path.join(temp_dir, 'two_edge')
            cx_networks.append(two_edge_net_file)
            with open(two_edge_net_file + constants.CX_SUFFIX, 'w') as f:
                json.dump(two_edge_net.to_cx(), f)

            mockprov = MagicMock()
            mockprov.register_dataset = MagicMock(return_val='xxx')
            mockprov.get_default_date_format_str = MagicMock(return_value='%Y-%m-%d')
            mockconverter = MagicMock()
            mockconverter.get_converted_hierarchy(return_value=[None, None, None, None])
            gen = CDAPSHiDeFHierarchyGenerator(provenance_utils=mockprov,
                                                   author='author',
                                                   version='version',
                                                   hcxconverter=mockconverter)
            gen.get_hierarchy(cx_networks)
            self.fail('Expected exception')
        except CellmapsGenerateHierarchyError as e:
            self.assertTrue('Cmd failed with exit code: 1' in str(e))

        finally:
            shutil.rmtree(temp_dir)






