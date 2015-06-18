__author__ = 'Victor Szczepanski'

class Message(object):
    """
    Represents a message with arbitrary data. Usually contains a hypercube or the like.
    TODO: Decide if we need this class as a separate entity, or if we should use a namedtuple.
    """
    def __init__(self, source, destination, data=None):
        """
        This function will not modify source or destination nodes.
        :param source:
        :param destination:
        :param data:
        :return:
        """
        self.source = source
        self.destination = destination
        self.data = data

    def __str__(self):
        return ''.join(['(', str(self.source), ', ', str(self.destination), ', ', str(self.data), ')'])

    def __repr__(self):
        return self.__str__()

