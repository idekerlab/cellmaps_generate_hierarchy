
import os
import sys
import csv
import logging
import subprocess
from datetime import date
import ndex2
import cdapsutil
import cellmaps_generate_hierarchy
from cellmaps_utils import constants
from cellmaps_utils.provenance import ProvenanceUtil
from cellmaps_generate_hierarchy.exceptions import CellmapsGenerateHierarchyError

logger = logging.getLogger(__name__)


class CXHierarchyGenerator(object):
    """
    Base class for generating hierarchy
    that is output in CX format following
    CDAPS style
    """
    def __init__(self,
                 provenance_utils=ProvenanceUtil(),
                 author='cellmaps_generate_hierarchy',
                 version=cellmaps_generate_hierarchy.__version__):
        """
        Constructor
        """
        self._provenance_utils = provenance_utils
        self._author = author
        self._version = version
        self._generated_dataset_ids = []

    def get_generated_dataset_ids(self):
        """
        Gets IDs of datasets created by this object
        that have been registered with FAIRSCAPE
        :return:
        """
        return self._generated_dataset_ids

    def get_hierarchy(self, networks):
        """
        Gets hierarchy


        :return:
        :rtype: :py:class:`~ndex2.nice_cx_network.NiceCXNetwork`
        """
        raise NotImplementedError('Subclasses need to implement')


