from threading import Thread

from common.SimulatorMessages import request_messages
from common.pydyndsProcess import pydyndsProcess

__author__ = 'Victor Szczepanski'

class Model(pydyndsProcess):
    """
    Model defines the current state of the DynDCOP. It exposes several functions for interacting with the model.
    This object is thread-safe; however, it is not intended to be modified by external operations.
    Thus, we use Properties to prevent accidental modification. If the developer wishes to modify these objects,
    please modify the appropriate property.

    TODO: Decide if we want to simulate messages or computations with variable delays, instead of assuming every
    message or computation takes the same time.
    """

    def __init__(self, dyn_dcop=None, algorithm_input_queue=None, algorithm_output_queue=None, model_request_queue=None, model_response_queue=None, model_message_event=None, algorithm_message_event=None, message_delay=0, computation_cost=0):
        """
        Initializes the model.
        :param dyn_dcop: the DynDCOP instance to simulate
        :param algorithm: the algorithm that is processing the DynDCOP. The Model polls the algorithm for stats that it
        uses to advance time in the DynDCOP.

        TODO: Mark fields as synchronized
        :return:
        """
        super().__init__(model_request_queue, model_response_queue, model_message_event)
        assert model_message_event is not algorithm_message_event
        self._dynDCOP = dyn_dcop
        self._algorithm_input_queue = algorithm_input_queue
        self._algorithm_output_queue = algorithm_output_queue
        self._algorithm_message_event = algorithm_message_event

        self._running = False
        self._finished = False

        self.currentDCOP = None #TODO: init with initial state of DynDCOP.
        self._currentCycle = 0
        self._lastMessageID = 0
        self._lastComputationID = 0

        #Settings
        self.messageDelay = message_delay
        self.computationCost = computation_cost

        self.simulation_thread = Thread(target=self.run)

        print("Done setting up Model.")

    @property
    def dynDCOP(self):
        return self._dynDCOP

    @dynDCOP.setter
    def dynDCOP(self, new_dyn_dcop=None):
        raise ValueError("dynDCOP is protected in Model. Change the setter property to allow modifications.")

    @property
    def algorithm_input_queue(self):
        return self._algorithm_input_queue

    @algorithm_input_queue.setter
    def algorithm_input_queue(self, new_algorithm=None):
        raise ValueError("algorithm_control_input_queue is protected in Model. Change the setter property to allow modifications.")

    @property
    def algorithm_output_queue(self):
        return self._algorithm_output_queue

    @algorithm_output_queue.setter
    def algorithm_output_queue(self, new_algorithm=None):
        raise ValueError("algorithm_control_output_queue is protected in Model. Change the setter property to allow modifications.")

    @property
    def running(self):
        return self._running

    @running.setter
    def running(self, new_state=False):
        raise ValueError("running is protected in Model. Change the setter property to allow modifications.")

    @property
    def finished(self):
        return self._finished

    @finished.setter
    def finished(self):
        raise ValueError("finished is protected in Model. Change the setter property to allow modifications.")

    @property
    def currentCycle(self):
        return self._currentCycle

    @currentCycle.setter
    def currentCycle(self, cycle_number=0):
        raise ValueError("currentCycle is protected in Model. Change the setter property to allow modifications.")

    @property
    def lastMessageID(self):
        return self._lastMessageID

    @lastMessageID.setter
    def lastMessageID(self, new_id=0):
        raise ValueError("lastMessageID is protected in Model. Change the setter property to allow modifications.")

    @property
    def lastComputationID(self):
        return self._lastComputationID

    @lastComputationID.setter
    def lastComputationID(self, new_id=0):
        raise ValueError("lastComputationID is protected in Model. Change the setter property to allow modifications.")

    def _special_control(self, request):
        """
        Overrides pydyndsProcess._special_control.
        :param request: The incoming request.
        :return bool: True if request handled. Else False.
        """
        if request is request_messages['CURRENT_STATE']:
            self._output_queue.put(self.currentDCOP)
            return True
        return False

    def run(self):
        """
        Launches the model's update process. Use this function when starting a new Model in a thread or subprocess.
        Initializes Model.running to True and Model.finished to False.
        Exits when it detects the end of the DynDCOP.

        :return:
        """
        self._running = True
        self._finished = False
        #TODO: Replace boolean exit flags with events that pydyndsProcess can signal.
        while self._running:
            self._update()

        print("Exiting model run...")

    def pre_stop(self):
        print("pre_stop Model.")
        self._stop = True
        self._running = False

    def _update(self):
        """
        Polls the algorithm for new stats to use to update the model with.
        :return:
        """

        #TODO: Use message passing with the algorithm's queues
        print("Model Update!")
        print("Number of pending requests to algorithm: " + str(self._algorithm_input_queue.qsize()))
        self._algorithm_input_queue.put(request_messages['STATS'])
        self._algorithm_message_event.set()
        new_messages = self._algorithm_output_queue.get()
        print("Got response from algorithm: " + str(new_messages))
        #new_computations = self.algorithm.newComputations

        #message_time = self._compute_messages_time(new_messages)
        #computation_time = self._compute_computations_time(new_computations)

        #TODO: store and calculate stats

        #advance model by greater of message cost or computation cost

        #self.currentCycle = max(message_time, computation_time) # This allows computations to be parallel to eachother and messages

        #Assumption: self.dynDCOP orders dcops by start cycle.
        if self._finished is not True:
            pass
            """
            for dcop in self.dynDCOP:
                if dcop.startCyle > self.currentCycle:
                    self.currentDCOP = dcop
                    if dcop.startCyle < self.currentCycle:
                        self._finished = True
            """

    def _compute_messages_time(self, new_messages=()):
        """
        Using the settings of this Model, calculates the time, in cycles, to advance due to new messages sent.
        :param new_messages: the new messages that have completed being sent.
        :return: the number of cycles to advance the model by.
        """
        last_first_cycle = _find_latest_start(new_messages)
        return last_first_cycle - self._currentCycle + self.messageDelay

    def _compute_computations_time(self, new_computations=()):
        last_first_cycle = _find_latest_start(new_computations)
        return last_first_cycle - self._currentCycle + self.computationCost


def _find_latest_start(new_items=()):
    """
    Finds the start cycle of the latest item.
    Assumes all items take the same time (have the same cost)
    :param new_items: the list of items to check
    :returns last_first_cycle: the the latest start cycle.
    """

    last_first_cycle = new_items[0].startCycle
    for message in new_items:
        if message.startCycle > last_first_cycle:
            last_first_cycle = message.startCycle

    return last_first_cycle


if __name__ == "__main__":
    pass
