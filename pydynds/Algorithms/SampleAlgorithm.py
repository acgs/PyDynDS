__author__ = 'Victor Szczepanski'

import queue
from threading import Thread, RLock
from multiprocessing import Process
import copy
import time

from pydynds.common import Message, ViewUpdateRequest


class Algorithm(Process):
    """
    This class can be inherited from, but is designed as a sample for understanding and testing.
    All algorithms begin with the initial state of the DynDCOP as a static DCOP instance.
    """
    def __init__(self, simulator, simulator_request_queue, simulator_response_queue, model_request_queue, model_response_queue, initialDCOP=None):
        """

        :param simulator:
        :param simulator_request_queue: a multiprocessing.Queue used for sending requests to the simulator
        :param simulator_response_queue: a multiprocessing.Queue used for reading responses from the simulator
        :param model_request_queue: a multiprocessing.Queue used to read requests from a model for stats
        :param model_response_queue: a multiprocessing.Queue used for sending stats to the model.
        :param initialDCOP:
        :return:
        """
        print("Setting up Algorithm...")
        self._DCOP_view = initialDCOP
        self._simulator = simulator #the reference to the simulator so that we can send ready signals to it.
        self._request_queue = simulator_request_queue
        self._response_queue = simulator_response_queue
        self._model_request_queue = model_request_queue
        self._model_response_queue = model_response_queue

        self.running = False
        self.done = False

        self.end_stats_queues = False #Should be set to True by Model or Simulator to stop responses.

        self.stats_lock = RLock()

        #stats are made available through a dictionary, since namedtuples are not pickleable.
        self.stats = {'total_messages': 0, 'total_computations': 0, 'last_message': None, 'last_computation': None,
                      'unread_messages': [], 'unread_computations': []}

        print("Done.")
        print("Setting up model thread...")
        self.model_thread = Thread(target=self.read_stats)
        self.model_thread.start()
        print("Done.")

    def preprocessing(self):
        """
        Usually, the algorithm uses this function to build a pseudotree or do any other steps it needs to prior to
        beginning, like setting up nodes.
        Users may reimplement this function.
        :return:
        """
        print("Preprocessing...")
        print("Done.")
        pass

    def run(self):
        """
        The run function is used for every iteration through the DynDCOP.
        Multiple messages or computations may be completed during a single run.This is the entry point to the algorithm.

        :return:
        """
        print("Running...")
        if not self.run_setup():
            return

        self.Run()

        self.run_teardown()

        print("Done.")

    def run_setup(self):
        """
        Called at beginning of run.
        :return:
        """
        print("Setting up...")
        self.running = True

        if not self.check_input():
            self.running = False
            self.done = True
            return False

        self.preprocessing()
        print("Done.")
        return True

    def run_teardown(self):
        """
        Called at end of run.
        :return:
        """
        pass

    def Run(self):
        """
        User provided run function. This actually runs the algorithm using the current view, and is injected into the run function.
        Users should override this function to implement new algorithms.
        :return:
        """
        #Since this is a sample, we will just send one message.
        self.send_message(None, None, None)

    def send_message(self, source, destination, data=None):
        """
        Represents sending a message from source node `source` to destination node `destination`.
        Constructs a Message to store in various stats.

        In a true algorithm, the message would actually move from the source to the destination.
        :param source:
        :param destination:
        :return new_message: the Message to be sent to the destination.
        """
        new_message = Message.Message(source, destination, data)
        with self.stats_lock:
            self.stats['total_messages'] += 1
            self.stats['last_message'] = new_message
            self.stats['unread_messages'].append(new_message)

        return new_message

    def check_input(self):
        """
        This function verifies that the current view of the DCOP is valid (i.e. not None).
        :return:
        """
        return self._DCOP_view is None

    def read_stats(self):
        """
        Provided for other processes to have access to this Algorithm's stats. Intended to be run in a separate thread.
        :return:
        """
        while not self.end_stats_queues:
            print("Getting stats requests...")
            try:
                self._model_request_queue.get(block=False)
            except queue.Empty:
                continue
            except AttributeError: #in case the queue is None
                continue
            with self.stats_lock:
                try:
                    self._model_response_queue.put(copy.deepcopy(self.stats)) #We deep copy to decouple the stats.
                except Exception as e:
                    print(e)
        print("Done read_stats.")
    def ready(self):
        """
        Requests the current view of the Model from the Simulator and updates the Algorithm's view.
        :return:
        """
        try:
            self._request_queue.put(ViewUpdateRequest.ViewUpdateRequest())
        except Exception as e:
            print(e)
        try:
            self._DCOP_view = self._response_queue.get()
        except Exception as e:
            print(e)


if __name__ == "__main__":
    #make a new algorithm and run it in a new process.
    a = Algorithm(None, None, None, None, None, None)
    print(a.stats)
    a.run()
    time.sleep(.001)
    a.end_stats_queues = True
    print(a.stats)