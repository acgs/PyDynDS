__author__ = 'Victor Szczepanski'

class ViewUpdateRequest(object):
    """
    A simple class that represents a request from an algorithm for an update to its view of the DCOP from the simulator.
    """
    def __init__(self, timestamp=0):
        self.timestamp = timestamp
