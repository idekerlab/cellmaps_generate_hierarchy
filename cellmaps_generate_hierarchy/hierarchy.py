
import cdapsutil


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

    def get_hierarchy(self):
        """
        Gets hierarchy

        # Todo: flip return object to HCX object

        :return:
        :rtype: :py:class:`ndex2.nice_cx_network.NiceCXNetwork`
        """
        raise NotImplementedError('Subclasses need to implement')


class CDAPSHierarchyGenerator(CXHierarchyGenerator):
    """
    Generates hierarchy using CDAPS
    """
    def __init__(self):
        """
        Constructor
        """
        super().__init__()

    def get_hierarchy(self, network):
        """

        :return:
        """
        cd = cdapsutil.CommunityDetection(runner=cdapsutil.ServiceRunner())
        return cd.run_community_detection(network,
                                          algorithm='hidef')






