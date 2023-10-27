import logging
import ndex2
import os

from cellmaps_generate_hierarchy.exceptions import CellmapsGenerateHierarchyError
import cellmaps_generate_hierarchy
from ndex2.cx2 import NoStyleCXToCX2NetworkFactory, RawCX2NetworkFactory

logger = logging.getLogger(__name__)


class HCXFromCDAPSCXHierarchy(object):
    """
    Converts CDAPS Hierarchy (and parent network/interactome)
    into HCX hierarchy and CX2 respectively.
    """

    VISUAL_EDITOR_PROPERTIES_ASPECT = 'visualEditorProperties'

    def __init__(self):
        """
        Constructor
        """
        pass

    def _get_root_nodes(self, hierarchy):
        """
        In CDAPS the root node has only source edges to children
        so this function counts up number of target edges for each node
        and the one with 0 is the root

        :param hierarchy:
        :type hierarchy: :py:class:`~ndex2.nice_cx_network.NiceCXNetwork`
        :return: root node ids
        :rtype: set
        """
        all_nodes = set()
        for node_id, node_obj in hierarchy.get_nodes():
            all_nodes.add(node_id)

        nodes_with_targets = set()
        for edge_id, edge_obj in hierarchy.get_edges():
            nodes_with_targets.add(edge_obj['t'])
        return all_nodes.difference(nodes_with_targets)

    def _add_isroot_node_attribute(self, hierarchy, root_nodes=None):
        """
        Using the **root_nodes** set or list, add
        ``HCX::isRoot`` to
        every node setting value to ``True``
        if node id is in **root_nodes**
        otherwise set the value to ``False``

        :param hierarchy:
        :type hierarchy: :py:class:`~ndex2.nice_cx_network.NiceCXNetwork`
        """
        attr_name = 'HCX::isRoot'
        for node_id, node_obj in hierarchy.get_nodes():
            if node_id in root_nodes:
                hierarchy.set_node_attribute(node_id, attr_name,
                                             values='true',
                                             type='boolean',
                                             overwrite=True)
            else:
                hierarchy.set_node_attribute(node_id, attr_name,
                                             values='false',
                                             type='boolean',
                                             overwrite=True)

    def _add_hierarchy_network_attributes(self, hierarchy, interactome_name=None):
        """

        :param hierarchy:
        :param interactome_name:
        :return:
        """
        hierarchy.set_network_attribute('ndexSchema', values='hierarchy_v0.1',
                                        type='string')
        hierarchy.set_network_attribute('HCX::modelFileCount',
                                        values='2',
                                        type='integer')
        hierarchy.set_network_attribute('HCX::interactionNetworkName',
                                        values=interactome_name,
                                        type='string')

    def _get_mapping_of_node_names_to_ids(self, network):
        """
        Gets a mapping of node names to node ids

        :param network:
        :type network:
        :return: :py:class:`~ndex2.nice_cx_network.NiceCXNetwork`
        """
        node_map = {}
        for node_id, node_obj in network.get_nodes():
            node_map[node_obj['n']] = node_id
        return node_map

    def _add_members_node_attribute(self, hierarchy,
                                    interactome_name_map=None,
                                    memberlist_attr_name='CD_MemberList'):
        """
        Updates the nodes in the given hierarchy by adding a 'HCX::members' attribute. This attribute is
        derived from the member list associated with each node, and it maps members to their corresponding
        IDs from the `interactome_name_map`.

        :param hierarchy: The network hierarchy that needs to be updated with the 'HCX::members' attribute.
        :type hierarchy: :py:class:`~ndex2.nice_cx_network.NiceCXNetwork`
        :param interactome_name_map: A dictionary mapping member names to their corresponding IDs in the interactome.
                                     If not provided, an error will be raised.
        :type interactome_name_map: dict or None, default: None
        :param memberlist_attr_name: The name of the node attribute which contains the list of members associated
                                     with each node in the hierarchy.
        :type memberlist_attr_name: str, default: 'CD_MemberList'
        :raises CellmapsGenerateHierarchyError: If `interactome_name_map` is None.
        :return:
        """
        if interactome_name_map is None:
            raise CellmapsGenerateHierarchyError('interactome name map is None')

        for node_id, node_obj in hierarchy.get_nodes():
            memberlist = hierarchy.get_node_attribute(node_id,
                                                      memberlist_attr_name)
            if memberlist is None or memberlist == (None, None):
                logger.warning('no memberlist for node')
                continue
            member_ids = set()
            for member in memberlist['v'].split(' '):
                if member in interactome_name_map:
                    member_ids.add(str(interactome_name_map[member]))
                else:
                    logger.warning(member + ' not in interactome. Skipping')

            hierarchy.set_node_attribute(node_id, 'HCX::members',
                                         values=list(member_ids), type='list_of_long',
                                         overwrite=True)

    def _get_visual_editor_properties_aspect_from_network(self, network=None):
        """
        Gets ``visualEditorProperties`` aspect from **network**
        :param network:
        :type network: :py:class:`ndex2.cx2.CX2Network`
        :return: `visualEditorProperties`` aspect or ``None`` if not found
        :rtype: dict
        """
        for aspect in network.get_opaque_aspects():
            if HCXFromCDAPSCXHierarchy.VISUAL_EDITOR_PROPERTIES_ASPECT in aspect:
                return aspect
        return None

    def _get_style_from_network(self, path_to_style_network):
        """
        Retrieves the style network from a given file and fetches the
        `visualEditorProperties` aspect associated with that network.

        :param path_to_style_network: The path to the style network file.
        :type path_to_style_network: str
        :return: A tuple containing the style network and its associated
                 `visualEditorProperties` aspect.
        :rtype: tuple(:py:class:`ndex2.cx2.CX2Network`, dict or None)
        """
        rawcx2_factory = RawCX2NetworkFactory()
        style_network = rawcx2_factory.get_cx2network(path_to_style_network)
        visual_editor_props = self._get_visual_editor_properties_aspect_from_network(style_network)
        return style_network, visual_editor_props

    def _convert_and_style_network(self, network, style_filename):
        """
        Converts the given network into the CX2 format and applies the specified style.

        :param network: The network to be converted and styled.
        :type network: :py:class:`~ndex2.nice_cx_network.NiceCXNetwork`
        :param style_filename: The filename of the style to be applied.
        :type style_filename: str
        :return: The converted and styled network.
        :rtype: :py:class:`ndex2.cx2.CX2Network`
        """
        cx_factory = NoStyleCXToCX2NetworkFactory()
        converted_network = cx_factory.get_cx2network(network)
        path_to_style_network = os.path.join(os.path.dirname(cellmaps_generate_hierarchy.__file__), style_filename)
        style_network, visual_editor_props = self._get_style_from_network(path_to_style_network)
        converted_network.set_visual_properties(style_network.get_visual_properties())

        if visual_editor_props is not None:
            converted_network.add_opaque_aspect(visual_editor_props)

        return converted_network

    def _add_hcx_attributes_to_hierarchy(self, hierarchy, parent_network):
        """
        Updates the provided hierarchy with HCX attributes. These attributes applied to
        network structure, root nodes, and member nodes.

        :param hierarchy: The network hierarchy that needs to be updated with the HCX attributes.
        :type hierarchy: :py:class:`~ndex2.nice_cx_network.NiceCXNetwork`
        :param parent_network: The parent network.
        :type parent_network: :py:class:`~ndex2.nice_cx_network.NiceCXNetwork`
        :return: The updated hierarchy with the added HCX attributes.
        :rtype: :py:class:`~ndex2.nice_cx_network.NiceCXNetwork`
        """
        # TODO: interactome name should be set earlier and passed to the function (not hardcoded)
        self._add_hierarchy_network_attributes(hierarchy, interactome_name="hierarchy_parent.cx2")

        root_nodes = self._get_root_nodes(hierarchy)

        self._add_isroot_node_attribute(hierarchy, root_nodes=root_nodes)

        # get mapping of node names to node ids
        interactome_name_map = self._get_mapping_of_node_names_to_ids(parent_network)

        self._add_members_node_attribute(hierarchy,
                                         interactome_name_map=interactome_name_map)
        return hierarchy

    def get_converted_hierarchy(self, hierarchy=None, parent_network=None):
        """
        Converts hierarchy in CX CDAPS format into HCX format and parent network
        from CX format into CX2 format

        For the parent network aka interactome, it translates it from cx to cx2 using
        `~ndex2.cx2.NoStyleCXToCX2NetworkFactory` class.

        This transformation is done by first annotating the hierarchy network
        with needed HCX annotations, namely going with filesystem based HCX format
        where the network attribute: ``HCX::interactionNetworkName`` is set to filename of parent ppi.

        For necessary annotations see: https://cytoscape.org/cx/cx2/hcx-specification/
        and for code implementing these annotations see:
        https://github.com/idekerlab/hiviewutils/blob/main/hiviewutils/hackedhcx.py

        Once the hierarchy is annotated, it translates it from cx to cx2
        using `~ndex2.cx2.NoStyleCXToCX2NetworkFactory` class.

        :param hierarchy: Hierarchy network
        :type hierarchy: :py:class:`~ndex2.nice_cx_network.NiceCXNetwork`
        :param parent_network: Parent network
        :type parent_network: :py:class:`~ndex2.nice_cx_network.NiceCXNetwork`
        :return: (hierarchy as :py:class:`~ndex2.cx2.CX2Network`,
                  parent ppi as :py:class:`~ndex2.cx2.CX2Network`)
        :rtype: tuple
        """
        parent_network_cx2 = self._convert_and_style_network(parent_network, 'interactome_style.cx2')
        hierarchy_with_hcx_attributes = self._add_hcx_attributes_to_hierarchy(hierarchy, parent_network)
        hierarchy_hcx = self._convert_and_style_network(hierarchy_with_hcx_attributes, 'hierarchy_style.cx2')

        return hierarchy_hcx, parent_network_cx2
