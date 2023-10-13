#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `cellmaps_generate_hierarchy` package."""

import os
import shutil
import tempfile
import unittest

from cellmaps_utils.exceptions import CellMapsProvenanceError

from cellmaps_generate_hierarchy.exceptions import CellmapsGenerateHierarchyError
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
