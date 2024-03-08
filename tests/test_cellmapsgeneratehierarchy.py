#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `cellmaps_generate_hierarchy` package."""

import os
import shutil
import tempfile
import json
import unittest
from unittest.mock import MagicMock, ANY

from cellmaps_utils.exceptions import CellMapsProvenanceError
from ndex2.cx2 import CX2Network

import cellmaps_generate_hierarchy
from cellmaps_utils import constants

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
        self.assertEqual(result, ("uuid12345", 'http://some-url.com/uuid12345'))

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
            myobj._save_network(net)
            self.fail('Expected exception')
        except CellmapsGenerateHierarchyError as he:
            self.assertTrue('An error occurred while saving the network to NDEx: ' in str(he))

    def test_update_hcx_annotations(self):
        mock_hierarchy = CX2Network()
        mock_hierarchy._network_attributes = {'HCX::interactionNetworkName': 'mock_name'}
        interactome_id = "test-uuid"
        myobj = NDExHierarchyUploader(ndexserver='server', ndexuser='user', ndexpassword='password')
        updated_hierarchy = myobj._update_hcx_annotations(mock_hierarchy, interactome_id)

        self.assertEqual(updated_hierarchy.get_network_attributes()['HCX::interactionNetworkUUID'], interactome_id)
        self.assertFalse('HCX::interactionNetworkName' in updated_hierarchy.get_network_attributes())

    def test_create_rocrate(self):

        prov = MagicMock()
        prov.register_rocrate = MagicMock()
        gen = CellmapsGenerateHierarchy(outdir='/foo', inputdirs=[], name='crate name',
                                        organization_name='organization name',
                                        project_name='project name', provenance_utils=prov)
        gen._description = 'description'
        gen._create_rocrate()
        prov.register_rocrate.assert_called_with('/foo', name='crate name',
                                                 organization_name='organization name',
                                                 project_name='project name',
                                                 description='description',
                                                 keywords=None)

    def test_create_rocrate_raise_type_error(self):

        prov = MagicMock()
        prov.register_rocrate = MagicMock(side_effect=TypeError('uh'))
        try:
            gen = CellmapsGenerateHierarchy(outdir='/foo', provenance_utils=prov)
            gen._create_rocrate()
            self.fail('expected exception')
        except CellmapsGenerateHierarchyError as ce:
            self.assertTrue('Invalid provenance: uh' in str(ce))

    def test_create_rocrate_raise_key_error(self):

        prov = MagicMock()
        prov.register_rocrate = MagicMock(side_effect=KeyError('uh'))
        try:
            gen = CellmapsGenerateHierarchy(outdir='/foo', provenance_utils=prov)
            gen._create_rocrate()
            self.fail('expected exception')
        except CellmapsGenerateHierarchyError as ce:
            self.assertTrue('Key missing in provenance: ' in str(ce))

    def test_update_provenance_fields(self):
        prov = MagicMock()
        prov.get_merged_rocrate_provenance_attrs = MagicMock()
        gen = CellmapsGenerateHierarchy(outdir='/foo', inputdirs=['/crate1'],
                                        provenance_utils=prov)
        gen._update_provenance_fields()
        prov.get_merged_rocrate_provenance_attrs.assert_called_with(['/crate1'], override_name=None,
                                                                    override_project_name=None,
                                                                    override_organization_name=None,
                                                                    extra_keywords=['hierarchy', 'model'])

    def test_register_software(self):

        prov = MagicMock()
        prov.register_software = MagicMock()
        gen = CellmapsGenerateHierarchy(outdir='/foo',
                                        provenance_utils=prov)
        gen._description = 'description'
        gen._keywords = ['hi']
        gen._register_software()
        software_description = gen._description + ' ' + cellmaps_generate_hierarchy.__description__
        prov.register_software.assert_called_once()
        self.assertEqual(('/foo',), prov.register_software.call_args.args)
        self.assertEqual('cellmaps_generate_hierarchy', prov.register_software.call_args.kwargs['name'])
        self.assertEqual(software_description, prov.register_software.call_args.kwargs['description'])
        self.assertEqual(cellmaps_generate_hierarchy.__author__, prov.register_software.call_args.kwargs['author'])
        self.assertEqual(cellmaps_generate_hierarchy.__version__, prov.register_software.call_args.kwargs['version'])
        self.assertEqual('py', prov.register_software.call_args.kwargs['file_format'])
        self.assertEqual(cellmaps_generate_hierarchy.__repo_url__, prov.register_software.call_args.kwargs['url'])
        self.assertEqual(3, len(prov.register_software.call_args.kwargs['keywords']))
        self.assertTrue('hi' in prov.register_software.call_args.kwargs['keywords'])
        self.assertTrue('tools' in prov.register_software.call_args.kwargs['keywords'])
        self.assertTrue('cellmaps_generate_hierarchy' in prov.register_software.call_args.kwargs['keywords'])

    def test_register_computation(self):

        prov = MagicMock()
        prov.register_computation = MagicMock()
        prov.get_login = MagicMock(return_value='smith')
        prov.get_id_of_rocrate = MagicMock(return_value='someid')
        gen = CellmapsGenerateHierarchy(outdir='/foo',
                                        provenance_utils=prov,
                                        input_data_dict={'foo': 'hi'})
        gen._inputdirs = '/xdir'
        gen._description = 'description'
        gen._keywords = ['hi']
        gen._softwareid = 'softid'
        gen._register_computation(['oneid'])

        description = gen._description + ' run of ' + cellmaps_generate_hierarchy.__name__
        prov.register_computation.assert_called_once()
        self.assertEqual(('/foo',), prov.register_computation.call_args.args)
        self.assertEqual('smith', prov.register_computation.call_args.kwargs['run_by'])
        self.assertEqual(description, prov.register_computation.call_args.kwargs['description'])
        self.assertEqual("{'foo': 'hi'}", prov.register_computation.call_args.kwargs['command'])
        self.assertEqual(['softid'], prov.register_computation.call_args.kwargs['used_software'])
        self.assertEqual(['someid'], prov.register_computation.call_args.kwargs['used_dataset'])
        self.assertEqual(['oneid'], prov.register_computation.call_args.kwargs['generated'])
        self.assertEqual(2, len(prov.register_computation.call_args.kwargs['keywords']))
        self.assertTrue('hi' in prov.register_computation.call_args.kwargs['keywords'])
        self.assertTrue('computation' in prov.register_computation.call_args.kwargs['keywords'])

    def test_register_computation_list_of_inputdirs(self):

        prov = MagicMock()
        prov.register_computation = MagicMock()
        prov.get_login = MagicMock(return_value='smith')
        prov.get_id_of_rocrate = MagicMock(side_effect=['1id', '2id'])
        gen = CellmapsGenerateHierarchy(outdir='/foo',
                                        provenance_utils=prov,
                                        input_data_dict={'foo': 'hi'})
        gen._inputdirs = ['/1', '/2']
        gen._description = 'description'
        gen._keywords = ['hi']
        gen._softwareid = 'softid'
        gen._register_computation(['oneid'])

        description = gen._description + ' run of ' + cellmaps_generate_hierarchy.__name__
        prov.register_computation.assert_called_once()
        self.assertEqual(('/foo',), prov.register_computation.call_args.args)
        self.assertEqual('smith', prov.register_computation.call_args.kwargs['run_by'])
        self.assertEqual(description, prov.register_computation.call_args.kwargs['description'])
        self.assertEqual("{'foo': 'hi'}", prov.register_computation.call_args.kwargs['command'])
        self.assertEqual(['softid'], prov.register_computation.call_args.kwargs['used_software'])
        self.assertEqual(['1id', '2id'], prov.register_computation.call_args.kwargs['used_dataset'])
        self.assertEqual(['oneid'], prov.register_computation.call_args.kwargs['generated'])
        self.assertEqual(2, len(prov.register_computation.call_args.kwargs['keywords']))
        self.assertTrue('hi' in prov.register_computation.call_args.kwargs['keywords'])
        self.assertTrue('computation' in prov.register_computation.call_args.kwargs['keywords'])

    def test_get_ppi_network_dest_file(self):
        ppi_net = MagicMock()
        ppi_net.get_network_attribute = MagicMock(return_value={'v': 1.5})
        gen = CellmapsGenerateHierarchy(outdir='/foo')
        self.assertEqual(os.path.join('/foo', constants.PPI_NETWORK_PREFIX + '_cutoff_1.5'),
                         gen.get_ppi_network_dest_file(ppi_network=ppi_net))

    def test_get_hierarchy_dest_file(self):
        gen = CellmapsGenerateHierarchy(outdir='/foo')
        self.assertEqual(os.path.join('/foo', constants.HIERARCHY_NETWORK_PREFIX),
                         gen.get_hierarchy_dest_file())

    def test_get_hierarchy_parent_network_dest_file(self):
        gen = CellmapsGenerateHierarchy(outdir='/foo')
        self.assertEqual(os.path.join('/foo', 'hierarchy_parent'),
                         gen.get_hierarchy_parent_network_dest_file())

    def test_remove_ppi_networks(self):
        temp_dir = tempfile.mkdtemp()
        try:
            afile = os.path.join(temp_dir, 'foo' + constants.CX_SUFFIX)
            open(afile, 'a').close()
            gen = CellmapsGenerateHierarchy(outdir=temp_dir)
            gen._remove_ppi_networks([os.path.join(temp_dir, 'foo'),
                                      os.path.join(temp_dir, 'doesnotexist')])
            self.assertFalse(os.path.isfile(afile))
        finally:
            shutil.rmtree(temp_dir)

    def test_write_ppi_network_as_cx(self):
        temp_dir = tempfile.mkdtemp()
        try:
            afile = os.path.join(temp_dir, 'hi.json')
            ppi_net = MagicMock()
            ppi_net.get_name = MagicMock(return_value='foo')
            ppi_net.to_cx = MagicMock(return_value={'foo': 'hi'})
            gen = CellmapsGenerateHierarchy(outdir='/foo')
            gen._write_ppi_network_as_cx(ppi_net, dest_path=afile)
            self.assertTrue(os.path.isfile(afile))
            with open(afile, 'r') as f:
                data = json.load(f)
            self.assertEqual({'foo': 'hi'}, data)
        finally:
            shutil.rmtree(temp_dir)

    def test_register_ppi_network(self):
        prov = MagicMock()
        prov.get_default_date_format_str = MagicMock(return_value='Y')
        ppi_net = MagicMock()
        ppi_net.get_name = MagicMock(return_value='net_name')
        prov.register_dataset = MagicMock(return_value='1')
        gen = CellmapsGenerateHierarchy(outdir='/foo',
                                        provenance_utils=prov)
        gen._description = 'description'
        gen._keywords = ['1', '1']
        res = gen._register_ppi_network(ppi_net, dest_path='/src/x')
        self.assertEqual(res, '1')
        self.assertEqual(('/foo',), prov.register_dataset.call_args.args)
        self.assertEqual('/src/x', prov.register_dataset.call_args.kwargs['source_file'])
        prov.register_dataset.assert_called_once()
        self.assertEqual(('/foo',), prov.register_dataset.call_args.args)
        self.assertEqual('/src/x', prov.register_dataset.call_args.kwargs['source_file'])
        d_dict_passed_in = prov.register_dataset.call_args.kwargs['data_dict']
        self.assertEqual('x PPI network file', d_dict_passed_in['name'])
        self.assertEqual('description PPI Network file', d_dict_passed_in['description'])
        self.assertEqual('CX', d_dict_passed_in['data-format'])
        self.assertEqual(cellmaps_generate_hierarchy.__name__, d_dict_passed_in['author'])
        self.assertEqual(cellmaps_generate_hierarchy.__version__, d_dict_passed_in['version'])
        self.assertEqual('Y', d_dict_passed_in['date-published'])
        self.assertTrue(2, len(d_dict_passed_in['keywords']))
        self.assertTrue('1' in d_dict_passed_in['keywords'])
        self.assertTrue('file' in d_dict_passed_in['keywords'])

    def test_register_ppi_network_keywords_is_none(self):
        prov = MagicMock()
        prov.get_default_date_format_str = MagicMock(return_value='Y')
        ppi_net = MagicMock()
        ppi_net.get_name = MagicMock(return_value='net_name')
        prov.register_dataset = MagicMock(return_value='1')
        gen = CellmapsGenerateHierarchy(outdir='/foo',
                                        provenance_utils=prov)
        gen._description = 'description'
        gen._keywords = None
        res = gen._register_ppi_network(ppi_net, dest_path='/src/x')
        self.assertEqual(res, '1')
        self.assertEqual(('/foo',), prov.register_dataset.call_args.args)
        self.assertEqual('/src/x', prov.register_dataset.call_args.kwargs['source_file'])
        prov.register_dataset.assert_called_once()
        self.assertEqual(('/foo',), prov.register_dataset.call_args.args)
        self.assertEqual('/src/x', prov.register_dataset.call_args.kwargs['source_file'])
        d_dict_passed_in = prov.register_dataset.call_args.kwargs['data_dict']
        self.assertEqual('x PPI network file', d_dict_passed_in['name'])
        self.assertEqual('description PPI Network file', d_dict_passed_in['description'])
        self.assertEqual('CX', d_dict_passed_in['data-format'])
        self.assertEqual(cellmaps_generate_hierarchy.__name__, d_dict_passed_in['author'])
        self.assertEqual(cellmaps_generate_hierarchy.__version__, d_dict_passed_in['version'])
        self.assertEqual('Y', d_dict_passed_in['date-published'])
        self.assertTrue(1, len(d_dict_passed_in['keywords']))
        self.assertTrue('file' in d_dict_passed_in['keywords'])

    def test_write_hierarchy_network(self):
        temp_dir = tempfile.mkdtemp()
        try:
            prov = MagicMock()
            prov.get_default_date_format_str = MagicMock(return_value='Y')
            ppi_net = MagicMock()
            ppi_net.get_name = MagicMock(return_value='net_name')
            prov.register_dataset = MagicMock(return_value='1')
            gen = CellmapsGenerateHierarchy(outdir=temp_dir,
                                            provenance_utils=prov)
            gen._description = 'description'
            gen._keywords = None
            res = gen._write_hierarchy_network(hierarchy=['hi'])
            self.assertEqual(os.path.join(temp_dir, 'hierarchy.cx2'), res)
            self.assertTrue(os.path.isfile(res))
            with open(res, 'r') as f:
                self.assertEqual(['hi'], json.load(f))
        finally:
            shutil.rmtree(temp_dir)

    # def test_register_hierarchy_network(self):