class CDAPSHiDeFHierarchyGenerator(CXHierarchyGenerator):
    """
    Generates hierarchy using HiDeF
    """

    CDAPS_JSON_FILE = 'cdaps.json'

    EDGELIST_TSV = '.id.edgelist.tsv'

    HIDEF_OUT_PREFIX = 'hidef_output'

    TRANSLATED_HIDEF_OUT_PREFIX = 'hidefnames_output'

    CDRES_KEY_NAME = 'communityDetectionResult'

    NODE_CX_KEY_NAME = 'nodeAttributesAsCX2'

    ATTR_DEC_NAME = 'attributeDeclarations'

    PERSISTENCE_COL_NAME = 'HiDeF_persistence'

    def __init__(self, hidef_cmd='hidef_finder.py',
                 provenance_utils=ProvenanceUtil(),
                 refiner=None,
                 author='cellmaps_generate_hierarchy',
                 version=cellmaps_generate_hierarchy.__version__):
        """

        :param hidef_cmd: HiDeF command line binary
        :type hidef_cmd: str
        :param provenance_utils:
        :param author:
        :type author: str
        :param version:
        """
        super().__init__(provenance_utils=provenance_utils,
                         author=author,
                         version=version)
        self._refiner = refiner
        self._python = sys.executable
        if os.sep not in hidef_cmd:
            self._hidef_cmd = os.path.join(os.path.dirname(self._python), hidef_cmd)
        else:
            self._hidef_cmd = hidef_cmd

    def _get_max_node_id(self, nodes_file):
        """
        Examines the 'nodes_file' passed in and finds the value of
        highest node id.

        It is assumed the 'nodes_file' a tab delimited
        file of format:

        <CLUSTER NAME> <# NODES> <SPACE DELIMITED NODE IDS> <SCORE>

        :param nodes_file:
        :type nodes_file: Path to to nodes file from hidef output
        :return: highest node id found
        :rtype: int
        """
        maxval = None
        with open(nodes_file, 'r') as csvfile:
            linereader = csv.reader(csvfile, delimiter='\t')
            for row in linereader:
                for node in row[2].split(' '):
                    if maxval is None:
                        maxval = int(node)
                        continue
                    curval = int(node)
                    if curval > maxval:
                        maxval = curval
        return maxval

    def write_members_for_row(self, out_stream, row, cur_node_id):
        """
        Given a row from nodes file from hidef output the members
        of the clusters by parsing the <SPACE DELIMITED NODE IDS>
        as mentioned in :py:func:`#get_max_node_id` description.

        The output is written to `out_stream` for each node id
        in format:

        <cur_node_id>,<node id>,c-m;

        :param out_stream:
        :type out_stream: file like object
        :param row: Should be a line from hidef nodes file parsed
                    by :py:func:`csv.reader`
        :type row: iterator
        :param cur_node_id: id of cluster that contains the nodes
        :type cur_node_id: int
        :return: None
        """
        for node in row[2].split(' '):
            out_stream.write(str(cur_node_id) + ',' +
                             node + ',c-m;')

    def update_cluster_node_map(self, cluster_node_map, cluster, max_node_id):
        """
        Updates 'cluster_node_map' which is in format of

        <cluster name> => <node id>

        by adding 'cluster' to 'cluster_node_map' if it does not
        exist

        :param cluster_node_map: map of cluster names to node ids
        :type cluster_node_map: dict
        :param cluster: name of cluster
        :type cluster: str
        :param max_node_id: current max node id
        :type max_node_id: int
        :return: (new 'max_node_id' if 'cluster' was added otherwise 'max_node_id',
                  id corresponding to 'cluster' found in 'cluster_node_map')
        :rtype: tuple
        """
        if cluster not in cluster_node_map:
            max_node_id += 1
            cluster_node_map[cluster] = max_node_id
            cur_node_id = max_node_id
        else:
            cur_node_id = cluster_node_map[cluster]
        return max_node_id, cur_node_id

    def update_persistence_map(self, persistence_node_map, node_id, persistence_val):
        """

        :param persistence_node_map:
        :param node_id:
        :param persistence_val:
        :return:
        """
        if node_id not in persistence_node_map:
            persistence_node_map[node_id] = persistence_val

    def write_communities(self, out_stream, edge_file, cluster_node_map):
        """
        Writes out links between clusters in COMMUNITYDETECTRESULT format
        as noted in :py:func:`#convert_hidef_output_to_cdaps`

        using hidef edge file set in 'edge_file' that is expected to
        be in this tab delimited format:

        <SOURCE CLUSTER> <TARGET CLUSTER> <default>

        This function converts the <SOURCE CLUSTER> <TARGET CLUSTER>
        to new node ids (leveraging 'cluster_node_map')

        and writes the following output:

        <SOURCE CLUSTER NODE ID>,<TARGET CLUSTER NODE ID>,c-c;

        to the 'out_stream'

        :param out_stream: output stream
        :type out_stream: file like object
        :param edge_file: path to hidef edges file
        :type edge_file: str
        :return: None
        """
        with open(edge_file, 'r') as csvfile:
            linereader = csv.reader(csvfile, delimiter='\t')
            for row in linereader:
                out_stream.write(str(cluster_node_map[row[0]]) + ',' +
                                 str(cluster_node_map[row[1]]) + ',c-c;')
        out_stream.write('",')

    def write_persistence_node_attribute(self, out_stream, persistence_map):
        """

        :param out_stream:
        :param persistence_map:
        :return:
        """
        out_stream.write('"' + CDAPSHiDeFHierarchyGenerator.NODE_CX_KEY_NAME + '": {')
        out_stream.write('"' + CDAPSHiDeFHierarchyGenerator.ATTR_DEC_NAME + '": [{')
        out_stream.write('"nodes": { "' + CDAPSHiDeFHierarchyGenerator.PERSISTENCE_COL_NAME +
                         '": { "d": "integer", "a": "p1", "v": 0}}}],')
        out_stream.write('"nodes": [')
        is_first = True
        for key in persistence_map:
            if is_first is False:
                out_stream.write(',')
            else:
                is_first = False
            out_stream.write('{"id": ' + str(key) + ',')
            out_stream.write('"v": { "p1": ' + str(persistence_map[key]) + '}}')

        out_stream.write(']}}')

    def convert_hidef_output_to_cdaps(self, out_stream, outdir):
        """
        Looks for x.nodes and x.edges in `outdir` directory
        to generate output in COMMUNITYDETECTRESULT format:
        https://github.com/idekerlab/communitydetection-rest-server/wiki/COMMUNITYDETECTRESULT-format

        This method leverages

        :py:func:`#write_members_for_row`

        and

        :py:func:`#write_communities`

        to write output

        :param out_stream: output stream to write results
        :type out_stream: file like object
        :param outdir:
        :type outdir: str
        :return: None
        """
        nodefile = os.path.join(outdir,
                                CDAPSHiDeFHierarchyGenerator.HIDEF_OUT_PREFIX +
                                '.pruned.nodes')
        max_node_id = self._get_max_node_id(nodefile)
        cluster_node_map = {}
        persistence_map = {}
        out_stream.write('{"communityDetectionResult": "')
        with open(nodefile, 'r') as csvfile:
            linereader = csv.reader(csvfile, delimiter='\t')
            for row in linereader:
                max_node_id, cur_node_id = self.update_cluster_node_map(cluster_node_map,
                                                                        row[0],
                                                                        max_node_id)
                self.update_persistence_map(persistence_map, cur_node_id, row[-1])
                self.write_members_for_row(out_stream, row,
                                      cur_node_id)
        edge_file = os.path.join(outdir, CDAPSHiDeFHierarchyGenerator.HIDEF_OUT_PREFIX + '.pruned.edges')
        self.write_communities(out_stream, edge_file, cluster_node_map)
        self.write_persistence_node_attribute(out_stream, persistence_map)
        out_stream.write('\n')
        return None

    def _run_cmd(self, cmd, cwd=None, timeout=36000):
        """
        Runs command as a command line process

        :param cmd_to_run: command to run as list
        :type cmd_to_run: list
        :return: (return code, standard out, standard error)
        :rtype: tuple
        """
        logger.debug('Running command under ' + str(cwd) +
                     ' path: ' + str(cmd))
        p = subprocess.Popen(cmd, cwd=cwd,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        try:
            out, err = p.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            logger.warning('Timeout reached. Killing process')
            p.kill()
            out, err = p.communicate()
            raise CellmapsGenerateHierarchyError('Process timed out. exit code: ' +
                                                 str(p.returncode) +
                                                 ' stdout: ' + str(out) +
                                                 ' stderr: ' + str(err))

        return p.returncode, out, err

    def _get_largest_network(self, networks):
        """
        Finds largest network by file size

        :param networks: list of :py:class:`~ndex2.nice_cx_network.NiceCXNetwork` objects
        :type networks: list
        :return: Largest network
        :rtype: :py:class:`~ndex2.nice_cx_network.NiceCXNetwork`
        """
        largest_network = None
        max_file_size = 0
        for n in networks:
            file_size = os.path.getsize(n + constants.CX_SUFFIX)
            if file_size >= max_file_size:
                largest_network = n
                max_file_size = file_size
        return largest_network

    def _get_name_to_id_dict(self, network):
        """

        :param network:
        :return:
        """
        name_to_id = {}
        for node_id, node_obj in network.get_nodes():
            name_to_id[node_obj['n']] = node_id
        return name_to_id

    def _get_id_to_name_dict(self, network):
        """

        :param network:
        :return:
        """
        id_to_name = {}
        for node_id, node_obj in network.get_nodes():
            id_to_name[node_id] = node_obj['n']
        return id_to_name

    def _create_edgelist_files_for_networks(self, networks):
        """
        Iterates through **networks** prefix paths and loads the
        CX files. Method then creates a PREFIX_PATH
        :py:const:`CDAPSHiDeFHierarchyGenerator.EDGELIST_TSV`
        file for each network and returns those paths as a list

        :param networks: Prefix paths of input PPI networks
        :type networks: list
        :return: (largest network path,
                  :py:class:`~ndex2.nice_cx_network.NiceCXNetwork`,
                  :py:class:`list`)
        :rtype: tuple
        """
        net_paths = []

        largest_network_path = self._get_largest_network(networks)
        largest_network = ndex2.create_nice_cx_from_file(largest_network_path + constants.CX_SUFFIX)
        logger.debug('Largest network name: ' + largest_network.get_name())
        largest_name_to_id = self._get_name_to_id_dict(largest_network)

        for n in networks:
            if largest_network_path == n:
                net = largest_network
            else:
                logger.debug('Creating NiceCXNetwork object from: ' + n + constants.CX_SUFFIX)
                net = ndex2.create_nice_cx_from_file(n + constants.CX_SUFFIX)
            dest_path = n + CDAPSHiDeFHierarchyGenerator.EDGELIST_TSV
            net_paths.append(dest_path)
            logger.debug('Writing out id edgelist: ' + str(dest_path))
            id_to_name = self._get_id_to_name_dict(net)
            with open(dest_path, 'w') as f:
                for edge_id, edge_obj in net.get_edges():
                    f.write(str(largest_name_to_id[id_to_name[edge_obj['s']]]) +
                            '\t' +
                            str(largest_name_to_id[id_to_name[edge_obj['t']]]) +
                            '\n')

                # register edgelist file with fairscape
                data_dict = {'name': os.path.basename(dest_path) +
                             ' PPI id edgelist file',
                             'description': 'PPI id edgelist file',
                             'data-format': 'tsv',
                             'author': str(self._author),
                             'version': str(self._version),
                             'date-published': date.today().strftime('%m-%d-%Y')}
                dataset_id = self._provenance_utils.register_dataset(os.path.dirname(dest_path),
                                                                     source_file=dest_path,
                                                                     data_dict=data_dict)
                self._generated_dataset_ids.append(dataset_id)

        logger.debug('Largest network name: ' + largest_network.get_name())
        return (largest_network_path + constants.CX_SUFFIX,
                largest_network, net_paths)

    def _register_hidef_output_files(self, outdir):
        """
        Register <HIDEF_PREFIX>.nodes and <HIDEF_PREFIX>.edges
        and <HIDEF_PREFIX>.weaver files with FAIRSCAPE

        """

        for hidef_file in [('nodes', 'tsv'),
                           ('edges', 'tsv'),
                           ('weaver', 'npy')]:
            outfile = os.path.join(outdir,
                                   CDAPSHiDeFHierarchyGenerator.HIDEF_OUT_PREFIX +
                                   '.' + hidef_file[0])
            data_dict = {'name': os.path.basename(outfile) +
                         ' HiDeF output ' + hidef_file[0] + ' file',
                         'description': ' HiDeF output ' + hidef_file[0] + ' file',
                         'data-format': hidef_file[1],
                         'author': str(self._author),
                         'version': str(self._version),
                         'date-published': date.today().strftime('%m-%d-%Y')}
            dataset_id = self._provenance_utils.register_dataset(os.path.dirname(outfile),
                                                                 source_file=outfile,
                                                                 data_dict=data_dict)
            self._generated_dataset_ids.append(dataset_id)

    def _annotate_hierarchy(self, network=None, path=None):
        """
        Adds HCX attributes to network as well as sets

        ``prov:wasGeneratedBy`` to the name and version of this tool

        ``prov:wasDerivedFrom`` to FAIRSCAPE dataset id of this rocrate

        :param network: Hierarchy
        :type network: :py:class:`~ndex2.nice_cx_network.NiceCXNetwork`
        :param path: Path to largest PPI network in CX or CX2 format
        :type path: str
        """
        network.set_network_attribute(name='prov:wasGeneratedBy',
                                      values=self._author + ' ' + self._version)
        network.set_network_attribute(name='prov:wasDerivedFrom',
                                      values='RO-crate: ' + os.path.dirname(path))

    def get_hierarchy(self, networks):
        """
        Runs HiDeF to generate hierarchy and registers resulting output
        files with FAIRSCAPE. To do this the method generates edgelist
        files from the CX files corresponding to the **networks** using
        the internal node ids for edge source and target names. These
        files are written to the same directory as the **networks**
        with HiDeF
        is then given all these networks via ``--g`` flag.



        .. warning::

            Due to FAIRSCAPE registration this method is NOT threadsafe and
            cannot be called in parallel or with any other call that is
            updating FAIRSCAPE registration on the current RO-CRATE

        :param networks: Paths (without suffix ie .cx) to PPI networks to be
                         used as input to HiDeF
        :type networks: list
        :raises CellmapsGenerateHierarchyError: If there was an error
        :return: Resulting hierarchy or ``None`` if no hierarchy from HiDeF
        :rtype: :py:class:`~ndex2.nice_cx_network.NiceCXNetwork`
        """
        outdir = os.path.dirname(networks[0])

        (largest_net_path, largest_net,
         edgelist_files) = self._create_edgelist_files_for_networks(networks)

        cmd = [self._python, self._hidef_cmd, '--g']
        cmd.extend(edgelist_files)
        outputprefix = os.path.join(outdir, CDAPSHiDeFHierarchyGenerator.HIDEF_OUT_PREFIX)
        cmd.extend(['--o', outputprefix,
                    '--alg', 'leiden', '--maxres', '80', '--k', '10',
                    '--skipgml'])

        exit_code, out, err = self._run_cmd(cmd)

        if exit_code != 0:
            logger.error('Cmd failed with exit code: ' + str(exit_code) +
                         ' : ' + str(out) + ' : ' + str(err))
            raise CellmapsGenerateHierarchyError('Cmd failed with exit code: ' + str(exit_code) +
                                                 ' : ' + str(out) + ' : ' + str(err))

        self._register_hidef_output_files(outdir)

        try:
            if self._refiner is not None:
                self._refiner.refine_hierarchy(outprefix=outputprefix)

            cdaps_out_file = os.path.join(outdir,
                                          CDAPSHiDeFHierarchyGenerator.CDAPS_JSON_FILE)
            with open(cdaps_out_file, 'w') as out_stream:
                self.convert_hidef_output_to_cdaps(out_stream, outdir)

            # register cdaps json file with fairscape
            data_dict = {'name': os.path.basename(cdaps_out_file) +
                         ' CDAPS output JSON file',
                         'description': 'CDAPS output JSON file',
                         'data-format': 'json',
                         'author': str(self._author),
                         'version': str(self._version),
                         'date-published': date.today().strftime('%m-%d-%Y')}
            dataset_id = self._provenance_utils.register_dataset(os.path.dirname(cdaps_out_file),
                                                                 source_file=cdaps_out_file,
                                                                 data_dict=data_dict)
            self._generated_dataset_ids.append(dataset_id)

            cd = cdapsutil.CommunityDetection(runner=cdapsutil.ExternalResultsRunner())
            hier = cd.run_community_detection(largest_net, algorithm=cdaps_out_file)
            self._annotate_hierarchy(network=hier, path=largest_net_path)
            return hier

        except FileNotFoundError as fe:
            logger.error('No output from hidef: ' + str(fe) + '\n')
        return None
