__author__ = 'Victor Szczepanski'

"""
This module handles the entry into pydynds. It may be invoked through the command line or used in other programs.
The main function handles starting up the simulator.
"""

import

from pydynds.SimulationController import SimulationController

def main(algorithm_name, message_delay, computation_delay, dyndcop_filename):
    """
    main handles initialization of the pydynds simulator and kicks off a simulation.
    :param algorithm_name:
    :param message_delay:
    :param computation_delay:
    :param dyndcop_filename:
    :return:
    """
    sim_controller = SimulationController()

    sim_controller.setup(algorithm_name)

    sim_controller.start()


if __name__ == "__main__":
    #read args from command line
    pass
