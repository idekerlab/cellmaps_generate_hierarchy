
import logging
import requests
import time
import ndex2
from cellmaps_generate_hierarchy.exceptions import CellmapsGenerateHierarchyError
logger = logging.getLogger(__name__)


class HierarchyLayout(object):
    """
    Base class for layout algorithms
    """
    def __init__(self):
        """
        Constructor
        """
        pass

    def add_layout(self, network=None):
        """
        Adds layout to network passed in.
        Subclasses should implement

        :param network:
        :type network: :py:class:`~ndex2.nice_cx_network.NiceCXNetwork`
        :raises NotImplementedError: Always raised
        """
        raise NotImplementedError('Subclasses should implement')


class CytoscapeJSBreadthFirstLayout(HierarchyLayout):
    """
    Runs breadthfirst layout from http://cytolayouts.ucsd.edu/cd
    to get a layout
    """

    HEADERS = {'Content-Type': 'application/json',
               'Accept': 'application/json'}

    def __init__(self, layout_algorithm='breadthfirst',
                 rest_endpoint='http://cytolayouts.ucsd.edu/cd/communitydetection/v1',
                 retry_sleep_time=1,
                 request_timeout=120):
        """
        Constructor

        :param layout_algorithm: can be one of the following:
                                 circle|cose|grid|concentric|breadthfirst|dagre
        :type layout_algorithm: str
        :param rest_endpoint: URL for rest service
        :type request_timeout: str
        :param retry_sleep_time: time in seconds to wait before checking status
                                 with REST service on status of task
        :type retry_sleep_time: int or float
        :param request_timeout: timeout in seconds to pass to :py:mod:`requests`
                                library for web requests
        :type request_timeout: int or float
        """
        self._layout_algorithm = layout_algorithm
        self._rest_endpoint = rest_endpoint
        self._retry_sleep_time = retry_sleep_time
        self._request_timeout = request_timeout

    def add_layout(self, network=None,
                   timeout=1800):
        """
        Runs algorithm specified in constructor on **network**
        in place

        :param network: Hierarchy network
        :type network: :py:class:`~ndex2.nice_cx_network.NiceCXNetwork`
        :param timeout: time in seconds to wait for task to finish before
                        failing
        :type timeout: int or float
        """
        res = requests.post(self._rest_endpoint,
                            headers=CytoscapeJSBreadthFirstLayout.HEADERS,
                            json={'algorithm': 'cytojslayout',
                                  'customParameters': {'--layout': self._layout_algorithm},
                                  'data': network.to_cx()},
                            timeout=self._request_timeout)

        task_id = self._wait_for_task(res, timeout=timeout)

        res = requests.get(self._rest_endpoint + '/' + str(task_id),
                           headers=CytoscapeJSBreadthFirstLayout.HEADERS)

        if res.status_code != 200:
            raise CellmapsGenerateHierarchyError('Error getting layout results')

        network.set_opaque_aspect('cartesianLayout', res.json()['result'])

    def _get_task_status(self, task_id, start_time=None,
                         timeout=None):
        """
        Gets status of task

        :param task_id: id of task
        :type task_id: str
        :return: response
        :rtype: :py:class:`requests.Response`
        """
        logger.debug('Checking status of task: ' + str(task_id))
        res = requests.get(self._rest_endpoint + '/' +
                           str(task_id) + '/status',
                           headers=CytoscapeJSBreadthFirstLayout.HEADERS)
        if res.status_code != 200:
            logger.debug('Request came back with error, '
                         'sleeping ' + str(self._retry_sleep_time) +
                         ' second(s) and trying again : ' +
                         str(res.text))
            if (int(time.time()) - start_time) > timeout:
                raise CellmapsGenerateHierarchyError('Layout task exceeded timeout of ' +
                                                     str(timeout) + ' seconds')
            time.sleep(self._retry_sleep_time)
            return None
        return res

    def _get_id_from_response(self, res):
        """
        Extracts id of task from json response

        :param res: response from post to layout service
        :type res: :py:class`requests.Response`
        :raises CellmapsGenerateHierarchyError: If there is an error trying
                                                to get id from response
        :return: id of task
        :rtype: str
        """
        res_json = res.json()
        if 'id' not in res_json:
            raise CellmapsGenerateHierarchyError('Error getting id from response: ' +
                                                 str(res_json) + ' ' + str(res.text))
        return res_json['id']

    def _is_task_complete(self, res, start_time=None,
                          timeout=None):
        """
        Checks if task is complete by examining the json from the **res** and
        if ``progress`` is ``100`` and ``status`` is ``complete`` the task is done

        :param res:
        :param start_time: time task was started in seconds
        :type start_time: float
        :param timeout: Number of seconds task is allowed to run before
                        considering the task is a failure
        :type timeout: float
        :raises CellmapsGenerateHierarchyError: If task ``status`` is not ``complete`` or
                                                if **timeout** exceeded
        :return: ``True`` if task is completed otherwise ``False``
        :rtype: bool
        """
        status_dict = res.json()
        if status_dict['progress'] == 100:
            if status_dict['status'] != 'complete':
                raise CellmapsGenerateHierarchyError('Task failed: ' +
                                                     str(status_dict))
            return True
        if (int(time.time()) - start_time) > timeout:
            raise CellmapsGenerateHierarchyError('Layout task exceeded timeout of ' +
                                                 str(timeout) + ' seconds')
        time.sleep(self._retry_sleep_time)
        return False

    def _wait_for_task(self, res, timeout=1800):
        """
        Waits for task set in **res** response

        :param res:
        :type res: :py:class:`requests.Response`
        :param timeout: Time in seconds to wait for task to complete
        :type timeout: int
        :raises CellmapsGenerateHierarchyError: If there is an error
        :return: task id
        :rtype: str
        """
        if res.status_code != 202:
            raise CellmapsGenerateHierarchyError('Error running layout: ' +
                                                 str(res.status_code) + ' : ' +
                                                 str(res.text))

        task_id = self._get_id_from_response(res)

        start_time = int(time.time())
        complete = False
        while complete is False:
            res = self._get_task_status(task_id=task_id,
                                        start_time=start_time,
                                        timeout=timeout)
            if res is None:
                continue

            complete = self._is_task_complete(res, start_time=start_time,
                                              timeout=timeout)
        return task_id


