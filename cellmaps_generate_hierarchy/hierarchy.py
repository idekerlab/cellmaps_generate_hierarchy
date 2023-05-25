
import os
import logging
import subprocess
from datetime import date
import ndex2
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
    def __init__(self, hidef_cmd='hidef_finder.py'):
        """
        Constructor
        """
        super().__init__()
        self._hidef_cmd = hidef_cmd

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

        edgelist_files = [n + '.tsv' for n in networks]

        cmd = [self._hidef_cmd, '--g']
        cmd.extend(edgelist_files)
        cmd.extend(['--o', os.path.join(outdir, 'hidef_output'),
                    '--alg', 'leiden', '--maxres', '40', '--k', '10',
                    '--skipgml'])

        exit_code, out, err = self._run_cmd(cmd)
        if exit_code != 0:
            logger.error('Cmd failed with exit code: ' + str(exit_code) +
                         ' : ' + str(out) + ' : ' + str(err))

        return ndex2.nice_cx_network.NiceCXNetwork()






