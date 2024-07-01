import logging
from cellmaps_utils.ndexupload import NDExHierarchyUploader as NDExHierarchyUploaderUtil

logger = logging.getLogger(__name__)


class NDExHierarchyUploader(object):
    """
    Base class for uploading hierarchical networks and their parent networks to NDEx.

    Note:
        This class is deprecated and will be removed in a future release.
        Please use `NDExHierarchyUploader` from `cellmaps_utils.ndexupload` instead.

    """

    def __init__(self, ndexserver, ndexuser, ndexpassword, visibility=None):
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
        self._ndex_uploader = NDExHierarchyUploaderUtil(ndexserver, ndexuser, ndexpassword, visibility)

    def get_cytoscape_url(self, ndexurl):
        """
        Generates a Cytoscape URL for a given NDEx network URL.

        :param ndexurl: The URL of the NDEx network.
        :type ndexurl: str
        :return: The URL pointing to the network's view on the Cytoscape platform.
        :rtype: str
        """
        return self._ndex_uploader.get_cytoscape_url(ndexurl)

    def save_hierarchy_and_parent_network(self, hierarchy, parent_ppi):
        """
        Saves both the hierarchy and its parent network to the NDEx server. This method first saves the parent
        network, then updates the hierarchy with HCX annotations based on the parent network's UUID, and
        finally saves the updated hierarchy. It returns the UUIDs and URLs for both the hierarchy and
        the parent network.

        :param hierarchy: The hierarchy network to be saved.
        :type hierarchy: :py:class:`~ndex2.cx2.CX2Network`
        :param parent_ppi: The parent protein-protein interaction network associated with the hierarchy.
        :type parent_ppi: :py:class:`~ndex2.cx2.CX2Network`
        :return: UUIDs and URLs for both the parent network and the hierarchy.
        :rtype: tuple
        """
        return self._ndex_uploader.save_hierarchy_and_parent_network(hierarchy, parent_ppi)

    def upload_hierary_and_parent_network_from_files(self, outdir):
        """
        Uploads hierarchy and parent network to NDEx from CX2 files located in a specified directory.
        It first checks the existence of the hierarchy and parent network files, then loads them into
        network objects, and finally saves them to NDEx using `save_hierarchy_and_parent_network` method.

        :param outdir: The directory where the hierarchy and parent network files are located.
        :type outdir: str
        :return: UUIDs and URLs for both the hierarchy and parent network.
        :rtype: tuple
        :raises CellmapsGenerateHierarchyError: If the required hierarchy or parent network files do not exist
                                                in the directory.
        """
        return self._ndex_uploader.upload_hierarchy_and_parent_network_from_files(outdir)
