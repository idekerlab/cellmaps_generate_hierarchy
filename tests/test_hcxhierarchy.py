#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `HcxHierarchy`."""
import unittest
from unittest.mock import patch, MagicMock
import ndex2
import os

from cellmaps_generate_hierarchy.exceptions import CellmapsGenerateHierarchyError
from cellmaps_generate_hierarchy.hcx import HCXFromCDAPSCXHierarchy


class TestHcxHierarchy(unittest.TestCase):
    """Tests for `HcxHierarchy`."""

    def setUp(self):
        """Set up test fixtures, if any."""

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def get_simple_hierarchy(self):
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

    def test_get_root_nodes(self):
        net = self.get_simple_hierarchy()
        myobj = HCXFromCDAPSCXHierarchy(ndexserver='server', ndexuser='user', ndexpassword='password')
        self.assertEqual({0}, myobj._get_root_nodes(net))

    def test_add_isroot_node_attribute(self):
        net = self.get_simple_hierarchy()
        myobj = HCXFromCDAPSCXHierarchy(ndexserver='server', ndexuser='user', ndexpassword='password')
        myobj._add_isroot_node_attribute(net, root_nodes={0})
        self.assertEqual('true', net.get_node_attribute(0, 'HCX::isRoot')['v'])
        for x in [1, 2, 3]:
            self.assertEqual('false', net.get_node_attribute(x, 'HCX::isRoot')['v'])

    def test_get_mapping_of_node_names_to_ids(self):
        net = self.get_simple_hierarchy()
        myobj = HCXFromCDAPSCXHierarchy(ndexserver='server', ndexuser='user', ndexpassword='password')
        res = myobj._get_mapping_of_node_names_to_ids(net)
        self.assertEqual({'child1': 1, 'child2': 2,
                          'root': 0, 'subchild1': 3}, res)

    def test_add_hierarchy_network_attributes(self):
        net = self.get_simple_hierarchy()
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
        net = self.get_simple_hierarchy()
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
        # {'child1': 1, 'child2': 2}
        net = self.get_simple_hierarchy()
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
        net = self.get_simple_hierarchy()
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

    def test_wait_for_network_summary_completion(self):
        mock_ndex_client = MagicMock()
        mock_ndex_client.get_network_summary.return_value = {"completed": True}
        myobj = HCXFromCDAPSCXHierarchy(ndexserver='server', ndexuser='user', ndexpassword='password')
        myobj._set_ndex_client(mock_ndex_client)
        myobj._wait_for_network_summary_completion("dummy_uuid")
        mock_ndex_client.get_network_summary.assert_called_with("dummy_uuid")

    def test_wait_for_network_summary_completion_timeout_exceeded(self):
        mock_ndex_client = MagicMock()
        mock_ndex_client.get_network_summary.return_value = {"completed": False}
        myobj = HCXFromCDAPSCXHierarchy(ndexserver='server', ndexuser='user', ndexpassword='password')
        myobj._set_ndex_client(mock_ndex_client)

        try:
            myobj._wait_for_network_summary_completion("dummy_uuid", timeout=1, timeout_sleep=0.5)
            self.fail('Expected exception')
        except CellmapsGenerateHierarchyError as he:
            self.assertTrue("Waiting for network summary exceeded" in str(he))

    def test_wait_for_network_summary_completion_error_message_in_summary(self):
        mock_ndex_client = MagicMock()
        mock_ndex_client.get_network_summary.return_value = {"errorMessage": "Some error"}
        myobj = HCXFromCDAPSCXHierarchy(ndexserver='server', ndexuser='user', ndexpassword='password')
        myobj._set_ndex_client(mock_ndex_client)

        try:
            myobj._wait_for_network_summary_completion("dummy_uuid")
            self.fail('Expected exception')
        except CellmapsGenerateHierarchyError as he:
            self.assertTrue("Error in network summary" in str(he))

    def test_save_network(self):
        net = self.get_simple_hierarchy()
        mock_ndex_client = MagicMock()
        mock_ndex_client.save_new_network = MagicMock(return_value='uuid12345')
        myobj = HCXFromCDAPSCXHierarchy(ndexserver='server', ndexuser='user', ndexpassword='password')
        myobj._set_ndex_client(mock_ndex_client)

        with patch.object(myobj, "_wait_for_network_summary_completion"):
            result = myobj._save_network(net)
            self.assertEqual(result, "uuid12345")

    def test_save_network_uuid_is_none(self):
        net = self.get_simple_hierarchy()
        mock_ndex_client = MagicMock()
        mock_ndex_client.save_new_network = MagicMock(return_value=None)
        myobj = HCXFromCDAPSCXHierarchy(ndexserver='server', ndexuser='user', ndexpassword='password')
        myobj._set_ndex_client(mock_ndex_client)

        with patch.object(myobj, "_wait_for_network_summary_completion"):
            try:
                result = myobj._save_network(net)
            except CellmapsGenerateHierarchyError as he:
                self.assertTrue('Expected a str, but got this: ' in str(he))

    def test_save_network_ndexclient_exception(self):
        net = self.get_simple_hierarchy()
        mock_ndex_client = MagicMock()
        mock_ndex_client.save_new_network.side_effect = Exception('NDEx throws exception')
        myobj = HCXFromCDAPSCXHierarchy(ndexserver='server', ndexuser='user', ndexpassword='password')
        myobj._set_ndex_client(mock_ndex_client)

        with patch.object(myobj, "_wait_for_network_summary_completion"):
            try:
                result = myobj._save_network(net)
            except CellmapsGenerateHierarchyError as he:
                self.assertTrue('An error occurred while saving the network to NDEx: ' in str(he))








