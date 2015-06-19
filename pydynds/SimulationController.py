from multiprocessing import Queue
import time

from Algorithms.Algorithm import Algorithm, SampleAlgorithm
from Model.Model import Model
from Simulator.Simulator import Simulator
from common.SimulatorMessages import request_messages

__author__ = 'Victor Szczepanski'

"""
This module defines functions for controlling and coordinating the simulation. This module should be used to
run simulations in PyDynDS.
"""

from enum import Enum

class InvalidState(RuntimeError):
    pass

class SimulationController(object):
    """
    Controls access to the simulation.

    Provides a state-machine API for basic control of the Simulator, Algorithm, and Model.
    Most external programs should use this interface -
    however, direct access to the Simulator, Algorithm, or Model is made available through this class.

    Please note that direct access bypasses the SimulationController's state-machine,
    so the components may transition to a state that the SimulationController cannot handle properly.
    In this case, it is best to use the provided stop function to reinitialize the simulation.

    Also note that calling the stop function will cause all internal state to be lost -
    including any stats from the Algorithm or state of the Model.
    Only call this method after collecting any relevant information.

    A visual state diagram is made available in  docs/design/SimulatorControlStates.png

                | Stop    | Setup | Start   | Pause  |  Resume |
    ------------------------------------------------------------
    <-> STOPPED | STOPPED | SETUP |   -     |   -    |    -    |
        SETUP   | STOPPED |   -   | RUNNING |   -    |    -    |
        RUNNING | STOPPED |   -   |   -     | PAUSED |    -    |
        PAUSED  | STOPPED |   -   |   -     |   -    | RUNNING |

    """

    states = Enum('States', 'STOPPED SETUP RUNNING PAUSED')

    def __init__(self):
        # We initialize these class variables in __init__ to make it more clear. However, these are reinitialized in _init.
        self.running = False
        self.paused = False
        self.finished = False
        self.current_state = SimulationController.states.STOPPED

        # algorithm, simulator, and model are references to the subprocesses spawned by setup.
        self.algorithm = None
        self.algorithm_input_queue = None
        self.algorithm_output_queue = None
        self.algorithm_control_queue = None

        self.simulator = None
        self.simulator_input_queue = None
        self.simulator_output_queue = None

        self.model = None
        self.model_input_queue = None
        self.model_output_queue = None

        self._init()

    def _init(self):
        """
        Called during initialization and upon transitioning to STOPPED state.
        :return:
        """
        self.running = False
        self.paused = False
        self.finished = False
        self.current_state = SimulationController.states.STOPPED

        # algorithm, simulator, and model are references to the subprocesses spawned by setup.
        self.algorithm = None
        self.algorithm_input_queue = Queue()
        self.algorithm_output_queue = Queue()
        self.algorithm_control_queue = Queue()

        self.simulator = None
        self.simulator_input_queue = Queue()
        self.simulator_output_queue = Queue()

        self.model = None
        self.model_input_queue = Queue()
        self.model_output_queue = Queue()

    def setup(self, algorithm_name, dyndcop, message_delay=0, computation_cost=0):
        """
        Sets up the Simulator, Algorithm, and Model using provided arguments.
        :raises InvalidState: if setup is called and simulation is not STOPPED, raises this exception.
        :returns Simulator, Algorithm, Model: references to the new Simualtor, Algorithm, and Model objects.
        """
        if self.current_state is not SimulationController.states.STOPPED:
            raise InvalidState("Cannot setup a not stopped simulation. Current State: " + str(self.current_state))

        print("Making model...")
        self.model = Model(dyn_dcop=dyndcop, algorithm_input_queue=self.algorithm_input_queue,
                           algorithm_output_queue=self.algorithm_output_queue,
                           model_request_queue=self.model_input_queue, model_response_queue=self.model_output_queue,
                           message_delay=message_delay, computation_cost=computation_cost)

        print("Made model.")
        #Get initial state from model to pass to algorithm
        print("Getting initial state of DynDCOP...")
        self.model_input_queue.put(request_messages['CURRENT_STATE'])
        dcop = self.model_output_queue.get()

        print("Got state: " + str(dcop))

        print("Making Simulator...")
        self.simulator = Simulator()
        print("Made Simulator.")

        print("Making Algorithm...")
        alg_kwargs = {'simulator': self.simulator, 'simulator_request_queue': self.simulator_input_queue,
                      'simulator_response_queue': self.simulator_output_queue,
                      'model_request_queue': self.model_input_queue, 'model_response_queue': self.model_output_queue,
                      'control_queue': self.algorithm_control_queue,'initialDCOP': dcop}
        self.algorithm = Algorithm.factory(algorithm_name, **alg_kwargs)

        print("Made Algorithm.")
        self.current_state = SimulationController.states.SETUP
        print("Done with Setup.")

    def get_current_stats(self):
        """
        We name this function as a getter, rather than a property, since it incurs some inter-process communication.
        :return current stats from the algorithm:
        """

        return self.algorithm.stats

    def start(self):
        """
        Starts the simulation after setup has been called.
        INVARIANT: SimulationController state must be SimulationController.states.SETUP
        INVARIANT: SimulationController.current_state will be SimulationController.states.RUNNING upon completion.
        INVARIANT: if function does not run to completion, SimulationController.current_state will be SimulationController.states.SETUP.
        :raises InvalidState: if start is called and simulation is not in SETUP, raises this exception.
        :return:
        """
        if self.current_state is not SimulationController.states.SETUP:
            raise InvalidState("Simulation is not setup. Current State: " + str(self.current_state))

        self.model_input_queue.put(request_messages['START'])
        self.simulator_input_queue.put(request_messages['START'])
        self.algorithm_control_queue.put(request_messages['START'])

        self.current_state = SimulationController.states.RUNNING
        self.running = True

    def stop(self):
        """
        Stops the simulation and reinitializes the Simulator, Algorithm, and model components.
        Internal state will be the same as after initialization of SimulationController.
        :return:
        """
        if self.current_state is SimulationController.states.STOPPED:
            return
        try:
            # Send stop messages to algorithm, model, and simulator.
            self.algorithm_input_queue.put(request_messages['STOP'])
            self.simulator_input_queue.put(request_messages['STOP'])
            self.model_input_queue.put(request_messages['STOP'])
        except Exception as e:
            print(e)
            return

        self._init()

    def pause(self):
        if not self.running and self.current_state is not SimulationController.states.RUNNING:
            raise InvalidState("Cannot pause a stopped simulation. Current State: " + self.current_state)
        self.paused = True
        self.current_state = SimulationController.states.PAUSED

    def resume(self):
        if self.current_state is not SimulationController.states.PAUSED:
            raise InvalidState("Cannot resume a not paused simulation. Current State: " + self.current_state)


if __name__ == "__main__":
    sc = SimulationController()

    print("Setting up Simulation...")
    sc.setup(algorithm_name=SampleAlgorithm.__name__, dyndcop=None)
    print("Set up.")
    print("Starting Simulation...")
    sc.start()
    print("Started.")
    time.sleep(.01)

    print("Collecting stats...")
    print(sc.get_current_stats())

    print("Stopping Simulation...")
    sc.stop()
    print("Stopped.")