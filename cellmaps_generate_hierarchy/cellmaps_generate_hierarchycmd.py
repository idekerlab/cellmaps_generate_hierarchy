#! /usr/bin/env python

import argparse
import sys
import logging
import logging.config
import getpass

from cellmaps_utils import logutils
from cellmaps_utils import constants
from cellmaps_utils.provenance import ProvenanceUtil
import cellmaps_generate_hierarchy
from cellmaps_generate_hierarchy.exceptions import CellmapsGenerateHierarchyError
from cellmaps_generate_hierarchy.hidefconverter import HierarchyToHiDeFConverter
from cellmaps_generate_hierarchy.ndexupload import NDExHierarchyUploader
from cellmaps_generate_hierarchy.ppi import CosineSimilarityPPIGenerator
from cellmaps_generate_hierarchy.hierarchy import CDAPSHiDeFHierarchyGenerator
from cellmaps_generate_hierarchy.maturehierarchy import HiDeFHierarchyRefiner
from cellmaps_generate_hierarchy.runner import CellmapsGenerateHierarchy
from cellmaps_generate_hierarchy.layout import CytoscapeJSBreadthFirstLayout
from cellmaps_generate_hierarchy.hcx import HCXFromCDAPSCXHierarchy

logger = logging.getLogger(__name__)

CO_EMBEDDINGDIRS = '--coembedding_dirs'


