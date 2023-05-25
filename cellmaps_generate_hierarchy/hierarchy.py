
import os
import csv
import logging
import subprocess
from datetime import date
import ndex2
import cdapsutil
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
    def __init__(self):
        """
        Constructor
        """
        pass

    def get_hierarchy(self, networks):
        """
        Gets hierarchy


        :return:
        :rtype: :py:class:`~ndex2.nice_cx_network.NiceCXNetwork`
        """
        raise NotImplementedError('Subclasses need to implement')


class HiDeFHierarchyGenerator(CXHierarchyGenerator):
    """
    Generates hierarchy using HiDeF
    """

    HIDEF_OUT_PREFIX = 'hidef_output'

    CDRES_KEY_NAME = 'communityDetectionResult'

    NODE_CX_KEY_NAME = 'nodeAttributesAsCX2'

    ATTR_DEC_NAME = 'attributeDeclarations'

    PERSISTENCE_COL_NAME = 'HiDeF_persistence'

    def __init__(self, hidef_cmd='hidef_finder.py'):
        """
        Constructor
        """
        super().__init__()
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

    def update_persistence_map(persistence_node_map, node_id, persistence_val):
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
        out_stream.write('"' + HiDeFHierarchyGenerator.NODE_CX_KEY_NAME + '": {')
        out_stream.write('"' + HiDeFHierarchyGenerator.ATTR_DEC_NAME + '": [{')
        out_stream.write('"nodes": { "' + HiDeFHierarchyGenerator.PERSISTENCE_COL_NAME +
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
        nodefile = os.path.join(outdir, HiDeFHierarchyGenerator.HIDEF_OUT_PREFIX + '.nodes')
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
        edge_file = os.path.join(outdir, HiDeFHierarchyGenerator.HIDEF_OUT_PREFIX + '.edges')
        self.write_communities(out_stream, edge_file, cluster_node_map)
        self.write_persistence_node_attribute(out_stream, persistence_map)
        out_stream.write('\n')
        return None

    def _run_cmd(self, cmd, cwd=None, timeout=3600):
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

    def get_hierarchy(self, networks):
        """
        stability = 10
        maxres = 40
        alg = 'leiden'
        input_networks = ' '.join(cutoff_files)
        g = ' '.join(cutoff_files)
        o = '{}/outputs_run_hidef/{}_cos_sim_layered.chi_{}.maxres_{}.alg_{}'.format(workdir,prefix, stability,maxres, alg)

        %run /cellar/users/lvschaffer/GitClones/HiDeF/hidef/hidef_finder.py --g $g --o $o --alg $alg --maxres $maxres --k $stability

        :return:
        """
        outdir = os.path.dirname(networks[0])

        largest_n_size = 0
        largest_n = None
        for n in networks:
            if os.path.getsize(n + constants.CX_SUFFIX) > largest_n_size:
                largest_n = n

        edgelist_files = [n + '.tsv' for n in networks]

        cmd = [self._hidef_cmd, '--g']
        cmd.extend(edgelist_files)
        cmd.extend(['--o', os.path.join(outdir, HiDeFHierarchyGenerator.HIDEF_OUT_PREFIX),
                    '--alg', 'leiden', '--maxres', '40', '--k', '10',
                    '--skipgml'])

        exit_code, out, err = self._run_cmd(cmd)
        if exit_code != 0:
            logger.error('Cmd failed with exit code: ' + str(exit_code) +
                         ' : ' + str(out) + ' : ' + str(err))

        try:
            cdaps_out_file = os.path.join(outdir, 'cdaps.json')
            with open(cdaps_out_file, 'w') as out_stream:
                self.convert_hidef_output_to_cdaps(out_stream, outdir)

            cd = cdapsutil.CommunityDetection(runner=cdapsutil.ExternalResultsRunner())
            # need to find the largest of the networks passed in
            return cd.run(ndex2.create_nice_cx_from_file(largest_n + constants.CX_SUFFIX), algorithm=cdaps_out_file)

        except FileNotFoundError as fe:
            logger.error('No output from hidef: ' + str(fe) + '\n')
            return None
        return None






