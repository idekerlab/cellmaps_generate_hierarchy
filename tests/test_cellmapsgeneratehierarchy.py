#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `cellmaps_generate_hierarchy` package."""

import os
import shutil
import tempfile
import unittest
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