def _parse_arguments(desc, args):
    """
    Parses command line arguments

    :param desc: description to display on command line
    :type desc: str
    :param args: command line arguments usually :py:func:`sys.argv[1:]`
    :type args: list
    :return: arguments parsed by :py:mod:`argparse`
    :rtype: :py:class:`argparse.Namespace`
    """
    parser = argparse.ArgumentParser(description=desc,
                                     formatter_class=constants.ArgParseFormatter)
    parser.add_argument('outdir', help='Output directory')
    parser.add_argument(CO_EMBEDDINGDIRS, nargs="+",
                        help='Directories where coembedding was run')
    parser.add_argument('--mode', choices=['run', 'ndexsave', 'convert'], default='run',
                        help='Processing mode. If set to "run" then hierarchy is generated. If '
                             'set to "ndexsave", it is assumes hierarchy has been generated '
                             '(named hierarchy.cx2 and parent_hierarchy.cx2) and '
                             'put in <outdir> passed in via the command line and this tool '
                             'will save the hierarchy to NDEx using --ndexserver, --ndexuser, and '
                             '--ndexpassword credentials. If set to convert, it is assumes hierarchy has been generated'
                             ' (named hierarchy.cx2) and it converts the hierarchy to HiDeF .nodes and .edges files')
    parser.add_argument('--hcx_dir',
                        help='Input directory for convert mode with hierarchy in hcx to be converted to HiDeF .nodes '
                             'and .edges files')
    parser.add_argument('--name',
                        help='Name of this run, needed for FAIRSCAPE. If '
                             'unset, name value from specified '
                             'by --coembedding_dir directory will be used')
    parser.add_argument('--organization_name',
                        help='Name of organization running this tool, needed '
                             'for FAIRSCAPE. If unset, organization name specified '
                             'in --coembedding_dir directory will be used')
    parser.add_argument('--project_name',
                        help='Name of project running this tool, needed for '
                             'FAIRSCAPE. If unset, project name specified '
                             'in --coembedding_dir directory will be used')
    parser.add_argument('--k', default=10,
                        help='HiDeF stability parameter')
    parser.add_argument('--algorithm', default='leiden',
                        help='HiDeF clustering algorithm parameter')
    parser.add_argument('--maxres', default=80,
                        help='HiDeF max resolution parameter')
    parser.add_argument('--stability', default=0.,
                        help='Containment index threshold for pruning hierarchy')
    parser.add_argument('--containment_threshold', default=0.75,
                        help='Containment index threshold for pruning hierarchy')
    parser.add_argument('--jaccard_threshold', default=0.9,
                        help='Jaccard index threshold for merging similar clusters')
    parser.add_argument('--min_diff', default=1,
                        help='Minimum difference in number of proteins for every '
                             'parent-child pair')
    parser.add_argument('--min_system_size', default=4,
                        help='Minimum number of proteins each system must have to be kept')
    parser.add_argument('--ppi_cutoffs', nargs='+', type=float,
                        default=[0.001, 0.002, 0.003, 0.004, 0.005, 0.006,
                                 0.007, 0.008, 0.009, 0.01, 0.02, 0.03,
                                 0.04, 0.05, 0.10],
                        help='Cutoffs used to generate PPI input networks. For example, '
                             'a value of 0.1 means to generate PPI input network using the '
                             'top ten percent of coembedding entries. Each cutoff generates '
                             'another PPI network')
    parser.add_argument('--hierarchy_parent_cutoff', default=0.1,
                        help='PPI network cutoff to be chosen as hierarchy parent network.')
    parser.add_argument('--skip_layout', action='store_true',
                        help='If set, skips layout of hierarchy step')
    parser.add_argument('--ndexserver', default='ndexbio.org',
                        help='Server where hierarchy can be converted to HCX and saved')
    parser.add_argument('--ndexuser',
                        help='NDEx user account')
    parser.add_argument('--ndexpassword',
                        help='NDEx password. Enter "-" to input password interactively, '
                             'or provide a file containing the password. Leave blank to not use a password.')
    parser.add_argument('--visibility', action='store_true',
                        help='If set, makes Hierarchy and interactome network loaded onto '
                             'NDEx publicly visible')
    parser.add_argument('--keep_intermediate_files', action='store_true',
                        help='If set, ppi network cx files will be saved.')
    parser.add_argument('--gene_node_attributes', nargs="+",
                        help='Accepts ro-crates that are output of imagedownloader or ppidownloader, '
                             'or tsv files with gene node attributes')
    parser.add_argument('--skip_logging', action='store_true',
                        help='If set, output.log, error.log '
                             'files will not be created')
    parser.add_argument('--logconf', default=None,
                        help='Path to python logging configuration file in '
                             'this format: https://docs.python.org/3/library/'
                             'logging.config.html#logging-config-fileformat '
                             'Setting this overrides -v parameter which uses '
                             ' default logger. (default None)')
    parser.add_argument('--verbose', '-v', action='count', default=1,
                        help='Increases verbosity of logger to standard '
                             'error for log messages in this module. Messages are '
                             'output at these python logging levels '
                             '-v = WARNING, -vv = INFO, '
                             '-vvv = DEBUG, -vvvv = NOTSET (default ERROR '
                             'logging)')
    parser.add_argument('--version', action='version',
                        version=('%(prog)s ' +
                                 cellmaps_generate_hierarchy.__version__))

    return parser.parse_args(args)


