__author__ = 'Victor Szczepanski'

"""
Collection of classes that represent messages that are passed between the subprocesses of PyDynDS.
"""


class ViewUpdateRequest(object):
    """
    A simple class that represents a request from an algorithm for an update to its view of the DCOP from the simulator.
    """
    def __init__(self, timestamp=0):
        self.timestamp = timestamp


request_messages = {'STOP': 0, 'START': 1, 'PAUSE': 2, 'RESUME': 3, 'CURRENT_STATE': 4, 'SUCCESS': 5, 'STATS':6} # Enum('RequestMessages', 'STOP START PAUSE RESUME CURRENT_STATE')

