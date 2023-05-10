#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `cellmaps_generate_hierarchy` package."""

import os
import tempfile
import shutil

import unittest
from cellmaps_generate_hierarchy import cellmaps_generate_hierarchycmd


class TestCellmaps_generate_hierarchy(unittest.TestCase):
    """Tests for `cellmaps_generate_hierarchy` package."""

    def setUp(self):
        """Set up test fixtures, if any."""

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_parse_arguments(self):
        """Tests parse arguments"""
        res = cellmaps_generate_hierarchycmd._parse_arguments('hi', ['outdir'])

        self.assertEqual('outdir', res.outdir)
        self.assertEqual(0, res.verbose)
        self.assertEqual(0, res.exitcode)
        self.assertEqual(None, res.logconf)

        someargs = ['outdir', '-vv', '--logconf', 'hi', '--exitcode', '3']
        res = cellmaps_generate_hierarchycmd._parse_arguments('hi', someargs)

        self.assertEqual(2, res.verbose)
        self.assertEqual('hi', res.logconf)
        self.assertEqual(3, res.exitcode)

    def test_main(self):
        """Tests main function"""

        # try where loading config is successful
        try:
            temp_dir = tempfile.mkdtemp()
            res = cellmaps_generate_hierarchycmd.main(['myprog.py',
                                                       temp_dir])
            self.assertEqual(res, 2)
        finally:
            shutil.rmtree(temp_dir)
