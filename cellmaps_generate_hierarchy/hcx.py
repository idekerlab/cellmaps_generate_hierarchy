
import logging
import ndex2

from cellmaps_generate_hierarchy.exceptions import CellmapsGenerateHierarchyError

logger = logging.getLogger(__name__)


class HCXFromCDAPSCXHierarchy(object):
    """
    Converts CDAPS Hierarchy (and parent network/interactome)
    into HCX hierarchy and CX2 respectively.
    """

    def __init__(self, ndexserver=None,
                 ndexuser=None,
                 ndexpassword=None):
        """
        Constructor
        """
        pass

    def get_converted_hierarchy(self, hierarchy=None, parent_network=None):
        """
        Converts hierarchy in CX CDAPS format into HCX format and parent network
        from CX format into CX2 format

        For the parent interactome simply upload the network to NDEx and also use the
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
        returned.

        The 3rd, 4th elements returned are the user viewable URLs of the hierarchy and
        parent networks put onto NDEx

        :param hierarchy: Hierarchy network
        :type hierarchy: :py:class:`~ndex2.nice_cx_network.NiceCXNetwork`
        :param parent_network: Parent network
        :type parent_network: :py:class:`~ndex2.nice_cx_network.NiceCXNetwork`
        :return: (hierarchy as :py:class:`list`,
                  parent ppi as :py:class:`list`, hierarchyurl, parenturl)
        :rtype: tuple
        """
        return None, None, None, None