def main(args):
    """
    Main entry point for program

    :param args: arguments passed to command line usually :py:func:`sys.argv[1:]`
    :type args: list

    :return: return value of :py:meth:`cellmaps_generate_hierarchy.runner.CellmapsGenerateHierarchy.run`
             or ``2`` if an exception is raised
    :rtype: int
    """
    desc = """
    Version {version}

    Takes a list of coembedding file {coembedding_file} files from {coembedding_dirs} directories
    (corresponding to multiple folds of the same data) that is in TSV format and generates several interaction networks
    that are fed via -g flag to HiDeF to create a hierarchy.

    Format of {coembedding_file} where 1st line is header:

    ''\t1\t2\t3\t4\t5...1024
    GENESYMBOL\tEMBEDDING1\tEMBEDDING2...

    Example:

            1       2       3       4       5
    AAAS    -0.35026753     -0.1307554      -0.046265163    0.3758623       0.22126552

    """.format(version=cellmaps_generate_hierarchy.__version__,
               coembedding_file=constants.CO_EMBEDDING_FILE,
               coembedding_dirs=', '.join(CO_EMBEDDINGDIRS))
    theargs = _parse_arguments(desc, args[1:])
    theargs.program = args[0]
    theargs.version = cellmaps_generate_hierarchy.__version__

    try:
        logutils.setup_cmd_logging(theargs)
        if theargs.ndexpassword == '-':
            theargs.ndexpassword = getpass.getpass(prompt="Enter NDEx Password: ")
        if theargs.mode == 'ndexsave':
            ndex_uploader = NDExHierarchyUploader(theargs.ndexserver, theargs.ndexuser, theargs.ndexpassword,
                                                  theargs.visibility)
            _, _, _, hierarchyurl = ndex_uploader.upload_hierary_and_parent_network_from_files(theargs.outdir)
            print(f'Hierarchy uploaded. To view hierarchy on NDEx please paste this URL in your '
                  f'browser {hierarchyurl}. To view Hierarchy on new experimental Cytoscape on the Web, go to '
                  f'{ndex_uploader.get_cytoscape_url(hierarchyurl)}')
            return 0
        if theargs.mode == 'convert':
            hcx_dir = theargs.hcx_dir if theargs.hcx_dir else theargs.outdir
            hidef_converter = HierarchyToHiDeFConverter(hcx_dir, theargs.outdir)
            return hidef_converter.generate_hidef_files()

        if theargs.coembedding_dirs is None:
            raise CellmapsGenerateHierarchyError('In run mode, coembedding_dirs parameter is required.')

        provenance = ProvenanceUtil()
        ppigen = CosineSimilarityPPIGenerator(embeddingdirs=theargs.coembedding_dirs,
                                              cutoffs=theargs.ppi_cutoffs)

        refiner = HiDeFHierarchyRefiner(ci_thre=theargs.containment_threshold,
                                        ji_thre=theargs.jaccard_threshold,
                                        min_term_size=theargs.min_system_size,
                                        min_diff=theargs.min_diff,
                                        provenance_utils=provenance)

        converter = HCXFromCDAPSCXHierarchy()

        hiergen = CDAPSHiDeFHierarchyGenerator(author='cellmaps_generate_hierarchy',
                                               refiner=refiner,
                                               hcxconverter=converter,
                                               hierarchy_parent_cutoff=float(theargs.hierarchy_parent_cutoff),
                                               version=cellmaps_generate_hierarchy.__version__,
                                               provenance_utils=provenance)
        if theargs.skip_layout is True:
            layoutalgo = None
        else:
            layoutalgo = CytoscapeJSBreadthFirstLayout()

        # we dont want to log the password anywhere so toss it from the dict
        input_data_dict = theargs.__dict__.copy()
        if 'ndexpassword' in input_data_dict:
            input_data_dict['ndexpassword'] = 'PASSWORD REMOVED FOR SECURITY REASONS'

        return CellmapsGenerateHierarchy(outdir=theargs.outdir,
                                         inputdirs=theargs.coembedding_dirs,
                                         ppigen=ppigen,
                                         algorithm=theargs.algorithm,
                                         maxres=theargs.maxres,
                                         k=theargs.k,
                                         gene_node_attributes=theargs.gene_node_attributes,
                                         hiergen=hiergen,
                                         name=theargs.name,
                                         project_name=theargs.project_name,
                                         organization_name=theargs.organization_name,
                                         layoutalgo=layoutalgo,
                                         skip_logging=theargs.skip_logging,
                                         input_data_dict=input_data_dict,
                                         provenance_utils=provenance,
                                         ndexserver=theargs.ndexserver,
                                         ndexuser=theargs.ndexuser,
                                         ndexpassword=theargs.ndexpassword,
                                         visibility=theargs.visibility,
                                         keep_intermediate_files=theargs.keep_intermediate_files
                                         ).run()
    except Exception as e:
        logger.exception('Caught exception: ' + str(e))
        return 2
    finally:
        logging.shutdown()


if __name__ == '__main__':  # pragma: no cover
    sys.exit(main(sys.argv))
