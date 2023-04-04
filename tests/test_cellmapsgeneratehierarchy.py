#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `cellmaps_generate_hierarchy` package."""


import unittest
from cellmaps_generate_hierarchy.runner import CellmapsgeneratehierarchyRunner


class TestCellmapsgeneratehierarchyrunner(unittest.TestCase):
    """Tests for `cellmaps_generate_hierarchy` package."""

    def setUp(self):
        """Set up test fixtures, if any."""

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_constructor(self):
        """Tests constructor"""
        myobj = CellmapsgeneratehierarchyRunner(0)

        self.assertIsNotNone(myobj)

    def test_run(self):
        """ Tests run()"""
        myobj = CellmapsgeneratehierarchyRunner(4)
        self.assertEqual(4, myobj.run())
