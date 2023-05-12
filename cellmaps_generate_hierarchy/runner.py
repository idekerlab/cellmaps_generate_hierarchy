#! /usr/bin/env python

import os
import logging
import time
import json
from datetime import date
from tqdm import tqdm
from cellmaps_utils import constants
from cellmaps_utils import logutils
from cellmaps_utils.provenance import ProvenanceUtil
import cellmaps_generate_hierarchy
from cellmaps_generate_hierarchy.exceptions import CellmapsGenerateHierarchyError


logger = logging.getLogger(__name__)


class CellmapsGenerateHierarchy(object):
    """
    Runs steps necessary to create PPI from embedding and to
    generate a hierarchy
    """
    def __init__(self, outdir=None,
                 inputdir=None,
                 ppigen=None,
                 hiergen=None,
                 name=None,
                 organization_name=None,
                 project_name=None,
                 provenance_utils=ProvenanceUtil(),
                 input_data_dict=None):
        """
        Constructor

        :param outdir: Directory to create and put results in
        :type outdir: str
        :param ppigen: PPI Network Generator object, should be a subclass
        :type ppigen: :py:class:`~cellmaps_generate_hierarchy.ppi.PPINetworkGenerator`
        :param hiergen: Hierarchy Generator object, should be a subclass
        :type hiergen: :py:class:`~cellmaps_generate_hierarchy.CXHierarchyGenerator`
        :param name:
        :param organization_name:
        :param project_name:
        :param provenance_utils:
        """
        logger.debug('In constructor')
        if outdir is None:
            raise CellmapsGenerateHierarchyError('outdir is None')
        self._outdir = os.path.abspath(outdir)
        self._inputdir = inputdir
        self._start_time = int(time.time())
        self._ppigen = ppigen
        self._hiergen = hiergen
        self._name = name
        self._project_name = project_name
        self._organization_name = organization_name
        self._input_data_dict = input_data_dict
        self._provenance_utils = provenance_utils

    def _create_rocrate(self):
        """
        Creates rocrate for output directory

        :raises CellMapsProvenanceError: If there is an error
        """
        logger.debug('Registering rocrate with FAIRSCAPE')
        name, proj_name, org_name = self._provenance_utils.get_name_project_org_of_rocrate(self._inputdir)

        if self._name is not None:
            name = self._name

        if self._organization_name is not None:
            org_name = self._organization_name

        if self._project_name is not None:
            proj_name = self._project_name
        try:
            self._provenance_utils.register_rocrate(self._outdir,
                                                    name=name,
                                                    organization_name=org_name,
                                                    project_name=proj_name)
        except TypeError as te:
            raise CellmapsGenerateHierarchyError('Invalid provenance: ' + str(te))
        except KeyError as ke:
            raise CellmapsGenerateHierarchyError('Key missing in provenance: ' + str(ke))

    def _register_software(self):
        """
        Registers this tool

        :raises CellMapsImageEmbeddingError: If fairscape call fails
        """
        self._softwareid = self._provenance_utils.register_software(self._outdir,
                                                                    name=cellmaps_generate_hierarchy.__name__,
                                                                    description=cellmaps_generate_hierarchy.__description__,
                                                                    author=cellmaps_generate_hierarchy.__author__,
                                                                    version=cellmaps_generate_hierarchy.__version__,
                                                                    file_format='.py',
                                                                    url=cellmaps_generate_hierarchy.__repo_url__)

    def _register_computation(self, generated_dataset_ids=[]):
        """
        # Todo: added inused dataset, software and what is being generated
        :return:
        """
        logger.debug('Getting id of input rocrate')
        input_dataset_id = self._provenance_utils.get_id_of_rocrate(self._inputdir)
        self._provenance_utils.register_computation(self._outdir,
                                                    name=cellmaps_generate_hierarchy.__name__ + ' computation',
                                                    run_by=str(os.getlogin()),
                                                    command=str(self._input_data_dict),
                                                    description='run of ' + cellmaps_generate_hierarchy.__name__,
                                                    used_software=[self._softwareid],
                                                    used_dataset=[input_dataset_id],
                                                    generated=generated_dataset_ids)

    def get_ppi_network_dest_file(self, ppi_network):
        """
        Gets the path where the PPI network should be written to

        :param ppi_network: PPI Network
        :type ppi_network: :py:class:`ndex2.nice_cx_network.NiceCXNetwork`
        :return: Path on filesystem to write the PPI network
        :rtype: str
        """
        cutoff = ppi_network.get_network_attribute('cutoff')['v']
        return os.path.join(self._outdir, constants.PPI_NETWORK_PREFIX +
                            '_cutoff_' + str(cutoff) + constants.CX_SUFFIX)

    def get_hierarchy_dest_file(self, hierarchy):
        """
        Gets the path where the hierarchy should be written to.
        Current implementation appends `_#cutoff` to filename
        where `#` is the cutoff value used in making the PPI network

        :param hierarchy: Hierarchy Network
        :type hierarchy: :py:class:`ndex2.nice_cx_network.NiceCXNetwork`
        :return: Path on filesystem to write Hierarchy Network
        :rtype: str
        """
        cutoff = 'unknown'
        try:
            cutoff = hierarchy.get_network_attribute('cutoff')['v']
        except Exception as e:
            logger.error('Unable to get cutoff from hierarchy network ' + str(e))

        return os.path.join(self._outdir, constants.HIERARCHY_NETWORK_PREFIX +
                            '_cutoff_' + str(cutoff) + constants.CX_SUFFIX)

    def run(self):
        """
        Runs CM4AI Generate Hierarchy


        :return:
        """
        exitcode = 99
        try:
            logger.debug('In run method')

            if os.path.isdir(self._outdir):
                raise CellmapsGenerateHierarchyError(self._outdir + ' already exists')

            if not os.path.isdir(self._outdir):
                os.makedirs(self._outdir, mode=0o755)

            logutils.setup_filelogger(outdir=self._outdir,
                                      handlerprefix='cellmaps_image_embedding')
            logutils.write_task_start_json(outdir=self._outdir,
                                           start_time=self._start_time,
                                           data={'commandlineargs': self._input_data_dict},
                                           version=cellmaps_generate_hierarchy.__version__)

            self._create_rocrate()

            self._register_software()
            generated_dataset_ids = []
            for ppi_network in tqdm(self._ppigen.get_next_network(), desc='Generating hierarchy'):

                logger.debug('Writing PPI network ' + str(ppi_network.get_name()))
                # write PPI to filesystem
                ppi_out_file = self.get_ppi_network_dest_file(ppi_network)
                with open(ppi_out_file, 'w') as f:
                    json.dump(ppi_network.to_cx(), f)

                # register ppi network file with fairscape
                data_dict = {'name': os.path.basename(ppi_out_file) + ' PPI network file',
                             'description': 'PPI Network file',
                             'data-format': 'CX',
                             'author': cellmaps_generate_hierarchy.__name__,
                             'version': cellmaps_generate_hierarchy.__version__,
                             'date-published': date.today().strftime('%m-%d-%Y')}
                generated_dataset_ids.append(self._provenance_utils.register_dataset(self._outdir,
                                                                                     source_file=ppi_out_file,
                                                                                     data_dict=data_dict))

                # generate hierarchy
                logger.info('Creating hierarchy')
                hierarchy = self._hiergen.get_hierarchy(ppi_network)
                hierarchy_out_file = self.get_hierarchy_dest_file(hierarchy)
                with open(hierarchy_out_file, 'w') as f:
                    json.dump(hierarchy.to_cx(), f)
                    # register ppi network file with fairscape
                    data_dict = {'name': os.path.basename(hierarchy_out_file) + ' Hierarchy network file',
                                 'description': 'Hierarchy network file',
                                 'data-format': 'CX',
                                 'author': cellmaps_generate_hierarchy.__name__,
                                 'version': cellmaps_generate_hierarchy.__version__,
                                 'date-published': date.today().strftime('%m-%d-%Y')}
                    generated_dataset_ids.append(self._provenance_utils.register_dataset(self._outdir,
                                                                                         source_file=hierarchy_out_file,
                                                                                         data_dict=data_dict))

            self._register_computation(generated_dataset_ids=generated_dataset_ids)
            exitcode = 0
        finally:
            logutils.write_task_finish_json(outdir=self._outdir,
                                            start_time=self._start_time,
                                            status=exitcode)

        return exitcode
