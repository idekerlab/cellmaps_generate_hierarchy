#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `HcxHierarchy`."""
import unittest
from unittest.mock import patch, MagicMock
import ndex2
from ndex2.cx2 import CX2Network
import os

from cellmaps_generate_hierarchy.exceptions import CellmapsGenerateHierarchyError
from cellmaps_generate_hierarchy.hcx import HCXFromCDAPSCXHierarchy


class TestHcxHierarchy(unittest.TestCase):
    """Tests for `HcxHierarchy`."""

    def setUp(self):
        """Set up test fixtures, if any."""

    def tearDown(self):
        """Tear down test fixtures, if any."""

    @staticmethod
    def _get_simple_nicecx_hierarchy():
        net = ndex2.nice_cx_network.NiceCXNetwork()
        root = net.create_node('root')
        child1 = net.create_node('child1')

        net.create_edge(edge_source=root,
                        edge_target=child1)

        child2 = net.create_node('child2')
        net.create_edge(edge_source=root,
                        edge_target=child2)

        subchild1 = net.create_node('subchild1')
        net.create_edge(edge_source=child1,
                        edge_target=subchild1)
        return net

    @staticmethod
    def _get_simple_cx2_hierarchy():
        net = ndex2.cx2.CX2Network()
        root = net.add_node(1, {'n': 'root'})
        child1 = net.add_node(2, {'n': 'child1'})

        net.add_edge(source=root, target=child1)

        child2 = net.add_node(3, {'n': 'child2'})
        net.add_edge(source=root, target=child2)

        subchild1 = net.add_node(4, {'n': 'subchild1'})
        net.add_edge(source=child1, target=subchild1)
        return net

    def test_get_root_nodes(self):
        net = self._get_simple_nicecx_hierarchy()
        myobj = HCXFromCDAPSCXHierarchy(ndexserver='server', ndexuser='user', ndexpassword='password')
        self.assertEqual({0}, myobj._get_root_nodes(net))

    def test_add_isroot_node_attribute(self):
        net = self._get_simple_nicecx_hierarchy()
        myobj = HCXFromCDAPSCXHierarchy(ndexserver='server', ndexuser='user', ndexpassword='password')
        myobj._add_isroot_node_attribute(net, root_nodes={0})
        self.assertEqual('true', net.get_node_attribute(0, 'HCX::isRoot')['v'])
        for x in [1, 2, 3]:
            self.assertEqual('false', net.get_node_attribute(x, 'HCX::isRoot')['v'])

    def test_get_mapping_of_node_names_to_ids(self):
        net = self._get_simple_nicecx_hierarchy()
        myobj = HCXFromCDAPSCXHierarchy(ndexserver='server', ndexuser='user', ndexpassword='password')
        res = myobj._get_mapping_of_node_names_to_ids(net)
        self.assertEqual({'child1': 1, 'child2': 2,
                          'root': 0, 'subchild1': 3}, res)

    def test_add_hierarchy_network_attributes(self):
        net = self._get_simple_nicecx_hierarchy()
        myobj = HCXFromCDAPSCXHierarchy(ndexserver='server', ndexuser='user', ndexpassword='password')
        myobj._add_hierarchy_network_attributes(net, interactome_id='12345')
        self.assertEqual('hierarchy_v0.1',
                         net.get_network_attribute('ndexSchema')['v'])
        self.assertEqual('2',
                         net.get_network_attribute('HCX::modelFileCount')['v'])
        self.assertEqual('12345',
                         net.get_network_attribute('HCX::interactionNetworkUUID')['v'])
        self.assertEqual('server',
                         net.get_network_attribute('HCX::interactionNetworkHost')['v'])

    def test_add_hierarchy_network_attributes_server_is_none(self):
        net = self._get_simple_nicecx_hierarchy()
        myobj = HCXFromCDAPSCXHierarchy(ndexserver=None, ndexuser='user', ndexpassword='password')
        myobj._add_hierarchy_network_attributes(net, interactome_id='12345')
        self.assertEqual('hierarchy_v0.1',
                         net.get_network_attribute('ndexSchema')['v'])
        self.assertEqual('2',
                         net.get_network_attribute('HCX::modelFileCount')['v'])
        self.assertEqual('12345',
                         net.get_network_attribute('HCX::interactionNetworkUUID')['v'])
        self.assertEqual('www.ndexbio.org',
                         net.get_network_attribute('HCX::interactionNetworkHost')['v'])

    def test_add_members_node_attribute(self):
        net = self._get_simple_nicecx_hierarchy()
        name_map = {'A': 100, 'B': 200}
        net.set_node_attribute(0, 'CD_MemberList', values='A B C')

        myobj = HCXFromCDAPSCXHierarchy(ndexserver='server', ndexuser='user', ndexpassword='password')
        myobj._add_members_node_attribute(net, interactome_name_map=name_map)

        mem_list = net.get_node_attribute(0, 'HCX::members')['v']
        self.assertEqual(2, len(mem_list))
        self.assertTrue('100' in mem_list)
        self.assertTrue('200' in mem_list)

        self.assertEqual(None, net.get_node_attribute(1, 'HCX::members'))

    def test_add_members_node_attribute_map_is_none(self):
        net = self._get_simple_nicecx_hierarchy()
        myobj = HCXFromCDAPSCXHierarchy(ndexserver='server', ndexuser='user', ndexpassword='password')
        try:
            myobj._add_members_node_attribute(net, interactome_name_map=None)
            self.fail('Expected exception')
        except CellmapsGenerateHierarchyError as he:
            self.assertEqual('interactome name map is None', str(he))

    def test_password_in_file(self):
        path = os.path.join(os.path.dirname(__file__), 'data', 'test_password')
        myobj = HCXFromCDAPSCXHierarchy(ndexserver='server', ndexuser='user', ndexpassword=path)
        self.assertEqual(myobj._password, 'password')

    def test_visibility(self):
        myobj = HCXFromCDAPSCXHierarchy(ndexserver='server', ndexuser='user', ndexpassword='password', visibility=True)
        self.assertEqual(myobj._visibility, 'PUBLIC')

    def test_get_visual_editor_properties_aspect_from_network(self):
        myobj = HCXFromCDAPSCXHierarchy(ndexserver='server')

        # try with empty network
        empty_net = CX2Network()
        res = myobj._get_visual_editor_properties_aspect_from_network(network=empty_net)
        self.assertIsNone(res)

        # try with network containing the aspect
        fake_net = CX2Network()
        visual_edit_aspect = {HCXFromCDAPSCXHierarchy.VISUAL_EDITOR_PROPERTIES_ASPECT: 1}
        fake_net.set_opaque_aspects([visual_edit_aspect])
        res = myobj._get_visual_editor_properties_aspect_from_network(network=fake_net)
        self.assertEqual(res, visual_edit_aspect)

    def test_save_network(self):
        net = self._get_simple_cx2_hierarchy()
        mock_ndex_client = MagicMock()
        mock_ndex_client.save_new_cx2_network.return_value = 'http://some-url.com/uuid12345'
        myobj = HCXFromCDAPSCXHierarchy(ndexserver='server', ndexuser='user', ndexpassword='password')
        myobj._set_ndex_client(mock_ndex_client)
        result = myobj._save_network(net)
        self.assertEqual(result, "uuid12345")

    def test_save_network_uuid_is_none(self):
        net = self._get_simple_cx2_hierarchy()
        mock_ndex_client = MagicMock()
        mock_ndex_client.save_new_cx2_network.return_value = None
        myobj = HCXFromCDAPSCXHierarchy(ndexserver='server', ndexuser='user', ndexpassword='password')
        myobj._set_ndex_client(mock_ndex_client)

        try:
            result = myobj._save_network(net)
        except CellmapsGenerateHierarchyError as he:
            self.assertTrue('Expected a str, but got this: ' in str(he))

    def test_save_network_ndexclient_exception(self):
        net = self._get_simple_cx2_hierarchy()
        mock_ndex_client = MagicMock()
        mock_ndex_client.save_new_cx2_network.side_effect = Exception('NDEx throws exception')
        myobj = HCXFromCDAPSCXHierarchy(ndexserver='server', ndexuser='user', ndexpassword='password')
        myobj._set_ndex_client(mock_ndex_client)

        try:
            result = myobj._save_network(net)
        except CellmapsGenerateHierarchyError as he:
            self.assertTrue('An error occurred while saving the network to NDEx: ' in str(he))
