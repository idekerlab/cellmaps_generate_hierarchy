#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `CytoscapeJSBreadthFirstLayout`."""

import os
import shutil
import tempfile
import unittest
from unittest.mock import MagicMock
import requests
import time
import requests_mock
import ndex2
from cellmaps_generate_hierarchy.layout import CytoscapeJSBreadthFirstLayout
from cellmaps_generate_hierarchy.exceptions import CellmapsGenerateHierarchyError

class TestMatureHierarchy(unittest.TestCase):
    """Tests for `CDAPSHierarchyGenerator`."""

    def setUp(self):
        """Set up test fixtures, if any."""

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_add_layout_500_status_code(self):
        runner = CytoscapeJSBreadthFirstLayout(rest_endpoint='http://xx',
                                               retry_sleep_time=0)
        net = ndex2.nice_cx_network.NiceCXNetwork()
        with requests_mock.Mocker() as m:
            m.post('http://xx', status_code=500)
            try:
                runner.add_layout(network=net)
                self.fail('Expected exception')
            except CellmapsGenerateHierarchyError as ce:
                self.assertTrue('Error running layout' in str(ce))

    def test_add_layout_task_failed(self):
        runner = CytoscapeJSBreadthFirstLayout(rest_endpoint='http://xx',
                                               retry_sleep_time=0)
        net = ndex2.nice_cx_network.NiceCXNetwork()
        with requests_mock.Mocker() as m:
            m.post('http://xx', status_code=202, json={'id': '12345'})
            m.get('http://xx/12345/status', status_code=200,
                  json={'progress': 100, 'status': 'error'})
            try:
                runner.add_layout(network=net)
                self.fail('Expected exception')
            except CellmapsGenerateHierarchyError as ce:
                self.assertTrue('Task failed' in str(ce))

    def test_add_layout_task_timeout(self):
        runner = CytoscapeJSBreadthFirstLayout(rest_endpoint='http://xx',
                                               retry_sleep_time=1)
        net = ndex2.nice_cx_network.NiceCXNetwork()
        with requests_mock.Mocker() as m:
            m.post('http://xx', status_code=202, json={'id': '12345'})
            m.get('http://xx/12345/status', status_code=500,
                  json={'progress': 100, 'status': 'error'})
            try:
                runner.add_layout(network=net, timeout=0)
                self.fail('Expected exception')
            except CellmapsGenerateHierarchyError as ce:
                self.assertTrue('Layout task exceeded' in str(ce))

    def test_add_layout_error_getting_final_result(self):
        runner = CytoscapeJSBreadthFirstLayout(rest_endpoint='http://xx',
                                               retry_sleep_time=0)
        net = ndex2.nice_cx_network.NiceCXNetwork()
        with requests_mock.Mocker() as m:
            m.post('http://xx', status_code=202, json={'id': '12345'})
            m.get('http://xx/12345/status', status_code=200,
                  json={'progress': 100, 'status': 'complete'})
            m.get('http://xx/12345', status_code=500, json={})
            try:
                runner.add_layout(network=net, timeout=0)
                self.fail('Expected exception')
            except CellmapsGenerateHierarchyError as ce:
                self.assertTrue('Error getting layout result' in str(ce))

    def test_add_layout_success(self):
        runner = CytoscapeJSBreadthFirstLayout(rest_endpoint='http://xx',
                                               retry_sleep_time=1)
        net = ndex2.nice_cx_network.NiceCXNetwork()
        with requests_mock.Mocker() as m:
            m.post('http://xx', status_code=202, json={'id': '12345'})
            m.get('http://xx/12345/status', status_code=200,
                  json={'progress': 100, 'status': 'complete'})
            m.get('http://xx/12345', status_code=200, json={'result': {'hi': 'there'}})
            runner.add_layout(network=net, timeout=0)
            self.assertEqual([{'hi': 'there'}], net.get_opaque_aspect('cartesianLayout'))

    def test_get_id_from_response_noid(self):
        runner = CytoscapeJSBreadthFirstLayout()
        try:
            mockres = MagicMock()
            mockres.json = MagicMock(return_val={})
            runner._get_id_from_response(mockres)
            self.fail('Expected exception')
        except CellmapsGenerateHierarchyError as ce:
            self.assertTrue('Error getting id from ' in str(ce))

    def test_is_task_complete_timeout_exceeded(self):
        runner = CytoscapeJSBreadthFirstLayout(retry_sleep_time=0)
        try:
            mockres = MagicMock()
            mockres.json = MagicMock(return_val={'progress': 50})
            start_time = int(time.time())-2
            runner._is_task_complete(mockres,
                                     start_time=start_time,
                                     timeout=1)
            self.fail('Expected exception')
        except CellmapsGenerateHierarchyError as ce:
            self.assertTrue('Layout task exceeded' in str(ce))

    def test_is_task_complete_notdone(self):
        runner = CytoscapeJSBreadthFirstLayout(retry_sleep_time=0)
        mockres = MagicMock()
        mockres.json = MagicMock(return_val={'progress': 50})
        start_time = int(time.time())
        runner._is_task_complete(mockres,
                                 start_time=start_time,
                                 timeout=500)
