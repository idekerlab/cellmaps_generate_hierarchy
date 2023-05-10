#! /usr/bin/env python

import argparse
import sys
import logging
import logging.config

from cellmaps_utils import logutils
from cellmaps_utils import constants
import cellmaps_generate_hierarchy
from cellmaps_generate_hierarchy.ppi import CosineSimilarityPPIGenerator
from cellmaps_generate_hierarchy.hierarchy import CDAPSHierarchyGenerator
from cellmaps_generate_hierarchy.runner import CellmapsGenerateHierarchy

logger = logging.getLogger(__name__)


class Formatter(argparse.ArgumentDefaultsHelpFormatter,
                argparse.RawDescriptionHelpFormatter):
    """
    Combine two Formatters to get help and default values
    displayed when showing help

    """
    pass


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
    parser.add_argument('--coembedding_dir',
                        help='Directory where coembedding was run')
    parser.add_argument('--name',
                        help='Name of this run, needed for FAIRSCAPE. If '
                             'unset, name value from specified '
                             'by --inputdir directory will be used')
    parser.add_argument('--organization_name',
                        help='Name of organization running this tool, needed '
                             'for FAIRSCAPE. If unset, organization name specified '
                             'in --inputdir directory will be used')
    parser.add_argument('--project_name',
                        help='Name of project running this tool, needed for '
                             'FAIRSCAPE. If unset, project name specified '
                             'in --input directory will be used')
    parser.add_argument('--logconf', default=None,
                        help='Path to python logging configuration file in '
                             'this format: https://docs.python.org/3/library/'
                             'logging.config.html#logging-config-fileformat '
                             'Setting this overrides -v parameter which uses '
                             ' default logger. (default None)')
    parser.add_argument('--exitcode', help='Exit code this command will return',
                        default=0, type=int)
    parser.add_argument('--verbose', '-v', action='count', default=0,
                        help='Increases verbosity of logger to standard '
                             'error for log messages in this module. Messages are '
                             'output at these python logging levels '
                             '-v = ERROR, -vv = WARNING, -vvv = INFO, '
                             '-vvvv = DEBUG, -vvvvv = NOTSET (default no '
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

    Invokes run() method on CellmapsGenerateHierarchy

    """.format(version=cellmaps_generate_hierarchy.__version__)
    theargs = _parse_arguments(desc, args[1:])
    theargs.program = args[0]
    theargs.version = cellmaps_generate_hierarchy.__version__

    try:
        logutils.setup_cmd_logging(theargs)

        ppigen = CosineSimilarityPPIGenerator(embeddingfile=theargs.coembedding_dir)

        hiergen = CDAPSHierarchyGenerator()
        return CellmapsGenerateHierarchy(outdir=theargs.outdir,
                                         ppigen=ppigen,
                                         hiergen=hiergen,
                                         input_data_dict=theargs.__dict__).run()
    except Exception as e:
        logger.exception('Caught exception: ' + str(e))
        return 2
    finally:
        logging.shutdown()


if __name__ == '__main__':  # pragma: no cover
    sys.exit(main(sys.argv))
