from multiprocessing import Event

from common.SimulatorMessages import ViewUpdateRequest
from common.pydyndsProcess import pydyndsProcess
from common.SimulatorMessages import request_messages
from common import Message

__author__ = 'Victor Szczepanski'

import queue
from threading import Thread, RLock
import copy
import time



class Algorithm(pydyndsProcess):
    """
    This class should be inherited from to allow factory-like construction of Algorithms.
    When a new Algorithm is added to PyDynDS, add its name to the __new__ constructor.

    The pausing feature, weakly provided by pydyndsProcess, is implemented during the sendMessage and doComputation
    functions by acquiring a shared lock.
    """
    def __init__(self, algorithm_input_queue=None, algorithm_output_queue=None,
                 simulator_input_queue=None, simulator_output_queue=None, model_input_queue=None,
                 model_output_queue=None, simulator_message_event=None, model_message_event=None,
                 controller_message_event=None, initialDCOP=None):
        """
        :param algorithm_input_queue: a multiprocessing.Queue used for receiving control requests from controller.
        :param algorithm_output_queue: a multiprocessing.Queue used for responding to requests from controller.
        :param simulator_input_queue: a multiprocessing.Queue used for sending requests to the simulator
        :param simulator_output_queue: a multiprocessing.Queue used for reading responses from the simulator
        :param model_input_queue: a multiprocessing.Queue used to read requests from a model for stats
        :param model_output_queue: a multiprocessing.Queue used for sending stats to the model.
        :param simulator_message_event: a multiprocessing.Event used for signaling the simulator that a new request is pending.
        :param model_message_event: a multiprocessing.Event used to notify the algorithm that a new request is pending.
        :param controller_message_event: a multiprocessing.Event used to notify the algorithm that a new request is pending.
        :param initialDCOP: the initial state of the DynDCOP.
        :return:
        """
        super().__init__(algorithm_input_queue, algorithm_output_queue, controller_message_event)
        self._DCOP_view = initialDCOP

        self._simulator_input_queue = simulator_input_queue
        self._simulator_output_queue = simulator_output_queue
        self._simulator_message_event = simulator_message_event #Used to notify simulator that there is a request pending in simulator_control_input_queue.

        self._model_input_queue = model_input_queue
        self._model_output_queue = model_output_queue
        self._model_message_event = model_message_event #Used to receive notifications from model that there is a request in model_control_input_queue.

        self.running = False
        self.done = False

        self._stop = False #Should be set to True by Model or Simulator to stop responses.

        self.stats_lock = RLock()

        #stats are made available through a dictionary, since namedtuples are not pickleable.
        self.stats = {'total_messages': 0, 'total_computations': 0, 'last_message': None, 'last_computation': None,
                      'unread_messages': [], 'unread_computations': []}

        #Start thread to handle incoming requests from model
        self.model_request_thread = Thread(target=self.model_request_handler)
        self.model_request_thread.start()

        self.simulation_thread = Thread(target=self.run)

    @staticmethod
    def factory(desc, *args, **kwargs):
        subclass_names = {subclass.__name__: subclass for subclass in Algorithm.__subclasses__()}
        if desc in subclass_names:
            return subclass_names[desc](*args, **kwargs)
        raise NotImplementedError("The provided class name is not a subclass of Algorithm.")

    def model_request_handler(self):
        """
        Handles waiting for requests on the model i/o queues.Intended to be run in a thread.

        Accepted request types are request_messages['STATS'].

        May implement dependency injection if needed.
        :return:
        """
        while not self._stop:
            try:
                if not self._model_message_event.wait(1):  # Wait for 1 second for a request from model
                    continue
                request = self._model_input_queue.get(block=False)
                if request is request_messages['STATS']:
                    self._model_output_queue.put(self.get_stats())
                else:
                    raise ValueError("Model request " + str(request) + " not valid.")
            except queue.Empty:
                continue

    def pre_stop(self):
        """
        Stops the simulation thread and prepares it for a new run (as if it has never been run before).
        :return:
        """
        print("Stopping Algorithm.")
        self.done = True

    def end(self):
        """
        Stops all threads, including queue monitoring threads. Only call this method if you are sure you are done with
        this class, or will handle thread creation manually.
        :return:
        """
        pass

    def preprocessing(self):
        """
        Usually, the algorithm uses this function to build a pseudotree or do any other steps it needs to prior to
        beginning, like setting up nodes.
        Users may reimplement this function.
        :return:
        """
        pass

    def run(self):
        """
        The run function is used for every iteration through the DynDCOP.
        Multiple messages or computations may be completed during a single run.This is the entry point to the algorithm.

        See the ActivityDiagram for a visual description of this function's behaviour.
        :return:
        """
        print("Start of Algorithm run.")
        #TODO: Replace boolean exit flags with events that pydyndsProcess can signal.
        while not self.done:
            print("Algorithm running!")
            #check that we still have a valid DCOP instance and perform any pre-processing.
            with self.pause_lock:
                if not self.run_setup():
                    return

            #request update from simulator
            with self.pause_lock:
                self.ready()

            #actually run the algorithm
            self.Run()

            #any post-processing the algorithm needs before next run.
            with self.pause_lock:
                self.run_teardown()

        print("Exiting Algorithm run...")

    def run_setup(self):
        """
        Called at beginning of run.
        :return:
        """
        self.running = True

        if not self.check_input():
            self.running = False
            self.done = True
            return False

        self.preprocessing()
        return True

    def run_teardown(self):
        """
        Called at end of run.
        :return:
        """
        pass

    def _send_message(self, source, destination, data=None):
        """
        Represents sending a message from source node `source` to destination node `destination`.
        Constructs a Message to store in various stats.

        Inheriting classes may reimplement this function to define special behaviour.
        The send_message function is preferred in the API.
        :param source:
        :param destination:
        :param data:
        :return:
        """
        new_message = Message.Message(source, destination, data)
        with self.stats_lock:
            self.stats['total_messages'] += 1
            self.stats['last_message'] = new_message
            self.stats['unread_messages'].append(new_message)

    def send_message(self, source, destination, data=None):
        """
        Represents sending a message from source node `source` to destination node `destination`.
        Constructs a Message to store in various stats.

        In a true algorithm, the message would actually move from the source to the destination.
        :param source:
        :param destination:
        :return new_message: the Message to be sent to the destination.
        """
        with self.pause_lock:
            return self.send_message(source, destination, data)

    def check_input(self):
        """
        This function verifies that the current view of the DCOP is valid (i.e. not None).
        :return:
        """
        return self._DCOP_view is not None

    def get_stats(self):
        """
        returns a copy of this algorithm's current stats.
        :return:
        """
        with self.stats_lock:
            stats = copy.deepcopy(self.stats)
        return stats

    def _special_control(self, request):
        """
        Provided for other processes to have access to this Algorithm's stats. Intended to be run in a separate thread.
        :return:
        """
        if request is request_messages['STATS']:
            print("Got STATS request in Algorithm.")
            self._output_queue.put(self.get_stats())
            print("Successfully copied stats!")
            return True
        return False

    def ready(self):
        """
        Requests the current view of the Model from the Simulator and updates the Algorithm's view.
        :return:
        """
        #TODO: Handle errors more transparently, and do not block indefinetly.
        try:
            self._simulator_input_queue.put(ViewUpdateRequest())
            self._simulator_message_event.set()
        except Exception as e:
            print(e)

        # Block waiting on response from simulator.
        try:
            self._DCOP_view = self._simulator_output_queue.get()
        except Exception as e:
            print(e)


