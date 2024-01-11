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
        res = cellmaps_generate_hierarchycmd._parse_arguments('hi',
                                                              ['outdir',
                                                               '--coembedding_dirs', 'foo',
                                                               '--ndexuser', 'foouser',
                                                               '--ndexpassword', 'foopass'])

        self.assertEqual('outdir', res.outdir)
        self.assertEqual(['foo'], res.coembedding_dirs)
        self.assertEqual(1, res.verbose)
        self.assertEqual(None, res.logconf)

        someargs = ['outdir', '-vv', '--logconf', 'hi',
                    '--coembedding_dirs', 'blah',
                    '--ndexuser', 'foouser',
                    '--ndexpassword', 'foopass']
        res = cellmaps_generate_hierarchycmd._parse_arguments('hi', someargs)

        self.assertEqual(3, res.verbose)
        self.assertEqual('hi', res.logconf)

    def test_main(self):
        """Tests main function"""

        # try where loading config is successful
        try:
            temp_dir = tempfile.mkdtemp()
            res = cellmaps_generate_hierarchycmd.main(['myprog.py',
                                                       temp_dir,
                                                       '--coembedding_dirs', 'foo',
                                                       '--ndexuser', 'foouser',
                                                       '--ndexpassword', 'foopass'])
            self.assertEqual(res, 2)
        finally:
            shutil.rmtree(temp_dir)
