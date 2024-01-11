#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `cellmaps_generate_hierarchy` package."""

import os
import shutil
import tempfile
import unittest
from unittest.mock import MagicMock

from cellmaps_utils.exceptions import CellMapsProvenanceError
from ndex2.cx2 import CX2Network

from cellmaps_generate_hierarchy.exceptions import CellmapsGenerateHierarchyError
from cellmaps_generate_hierarchy.ndexupload import NDExHierarchyUploader
from cellmaps_generate_hierarchy.runner import CellmapsGenerateHierarchy


class TestCellmapsgeneratehierarchyrunner(unittest.TestCase):
    """Tests for `cellmaps_generate_hierarchy` package."""

    def setUp(self):
        """Set up test fixtures, if any."""

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_constructor(self):
        """Tests constructor"""
        temp_dir = tempfile.mkdtemp()
        try:
            myobj = CellmapsGenerateHierarchy(outdir=os.path.join(temp_dir, 'out'))
            self.assertIsNotNone(myobj)
        finally:
            shutil.rmtree(temp_dir)

    def test_constructor_outdir_must_be_set(self):
        """Tests constructor outdir must be set"""
        try:
            CellmapsGenerateHierarchy()
            self.fail('Expected exception')
        except CellmapsGenerateHierarchyError as e:
            self.assertEqual('outdir is None', str(e))

    def test_run_without_logging(self):
        """ Tests run() without logging."""
        temp_dir = tempfile.mkdtemp()
        try:
            run_dir = os.path.join(temp_dir, 'run')
            myobj = CellmapsGenerateHierarchy(outdir=run_dir)
            try:
                myobj.run()
                self.fail('Expected CellMapsProvenanceError')
            except CellMapsProvenanceError as e:
                print(e)
                self.assertTrue('rocrates' in str(e))

            self.assertFalse(os.path.isfile(os.path.join(run_dir, 'output.log')))
            self.assertFalse(os.path.isfile(os.path.join(run_dir, 'error.log')))

        finally:
            shutil.rmtree(temp_dir)

    def test_run_with_logging(self):
        """ Tests run() with logging."""
        temp_dir = tempfile.mkdtemp()
        try:
            run_dir = os.path.join(temp_dir, 'run')
            myobj = CellmapsGenerateHierarchy(outdir=run_dir,
                                              skip_logging=False)
            try:
                myobj.run()
                self.fail('Expected CellMapsProvenanceError')
            except CellMapsProvenanceError as e:
                self.assertTrue('rocrates' in str(e))

            self.assertTrue(os.path.isfile(os.path.join(run_dir, 'output.log')))
            self.assertTrue(os.path.isfile(os.path.join(run_dir, 'error.log')))

        finally:
            shutil.rmtree(temp_dir)

    def test_password_in_file(self):
        path = os.path.join(os.path.dirname(__file__), 'data', 'test_password')
        myobj = NDExHierarchyUploader(ndexserver='server', ndexuser='user', ndexpassword=path)
        self.assertEqual(myobj._password, 'password')

    def test_visibility(self):
        myobj = NDExHierarchyUploader(ndexserver='server', ndexuser='user', ndexpassword='password', visibility=True)
        self.assertEqual(myobj._visibility, 'PUBLIC')

    def test_save_network(self):
        net = MagicMock()
        mock_ndex_client = MagicMock()
        mock_ndex_client.save_new_cx2_network.return_value = 'http://some-url.com/uuid12345'
        myobj = NDExHierarchyUploader(ndexserver='server', ndexuser='user', ndexpassword='password')
        myobj._ndexclient = mock_ndex_client
        result = myobj._save_network(net)
        self.assertEqual(result, ("uuid12345", 'https://server/cytoscape/0/networks/uuid12345'))

    def test_save_network_uuid_is_none(self):
        net = MagicMock()
        mock_ndex_client = MagicMock()
        mock_ndex_client.save_new_cx2_network.return_value = None
        myobj = NDExHierarchyUploader(ndexserver='server', ndexuser='user', ndexpassword='password')
        myobj._ndexclient = mock_ndex_client

        try:
            result = myobj._save_network(net)
        except CellmapsGenerateHierarchyError as he:
            self.assertTrue('Expected a str, but got this: ' in str(he))

    def test_save_network_ndexclient_exception(self):
        net = MagicMock()
        mock_ndex_client = MagicMock()
        mock_ndex_client.save_new_cx2_network.side_effect = Exception('NDEx throws exception')
        myobj = NDExHierarchyUploader(ndexserver='server', ndexuser='user', ndexpassword='password')
        myobj._ndexclient = mock_ndex_client

        try:
            result = myobj._save_network(net)
        except CellmapsGenerateHierarchyError as he:
            self.assertTrue('An error occurred while saving the network to NDEx: ' in str(he))

    def test_update_hcx_annotations(self):
        mock_hierarchy = CX2Network()
        mock_hierarchy._network_attributes = {'HCX::interactionNetworkName': 'mock_name'}
        interactome_id = "test-uuid"
        myobj = NDExHierarchyUploader(ndexserver='server', ndexuser='user', ndexpassword='password')
        updated_hierarchy = myobj._update_hcx_annotations(mock_hierarchy, interactome_id)

        self.assertEqual(updated_hierarchy.get_network_attributes()['HCX::interactionNetworkUUID'], interactome_id)
        self.assertEqual(updated_hierarchy.get_network_attributes()['HCX::interactionNetworkHost'], 'server')
        self.assertFalse('HCX::interactionNetworkName' in updated_hierarchy.get_network_attributes())

        myobj._server = None
        updated_hierarchy = myobj._update_hcx_annotations(mock_hierarchy, interactome_id)
        self.assertEqual(updated_hierarchy.get_network_attributes()['HCX::interactionNetworkHost'], 'www.ndexbio.org')