class SampleAlgorithm(Algorithm):
    """
    This class can be inherited from, but is designed as a sample for understanding and testing.
    All algorithms begin with the initial state of the DynDCOP as a static DCOP instance.
    """
    def __init__(self, algorithm_input_queue=None, algorithm_output_queue=None,
                 simulator_input_queue=None, simulator_output_queue=None, model_input_queue=None,
                 model_output_queue=None, simulator_message_event=None, model_message_event=None,
                 controller_message_event=None, initialDCOP=None):

        super().__init__(algorithm_input_queue, algorithm_output_queue, simulator_input_queue,
                         simulator_output_queue, model_input_queue, model_output_queue, simulator_message_event,
                         model_message_event, controller_message_event, initialDCOP)

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

    def Run(self):
        """
        User provided run function. This actually runs the algorithm using the current view, and is injected into the run function.
        Users should override this function to implement new algorithms.
        :return:
        """
        print("Beginning SampleAlgorithm...")
        #Since this is a sample, we will just send one message.
        self.send_message('v1','v2', [[1,2,3],[4,5,6],[7,8,9]])


if __name__ == "__main__":
    #make a new algorithm and run it in a new process.
    model_request_queue = queue.Queue()
    model_response_queue = queue.Queue()
    message_event = Event()
    alg_kwargs = {'simulator_request_queue': None, 'simulator_response_queue': None,
                  'model_request_queue': model_request_queue, 'model_response_queue': model_response_queue,
                  'message_event': message_event, 'algorithm_control_input_queue': model_request_queue,
                  'algorithm_control_output_queue': model_response_queue, 'initialDCOP': None}

    print("Creating algorithm " + str(SampleAlgorithm.__name__))
    a = Algorithm.factory(SampleAlgorithm.__name__, **alg_kwargs)
    print(a.stats)
    a.run()
    model_request_queue.put(request_messages['STATS'])
    message_event.set()
    time.sleep(.001)
    a.end_stats_queues = True
    a._stop_control()
    print(str(model_response_queue.get(block=False)))
