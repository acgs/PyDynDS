__author__ = 'Victor Szczepanski'

class IDGenerator(object):
    """
    Simply yields the next integer, beginning from 0.
    """

    def __init__(self):
        self._currentID = 0

    def nextID(self):
        """
        Generates the next ID.
        :return: Next ID to use.
        """
        self._currentID += 1
        return self._currentID - 1

    @property.setter
    def currentID(self, newID=0):
        raise ValueError("currentID is protected.")

    @property.getter
    def currentID(self):
        return self._currentID