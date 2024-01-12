import logging
import os
from ndex2.cx2 import RawCX2NetworkFactory
import ndex2.constants as constants
import cellmaps_utils.constants as cellmaps_constants

from cellmaps_generate_hierarchy.exceptions import CellmapsGenerateHierarchyError

logger = logging.getLogger(__name__)


class HierarchyToHiDeFConverter:
    HIDEF_OUT_PREFIX = 'hidef_output_gene_names'

    def __init__(self, directory):
        self.directory = directory
        self.hierarchy_path = os.path.join(directory,
                                           cellmaps_constants.HIERARCHY_NETWORK_PREFIX + cellmaps_constants.CX2_SUFFIX)
        try:
            factory = RawCX2NetworkFactory()
            self.hierarchy = factory.get_cx2network(self.hierarchy_path)
        except Exception as e:
            logger.error(f"Failed to load hierarchy: {e}")
            raise CellmapsGenerateHierarchyError(f"Failed to load hierarchy: {e}")

    def generate_hidef_files(self):
        try:
            nodes = self.hierarchy.get_nodes()
            edges = self.hierarchy.get_edges()
            formatted_nodes = self._format_aspect(nodes, self._format_node)
            formatted_edges = self._format_aspect(edges, self._format_edge)
            self._write_to_file(HierarchyToHiDeFConverter.HIDEF_OUT_PREFIX + '.nodes', formatted_nodes)
            self._write_to_file(HierarchyToHiDeFConverter.HIDEF_OUT_PREFIX + '.edges', formatted_edges)
        except Exception as e:
            logger.error(f"Error during HiDeF generation: {e}")
            raise

    @staticmethod
    def _format_aspect(aspect, format_function):
        return [format_function(aspect_id) for aspect_id in aspect]

    def _format_node(self, node_id):
        node = self.hierarchy.get_node(node_id)
        node_attr = node[constants.ASPECT_VALUES]
        formatted_node = (node_attr['name'], node_attr['CD_MemberList_Size'],
                          node_attr['CD_MemberList'], node_attr['HiDeF_persistence'])
        return "\t".join(map(str, formatted_node))

    def _format_edge(self, edge_id):
        edge = self.hierarchy.get_edge(edge_id)
        source_node = self._find_node_name_by_id(edge[constants.EDGE_SOURCE])
        target_node = self._find_node_name_by_id(edge[constants.EDGE_TARGET])
        return f"{source_node}\t{target_node}\tdefault"

    def _find_node_name_by_id(self, node_id):
        node = self.hierarchy.get_node(node_id)
        return node[constants.ASPECT_VALUES]['name']

    def _write_to_file(self, filename, lines):
        file_path = os.path.join(self.directory, filename)
        with open(file_path, 'w') as file:
            file.write('\n'.join(lines))
