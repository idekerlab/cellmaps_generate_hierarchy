#! /usr/bin/env python

import os
import logging
import re
import time
import json
import warnings
from datetime import date

import ndex2
import pandas as pd
from tqdm import tqdm
from cellmaps_utils import constants
from cellmaps_utils import logutils
from cellmaps_utils.provenance import ProvenanceUtil
import cellmaps_generate_hierarchy
from cellmaps_generate_hierarchy.exceptions import CellmapsGenerateHierarchyError
from cellmaps_generate_hierarchy.hidefconverter import HierarchyToHiDeFConverter
from cellmaps_generate_hierarchy.ndexupload import NDExHierarchyUploader

logger = logging.getLogger(__name__)


class CellmapsGenerateHierarchy(object):
    """
    Runs steps necessary to create PPI from embedding and to
    generate a hierarchy
    """

    def __init__(self, outdir=None,
                 inputdirs=[],
                 ppigen=None,
                 algorithm='leiden',
                 maxres=80,
                 k=10,
                 gene_node_attributes=None,
                 hiergen=None,
                 name=None,
                 organization_name=None,
                 project_name=None,
                 layoutalgo=None,
                 skip_logging=True,
                 provenance_utils=ProvenanceUtil(),
                 input_data_dict=None,
                 ndexserver=None,
                 ndexuser=None,
                 ndexpassword=None,
                 visibility=None,
                 keep_intermediate_files=False
                 ):
        """
        Constructor

        :param outdir: Directory to create and put results in
        :type outdir: str
        :param ppigen: PPI Network Generator object, should be a subclass
        :type ppigen: :py:class:`~cellmaps_generate_hierarchy.ppi.PPINetworkGenerator`
        :param hiergen: Hierarchy Generator object, should be a subclass
        :type hiergen: :py:class:`~cellmaps_generate_hierarchy.HierarchyGenerator`
        :param name:
        :param organization_name:
        :param project_name:
        :param skip_logging: If ``True`` skip logging, if ``None`` or ``False`` do NOT skip logging
        :type skip_logging: bool
        :param provenance_utils:
        :param ndexserver:
        :type ndexserver: str
        :param ndexuser:
        :type ndexuser: str
        :param ndexpassword:
        :type ndexpassword: str
        :param visibility: If set to ``public``, ``PUBLIC`` or ``True`` sets hierarchy and interactome to
                           publicly visibility on NDEx, otherwise they are left as private
        :type visibility: str or bool
        """
        logger.debug('In constructor')
        if outdir is None:
            raise CellmapsGenerateHierarchyError('outdir is None')
        self._outdir = os.path.abspath(outdir)
        self._inputdirs = inputdirs
        self._start_time = int(time.time())
        self._ppigen = ppigen
        self._algorithm = algorithm
        self._maxres = maxres
        self._k = k
        self._gene_node_attributes = gene_node_attributes
        self._hiergen = hiergen
        self._name = name
        self._project_name = project_name
        self._organization_name = organization_name
        self._keywords = None
        self._description = None
        if skip_logging is None:
            self._skip_logging = False
        else:
            self._skip_logging = skip_logging
        self._input_data_dict = input_data_dict
        self._provenance_utils = provenance_utils
        self._layoutalgo = layoutalgo
        self._server = ndexserver
        self._user = ndexuser
        self._password = ndexpassword
        self._visibility = visibility
        self.keep_intermediate_files = keep_intermediate_files

    def _update_provenance_fields(self):
        """

        :return:
        """

        prov_attrs = self._provenance_utils.get_merged_rocrate_provenance_attrs(self._inputdirs,
                                                                                override_name=self._name,
                                                                                override_project_name=self._project_name,
                                                                                override_organization_name=self._organization_name,
                                                                                extra_keywords=['hierarchy', 'model'])

        self._name = prov_attrs.get_name()
        self._organization_name = prov_attrs.get_organization_name()
        self._project_name = prov_attrs.get_project_name()
        self._keywords = prov_attrs.get_keywords()
        self._description = prov_attrs.get_description()

    def _create_rocrate(self):
        """
        Creates rocrate for output directory

        :raises CellMapsProvenanceError: If there is an error
        """
        logger.debug('Registering rocrate with FAIRSCAPE')

        try:
            self._provenance_utils.register_rocrate(self._outdir,
                                                    name=self._name,
                                                    organization_name=self._organization_name,
                                                    project_name=self._project_name,
                                                    description=self._description,
                                                    keywords=self._keywords)
        except TypeError as te:
            raise CellmapsGenerateHierarchyError('Invalid provenance: ' + str(te))
        except KeyError as ke:
            raise CellmapsGenerateHierarchyError('Key missing in provenance: ' + str(ke))

    def _get_keywords_extended_with_new_values(self, new_values=None):
        """
        Takes keywords passed into constructor and append **new_values**
        and return a unique list of merged values

        :param new_values: new values
        :type new_values: list
        :return: merged list of keywords
        :rtype: list
        """
        if self._keywords is None or len(self._keywords) == 0:
            keywords = []
        else:
            keywords = self._keywords.copy()

        if isinstance(new_values, list):
            keywords.extend(new_values)
        else:
            keywords.append(new_values)

        return list(set(keywords))

    def _register_software(self):
        """
        Registers this tool

        :raises CellMapsImageEmbeddingError: If fairscape call fails
        """
        software_keywords = self._get_keywords_extended_with_new_values(new_values=['tools',
                                                                                    cellmaps_generate_hierarchy.__name__])
        software_description = self._description + ' ' + \
                               cellmaps_generate_hierarchy.__description__
        self._softwareid = self._provenance_utils.register_software(self._outdir,
                                                                    name=cellmaps_generate_hierarchy.__name__,
                                                                    description=software_description,
                                                                    author=cellmaps_generate_hierarchy.__author__,
                                                                    version=cellmaps_generate_hierarchy.__version__,
                                                                    file_format='py',
                                                                    keywords=software_keywords,
                                                                    url=cellmaps_generate_hierarchy.__repo_url__)

    def _register_computation(self, generated_dataset_ids=[]):
        """
        # Todo: added in used dataset, software and what is being generated
        :return:
        """
        logger.debug('Getting id of input rocrate')
        input_dataset_ids = []
        if isinstance(self._inputdirs, list):
            for i_dir in self._inputdirs:
                input_dataset_ids.append(self._provenance_utils.get_id_of_rocrate(i_dir))
        else:
            input_dataset_ids.append(self._provenance_utils.get_id_of_rocrate(self._inputdirs))

        keywords = self._get_keywords_extended_with_new_values(new_values=['computation'])
        description = self._description + ' run of ' + cellmaps_generate_hierarchy.__name__
        self._provenance_utils.register_computation(self._outdir,
                                                    name=cellmaps_generate_hierarchy.__computation_name__,
                                                    run_by=str(self._provenance_utils.get_login()),
                                                    command=str(self._input_data_dict),
                                                    description=description,
                                                    keywords=keywords,
                                                    used_software=[self._softwareid],
                                                    used_dataset=input_dataset_ids,
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
                            '_cutoff_' + str(cutoff))

    def get_hierarchy_dest_file(self):
        """
        Creates file path prefix for hierarchy

        Example path: ``/tmp/foo/hierarchy``

        :return: Prefix path on filesystem to write Hierarchy Network
        :rtype: str
        """
        return os.path.join(self._outdir, constants.HIERARCHY_NETWORK_PREFIX)

    def get_hierarchy_parent_network_dest_file(self):
        """
        Creates file path prefix for hierarchy parent network

        Example path: ``/tmp/foo/hierarchy_parent``
        :return:
        """
        return os.path.join(self._outdir, 'hierarchy_parent')

    def _remove_ppi_networks(self, networks_paths):
        for n in networks_paths:
            try:
                os.remove(n + constants.CX_SUFFIX)
            except Exception as e:
                logger.warning(f"Tried to remove ppi file {n}, but failed due to: {e}")

    def _write_ppi_network_as_cx(self, ppi_network, dest_path=None):
        """

        :param ppi_network:
        :return:
        """
        logger.debug('Writing PPI network ' + str(ppi_network.get_name()))
        # write PPI to filesystem

        with open(dest_path, 'w') as f:
            json.dump(ppi_network.to_cx(), f)

    def _register_ppi_network(self, ppi_network, dest_path=None):
        """

        :param ppi_network:
        :return:
        """
        logger.debug('Registering PPI network ' + str(ppi_network.get_name()))

        description = self._description
        description += ' PPI Network file'

        keywords = self._get_keywords_extended_with_new_values(new_values=['file'])

        # register ppi network file with fairscape
        data_dict = {'name': os.path.basename(dest_path) + ' PPI network file',
                     'description': description,
                     'keywords': keywords,
                     'data-format': 'CX',
                     'author': cellmaps_generate_hierarchy.__name__,
                     'version': cellmaps_generate_hierarchy.__version__,
                     'date-published': date.today().strftime(self._provenance_utils.get_default_date_format_str())}
        return self._provenance_utils.register_dataset(self._outdir,
                                                       source_file=dest_path,
                                                       data_dict=data_dict)

    def _write_hierarchy_network(self, hierarchy=None):
        """
        Writes **hierarchy** to file

        :param hierarchy: CX2 network converted to list and dicts
        :type hierarchy: list
        :return: Path to hierarchy output file
        :rtype: str
        """
        logger.debug('Writing hierarchy')
        suffix = '.cx2'  # todo put this into cellmaps_utils.constants
        hierarchy_out_file = self.get_hierarchy_dest_file() + suffix
        with open(hierarchy_out_file, 'w') as f:
            json.dump(hierarchy, f)

        return hierarchy_out_file

    def _register_hierarchy_network(self, hierarchy_out_file=None, hierarchyurl=None):
        """

        :param network:
        :return:
        """
        logger.debug('Register hierarchy with fairscape')

        description = self._description
        description += ' Hierarchy network file'
        keywords = self._get_keywords_extended_with_new_values(new_values=['file',
                                                                           'hierarchy',
                                                                           'network',
                                                                           'HCX'])
        # register hierarchy network file with fairscape
        # The name must be Output Dataset so that the cm4ai portal knows to
        # grab the URL link
        data_dict = {'name': 'Output Dataset',
                     'description': description,
                     'keywords': keywords,
                     'data-format': 'HCX',
                     'author': cellmaps_generate_hierarchy.__name__,
                     'version': cellmaps_generate_hierarchy.__version__,
                     'date-published': date.today().strftime(self._provenance_utils.get_default_date_format_str())}
        if hierarchyurl is not None:
            data_dict['url'] = hierarchyurl
        dataset_id = self._provenance_utils.register_dataset(self._outdir,
                                                             source_file=hierarchy_out_file,
                                                             data_dict=data_dict)
        return dataset_id

    def _write_and_register_hierarchy_parent_network(self, parent=None, parenturl=None):
        """

        :param network:
        :return:
        """
        logger.debug('Writing hierarchy parent')
        suffix = '.cx2'  # todo put this into cellmaps_utils.constants
        parent_out_file = self.get_hierarchy_parent_network_dest_file() + suffix
        with open(parent_out_file, 'w') as f:
            json.dump(parent, f)
        description = self._description
        description += ' Hierarchy parent network file'
        keywords = self._get_keywords_extended_with_new_values(new_values=['file',
                                                                           'parent',
                                                                           'interactome',
                                                                           'ppi',
                                                                           'network',
                                                                           'CX2'])

        data_dict = {'name': 'Hierarchy parent network',
                     'description': description,
                     'keywords': keywords,
                     'data-format': 'CX2',
                     'author': cellmaps_generate_hierarchy.__name__,
                     'version': cellmaps_generate_hierarchy.__version__,
                     'date-published': date.today().strftime(self._provenance_utils.get_default_date_format_str())}
        if parenturl is not None:
            data_dict['url'] = parenturl
        dataset_id = self._provenance_utils.register_dataset(self._outdir,
                                                             source_file=parent_out_file,
                                                             data_dict=data_dict)
        return dataset_id

    def _register_hidef_output_with_gene_names(self, hidef_output_path, hidef_output_name):
        """
        """
        logger.debug(f'Registering hidef output {hidef_output_name} with gene names')

        description = self._description
        description += f' HiDeF output {hidef_output_name} with gene names file'

        keywords = self._get_keywords_extended_with_new_values(new_values=['file'])

        # register file with fairscape
        data_dict = {'name': f'HiDeF output {hidef_output_name} with gene names',
                     'description': description,
                     'keywords': keywords,
                     'data-format': "tsv",
                     'author': cellmaps_generate_hierarchy.__name__,
                     'version': cellmaps_generate_hierarchy.__version__,
                     'date-published': date.today().strftime(self._provenance_utils.get_default_date_format_str())}
        return self._provenance_utils.register_dataset(self._outdir,
                                                       source_file=hidef_output_path,
                                                       data_dict=data_dict)

    def _add_gene_node_attributes(self, parent_ppi):
        """
        Adds gene node attributes to the parent PPI network from provided TSV files or found in ro-crates.

        :param parent_ppi: The PPI network to which the attributes will be added.
        :type parent_ppi: :py:class:`ndex2.cx2.CX2Network`
        :return: The parent PPI network object with the new attributes added.
        :rtype: :py:class:`ndex2.cx2.CX2Network`
        """
        node_name_dict = {}
        for node_id, node_obj in parent_ppi.get_nodes().items():
            node_name_dict[node_obj['v']['name']] = node_id

        for entry_path in self._gene_node_attributes:
            attr_files = list()
            if os.path.isdir(entry_path):
                attr_files.extend([os.path.join(entry_path, f) for f in os.listdir(entry_path)
                                   if re.match(r'\d+_' + re.escape(constants.IMAGE_GENE_NODE_ATTR_FILE), f)])

                ppi_attr_file = os.path.join(entry_path, constants.PPI_GENE_NODE_ATTR_FILE)
                if os.path.exists(ppi_attr_file):
                    attr_files.append(ppi_attr_file)

                if len(attr_files) < 1:
                    logger.warning(f"No attribute file found in directory {entry_path}")
                    continue
            elif entry_path.endswith('.tsv'):
                attr_files.append(entry_path)
            else:
                logger.warning(f"Entry is neither a directory nor a TSV file: {entry_path}")
                continue

            for attribute_file in attr_files:
                df = pd.read_csv(attribute_file, sep='\t', header=0)

                for _, row in df.iterrows():
                    gene_name = row.iloc[0]
                    node_id = node_name_dict.get(gene_name, None)
                    if node_id is None:
                        continue

                    for column_name in df.columns[1:]:
                        if not pd.isna(row[column_name]):
                            parent_ppi.add_node_attribute(node_id, column_name, row[column_name])
                            if column_name == 'represents' and row[column_name].startswith('ensembl:ENSG'):
                                ensembl_only = re.sub('^ensembl:', '', row[column_name])
                                # URL suggested by Jan to get HPA info
                                parent_ppi.add_node_attribute(node_id, 'representsurl',
                                                              'https://www.proteinatlas.org/' +
                                                              ensembl_only + '/subcellular')

                                # URL suggested by Jan to get all antibodies for given ensembl id
                                parent_ppi.add_node_attribute(node_id, 'antibodyurl',
                                                              'https://www.proteinatlas.org/' +
                                                              ensembl_only + '/summary/antibody')
        return parent_ppi

    def _get_network_attribute(self, network=None, attribute_name=None,
                               default='Unknown'):
        """
        Gets network attribute from **network** value matching
        **attribute_name** or value of **default** if not found

        :param network:
        :type network: :py:class:`~ndex2.cx2.CX2Network`
        :param attribute_name:
        :type attribute_name: str
        :param default:
        :type default: str
        :return:
        :rtype: str
        """
        net_attrs = network.get_network_attributes()
        if net_attrs is None:
            logger.info('Network lacks any network attributes. hmm....')
            return default
        if attribute_name in net_attrs:
            return net_attrs[attribute_name]
        logger.debug(str(attribute_name) + ' network attribute note found. using default')
        return default

    def _update_ppi_with_hierarchy_attributes(self, parent_ppi=None, hierarchy=None):
        """
        Updates parent_ppi aka parent network with some attributes from hierarchy
        namely **prov:wasGeneratedBy** and **prov:wasDerivedFrom**

        In addition
        :param hierarchy:
        :type hierarchy: :py:class:`~ndex2.cx2.CX2Network`
        """
        parent_ppi.add_network_attribute('prov:wasGeneratedBy',
                                         self._get_network_attribute(hierarchy, attribute_name='prov:wasGeneratedBy'))
        parent_ppi.add_network_attribute('prov:wasDerivedFrom',
                                         self._get_network_attribute(hierarchy, attribute_name='prov:wasDerivedFrom'))
        p_net_attrs = parent_ppi.get_network_attributes()
        parent_ppi.add_network_attribute('name', str(hierarchy.get_name() + ' ' + p_net_attrs['name']))

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
            if self._skip_logging is False:
                logutils.setup_filelogger(outdir=self._outdir,
                                          handlerprefix='cellmaps_image_embedding')
            logutils.write_task_start_json(outdir=self._outdir,
                                           start_time=self._start_time,
                                           data={'commandlineargs': self._input_data_dict},
                                           version=cellmaps_generate_hierarchy.__version__)
            self._update_provenance_fields()

            self._create_rocrate()

            self._register_software()

            generated_dataset_ids = []
            ppi_network_prefix_paths = []
            # generate PPI networks
            for ppi_network in tqdm(self._ppigen.get_next_network(), desc='Generating hierarchy'):
                dest_prefix = self.get_ppi_network_dest_file(ppi_network)
                ppi_network_prefix_paths.append(dest_prefix)
                cx_path = dest_prefix + constants.CX_SUFFIX
                self._write_ppi_network_as_cx(ppi_network, dest_path=cx_path)
                if self.keep_intermediate_files:
                    generated_dataset_ids.append(self._register_ppi_network(ppi_network, dest_path=cx_path))

            # generate hierarchy and get parent ppi
            hierarchy, parent_ppi = self._hiergen.get_hierarchy(ppi_network_prefix_paths, self._algorithm, self._maxres,
                                                                self._k)

            if not self.keep_intermediate_files:
                self._remove_ppi_networks(ppi_network_prefix_paths)

            if self._gene_node_attributes is not None:
                parent_ppi = self._add_gene_node_attributes(parent_ppi)

            parenturl = None
            hierarchyurl = None

            self._update_ppi_with_hierarchy_attributes(parent_ppi=parent_ppi, hierarchy=hierarchy)

            if self._server is not None and self._user is not None and self._password is not None:
                ndex_uploader = NDExHierarchyUploader(self._server, self._user, self._password, self._visibility)
                _, parenturl, _, hierarchyurl = ndex_uploader.save_hierarchy_and_parent_network(hierarchy, parent_ppi)
                message = (f'Hierarchy uploaded. To view hierarchy on NDEx please paste this URL in your browser '
                           f'{hierarchyurl}. To view Hierarchy on new experimental Cytoscape on the Web, '
                           f'go to {ndex_uploader.get_cytoscape_url(hierarchyurl)}')
                print(message)
                logger.info(message)

            hierarchy = hierarchy.to_cx2()
            parent_ppi = parent_ppi.to_cx2()

            # TODO: Need to support layout with HCX
            warnings.warn("Layout disabled due to incompatibilities with HCX format")
            # if self._layoutalgo is not None:
            #    logger.debug('Applying layout')
            #    self._layoutalgo.add_layout(network=hierarchy)
            # else:
            #    logger.debug('No layout algorithm set, skipping')

            # write out hierarchy
            hierarchy_out_file = self._write_hierarchy_network(hierarchy)

            # write out parent network and register with fairscape
            generated_dataset_ids.append(self._write_and_register_hierarchy_parent_network(parent=parent_ppi,
                                                                                           parenturl=parenturl))

            generated_dataset_ids.append(self._register_hierarchy_network(hierarchy_out_file,
                                                                          hierarchyurl=hierarchyurl))

            # add datasets created by hiergen object
            generated_dataset_ids.extend(self._hiergen.get_generated_dataset_ids())

            hidef_converter = HierarchyToHiDeFConverter(self._outdir, self._outdir)
            hidef_nodes, hidef_edges = hidef_converter.generate_hidef_files()
            generated_dataset_ids.append(
                self._register_hidef_output_with_gene_names(hidef_nodes, 'nodes'))
            generated_dataset_ids.append(
                self._register_hidef_output_with_gene_names(hidef_edges, 'edges'))

            # register generated datasets
            self._register_computation(generated_dataset_ids=generated_dataset_ids)
            exitcode = 0
        finally:
            logutils.write_task_finish_json(outdir=self._outdir,
                                            start_time=self._start_time,
                                            status=exitcode)

        return exitcode
