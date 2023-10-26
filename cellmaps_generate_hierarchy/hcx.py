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

    def __init__(self, ndexserver=None,
                 ndexuser=None,
                 ndexpassword=None,
                 visibility=None):
        """
        Constructor

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
        self._server = ndexserver
        self._user = ndexuser
        if ndexpassword is not None and os.path.isfile(ndexpassword):
            with open(ndexpassword, 'r') as file:
                self._password = file.readline().strip()
        else:
            self._password = ndexpassword
        self._visibility = None
        if visibility is not None:
            if isinstance(visibility, bool):
                if visibility is True:
                    self._visibility = 'PUBLIC'
            elif isinstance(visibility, str):
                if visibility.lower() == 'public':
                    self._visibility = 'PUBLIC'
        self._ndexclient = None
        self._initialize_ndex_client()

    def _set_ndex_client(self, client):
        """
        Sets alternate NDEx client
        """
        self._ndexclient = client

    def _initialize_ndex_client(self):
        """
        Creates NDEx client
        :return:
        """
        logger.debug('Connecting to NDEx server: ' + str(self._server) +
                     ' with user: ' + str(self._user))
        self._ndexclient = ndex2.client.Ndex2(host=self._server,
                                              username=self._user,
                                              password=self._password,
                                              skip_version_check=True)

    def _save_network(self, network):
        """

        :param network: Network to save
        :type network: :py:class:`~ndex2.cx2.CX2Network`
        :return: NDEX UUID of network
        :rtype: str
        """
        logger.debug('Saving network named: ' + str(network.get_name()) +
                     ' to NDEx with visibility set to: ' + str(self._visibility))
        try:
            res = self._ndexclient.save_new_cx2_network(network.to_cx2(),
                                                        visibility=self._visibility)
        except Exception as e:
            raise CellmapsGenerateHierarchyError('An error occurred while saving the network to NDEx: ' + str(e))

        if not isinstance(res, str):
            raise CellmapsGenerateHierarchyError('Expected a str, but got this: ' + str(res))

        ndexuuid = res[res.rfind('/') + 1:]
        return ndexuuid

    def _delete_network(self, network_id):
        self._ndexclient.delete_network(network_id)

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

    def _add_hierarchy_network_attributes(self, hierarchy, interactome_id=None, interactome_name=None):
        """

        :param hierarchy:
        :param interactome_id:
        :return:
        """
        hierarchy.set_network_attribute('ndexSchema', values='hierarchy_v0.1',
                                        type='string')
        hierarchy.set_network_attribute('HCX::modelFileCount',
                                        values='2',
                                        type='integer')
        if interactome_name is not None:
            hierarchy.set_network_attribute('HCX::interactionNetworkName',
                                            values=interactome_name,
                                            type='string')
        elif interactome_id is not None:
            hierarchy.set_network_attribute('HCX::interactionNetworkUUID',
                                            values=interactome_id,
                                            type='string')
            if self._server is None:
                server = 'www.ndexbio.org'
            else:
                server = self._server
            hierarchy.set_network_attribute('HCX::interactionNetworkHost',
                                            values=server,
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

        :param hierarchy:
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

    def _generate_url(self, uuid):
        return 'https://' + self._server + '/cytoscape/network/' + str(uuid)

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

    def get_converted_hierarchy(self, hierarchy=None, parent_network=None):
        """
        Converts hierarchy in CX CDAPS format into HCX format and parent network
        from CX format into CX2 format

        For the parent network aka interactome simply upload the network to NDEx and also use the
        python client to get CX2 as a list object via json load and set that as 2nd element
        in tuple returned

        This transformation is done by first annotating the hierarchy network
        with needed HCX annotations, namely going with filesystem based HCX format
        where the network attribute: ``HCX::interactionNetworkUUID`` is set to UUID of network
        uploaded to NDEx.

        For necessary annotations see: https://cytoscape.org/cx/cx2/hcx-specification/

        and for code implementing these annotations see:
        https://github.com/idekerlab/hiviewutils/blob/main/hiviewutils/hackedhcx.py

        Once the hierarchy is annotated upload it to NDEx and then use the python client
        to get CX2 as a list object via json load and set that as 1st element in tuple
        returned. Uploading networks to NDEx returns a URL that can be parsed to get UUID of
        the networks

        The 3rd, 4th elements returned should be the user viewable URLs of the hierarchy
        and parent networks put onto NDEx

        :param hierarchy: Hierarchy network
        :type hierarchy: :py:class:`~ndex2.nice_cx_network.NiceCXNetwork`
        :param parent_network: Parent network
        :type parent_network: :py:class:`~ndex2.nice_cx_network.NiceCXNetwork`
        :return: (hierarchy as :py:class:`list`,
                  parent ppi as :py:class:`list`, hierarchyurl, parenturl)
        :rtype: tuple
        """
        hierarchy_url = None
        interactome_url = None

        cx_factory = NoStyleCXToCX2NetworkFactory()
        parent_network_cx2 = cx_factory.get_cx2network(parent_network)

        rawcx2_factory = RawCX2NetworkFactory()
        path_to_style_network = os.path.join(os.path.dirname(cellmaps_generate_hierarchy.__file__),
                                             'interactome_style.cx2')
        style_network = rawcx2_factory.get_cx2network(path_to_style_network)
        parent_network_cx2.set_visual_properties(style_network.get_visual_properties())

        visual_editor_props = self._get_visual_editor_properties_aspect_from_network(style_network)
        if visual_editor_props is not None:
            parent_network_cx2.add_opaque_aspect(visual_editor_props)

        if self._server is not None and self._user is not None and self._password is not None:
            interactome_id = self._save_network(parent_network_cx2)
            interactome_url = self._generate_url(interactome_id)
            self._add_hierarchy_network_attributes(hierarchy,
                                                   interactome_id=interactome_id)
        else:
            # TODO: interactome name should be set earlier and passed to the function (not hardcoded)
            self._add_hierarchy_network_attributes(hierarchy,
                                                   interactome_name="hierarchy_parent.cx2")

        root_nodes = self._get_root_nodes(hierarchy)

        self._add_isroot_node_attribute(hierarchy, root_nodes=root_nodes)

        # get mapping of node names to node ids
        interactome_name_map = self._get_mapping_of_node_names_to_ids(parent_network)

        self._add_members_node_attribute(hierarchy,
                                         interactome_name_map=interactome_name_map)

        hierarchy_hcx = cx_factory.get_cx2network(hierarchy)
        path_to_style_network = os.path.join(os.path.dirname(cellmaps_generate_hierarchy.__file__),
                                             'hierarchy_style.cx2')
        style_network = rawcx2_factory.get_cx2network(path_to_style_network)
        hierarchy_hcx.set_visual_properties(style_network.get_visual_properties())

        visual_editor_props = self._get_visual_editor_properties_aspect_from_network(style_network)
        if visual_editor_props is not None:
            hierarchy_hcx.add_opaque_aspect(visual_editor_props)

        if self._server is not None and self._user is not None and self._password is not None:
            hierarchy_id = self._save_network(hierarchy_hcx)
            hierarchy_url = self._generate_url(hierarchy_id)

        return hierarchy_hcx.to_cx2(), parent_network_cx2.to_cx2(), hierarchy_url, interactome_url
