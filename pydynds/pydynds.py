__author__ = 'Victor Szczepanski'

"""
This module handles the entry into pydynds. It may be invoked through the command line or used in other programs.
The main function handles starting up the simulator.
"""

import argparse

from pydynds.SimulationController import SimulationController

class PyDynDS(object):

    def __init__(self):
        self.sim_controller = None

    def main(self, algorithm_name, message_delay, computation_delay, dyndcop_filename):
        """
        main handles initialization of the pydynds simulator and kicks off a simulation.
        :param algorithm_name:
        :param message_delay:
        :param computation_delay:
        :param dyndcop_filename:
        :return:
        """

        #TODO: Read in dyndcop from file
        dyndcop = None

        self.initialize(algorithm_name, message_delay, computation_delay, dyndcop)

        self.make_CLI()

    def initialize(self, algorithm_name, message_delay, computation_delay, dyndcop):
        """
        Initializes the simulator.

        :return:
        """
        self.sim_controller = SimulationController(algorithm_name, message_delay, computation_delay, dyndcop)

    def make_CLI(self):
        """
        Makes a command-line interface to interact with the simulator.
        :return:
        """
        pass

    def display_DynDCOP(self):
        """
        Uses curses to display the current state of the DynDCOP.
        :return:
        """
        pass

    def initialize_simulator(self):
        """
        Reinitalizes the simulator.
        :return:
        """
        #TODO: include logic to destroy any simulator, algorithm, or model instances.
        self.initialize()

    def start_simulation(self):
        """
        Kicks off the actual simulation of the provided DynDCOP.
        :return:
        """
        self.sim_controller.setup()
        self.sim_controller.start()

    def pause_simulation(self):
        """
        Signals the simulation to pause. Stats can still be gathered and reported by the Model, but processing in the Algorithm is suspended.
        :return:
        """
        self.sim_controller.pause()

    def resume_simulation(self):
        """
        Signals the simulation to continue from paused state. Raises an exception if simulation is not paused.
        :return:
        """
        pass

    def stop_simulation(self):
        """
        Signals the simulation to stop all behaviour and quit.
        :returns stats, dynDCOP:the stats of the Algorithm and current state of the model
        """
        pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='The Python Dynamic DCOP Simulator (PyDynDS)')
    parser.add_argument('algorithm_name', metavar='A', type=str,
                       help='The name of the Algorithm class to use in this simulation.')
    parser.add_argument('message_delay', metavar='M', type=int,
                       help='The delay, in cycles, for each message.')
    parser.add_argument('computation_delay', metavar='C', type=int,
                       help='The delay, in cycyles, for each computation.')
    parser.add_argument('DynDCOP', metavar='D', type=str,
                       help='The path to a DynDCOP file.')

    args = parser.parse_args()
    pydynds = PyDynDS()
    pydynds.main(args.algorithm_name, args.message_delay, args.computation_delay, args.DynDCOP)
