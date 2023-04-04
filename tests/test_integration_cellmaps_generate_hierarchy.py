#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Integration Tests for `cellmaps_generate_hierarchy` package."""

import os

import unittest
from cellmaps_generate_hierarchy import cellmaps_generate_hierarchycmd

SKIP_REASON = 'CELLMAPS_GENERATE_HIERARCHY_INTEGRATION_TEST ' \
              'environment variable not set, cannot run integration ' \
              'tests'

@unittest.skipUnless(os.getenv('CELLMAPS_GENERATE_HIERARCHY_INTEGRATION_TEST') is not None, SKIP_REASON)
class TestIntegrationCellmaps_generate_hierarchy(unittest.TestCase):
    """Tests for `cellmaps_generate_hierarchy` package."""

    def setUp(self):
        """Set up test fixtures, if any."""

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_something(self):
        """Tests parse arguments"""
        self.assertEqual(1, 1)
