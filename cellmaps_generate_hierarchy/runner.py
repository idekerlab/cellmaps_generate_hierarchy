#! /usr/bin/env python

import os
import logging
import time
from cellmaps_utils import constants

from cellmaps_utils import logutils
from cellmaps_utils.provenance import ProvenanceUtil
import cellmaps_generate_hierarchy
from cellmaps_generate_hierarchy.exceptions import CellmapsGenerateHierarchyError


logger = logging.getLogger(__name__)


class CellmapsGenerateHierarchy(object):
    """
    Class to run algorithm
    """
    def __init__(self, exitcode, outdir=None,
                 name=cellmaps_generate_hierarchy.__name__,
                 organization_name=None,
                 project_name=None,
                 provenance_utils=ProvenanceUtil()):
        """
        Constructor

        :param exitcode: value to return via :py:meth:`.CellmapsGenerateHierarchy.run` method
        :type int:
        """
        self._exitcode = exitcode
        logger.debug('In constructor')
        if outdir is None:
            raise CellmapsGenerateHierarchyError('outdir is None')
        self._outdir = os.path.abspath(outdir)
        self._start_time = int(time.time())
        self._name = name
        self._project_name = project_name
        self._organization_name = organization_name
        self._provenance_utils = provenance_utils

    def _create_run_crate(self):
        """
        Creates rocrate for output directory

        :raises CellMapsProvenanceError: If there is an error
        """
        name = self._name
        if name is None:
            name = 'TODO better set this via input rocrate'

        # TODO: If organization or project name is unset need to pull from input rocrate
        org_name = self._organization_name
        if org_name is None:
            org_name = 'TODO BETTER SET THIS via input rocrate'

        proj_name = self._project_name
        if proj_name is None:
            proj_name = 'TODO BETTER SET THIS via input rocrate'
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
                                                                    name=self._name,
                                                                    description=cellmaps_generate_hierarchy.__description__,
                                                                    author=cellmaps_generate_hierarchy.__author__,
                                                                    version=cellmaps_generate_hierarchy.__version__,
                                                                    file_format='.py',
                                                                    url=cellmaps_generate_hierarchy.__repo_url__)

    def _register_computation(self):
        """
        # Todo: added inused dataset, software and what is being generated
        :return:
        """
        self._provenance_utils.register_computation(self._outdir,
                                                    name=cellmaps_generate_hierarchy.__name__ + ' computation',
                                                    run_by=str(os.getlogin()),
                                                    command=str(self._input_data_dict),
                                                    description='run of ' + cellmaps_generate_hierarchy.__name__,
                                                    used_software=[self._softwareid])
                                                    #used_dataset=[self._unique_datasetid, self._samples_datasetid],
                                                    #generated=[self._image_gene_attrid])

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
                                           data={},
                                           version=cellmaps_generate_hierarchy.__version__)

            self._create_run_crate()

            # Todo: uncomment when fixed
            # register software fails due to this bug:
            # https://github.com/fairscape/fairscape-cli/issues/7
            # self._register_software()

            # Todo: add implementation here

            # Todo: uncomment when above work
            # Above registrations need to work for this to work
            # register computation
            # self._register_computation()
        finally:
            logutils.write_task_finish_json(outdir=self._outdir,
                                            start_time=self._start_time,
                                            status=exitcode)

        return exitcode


        """
        with open(os.path.join(self._outdir, 'music_edgelist.tsv'), 'w') as f:

            f.write('\t'.join(['GeneA', 'GeneB', 'Weight']) + '\n')
            for genea in uniq_genes:
                if len(genea) == 0:
                    continue
                for geneb in uniq_genes:
                    if len(geneb) == 0:
                        continue
                    if genea == geneb:
                        continue
                    f.write(str(genea) + '\t' + str(geneb) + '\t' +
                            str(random.random()) + '\n')
        """
        return self._exitcode
