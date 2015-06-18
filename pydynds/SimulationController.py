__author__ = 'Victor Szczepanski'

"""
This module defines functions for controlling and coordinating the simulation. This module should be used to
run simulations in PyDynDS.
"""

from enum import Enum

class SimulationController(object):

    states = Enum('STOPPED', 'SETUP', 'RUNNING', 'PAUSED')

    def __init__(self):
        self.running = False
        self.paused = False
        self.finished = False
        self.current_state = SimulationController.states.STOPPED

    def setup(self, algorithm_name):
        """
        Sets up the Simulator, Algorithm, and Model using provided arguments.
        :returns Simulator, Algorithm, Model: references to the new Simualtor, Algorithm, and Model objects.
        """
        if self.current_state is not SimulationController.states.STOPPED:
            raise RuntimeError("Simulation in invalid state %s for transition to setup.", str(self.current_state))
        self.current_state = SimulationController.states.SETUP

    def start(self):
        if self.current_state is not SimulationController.states.SETUP:
            raise RuntimeError("Simulation in invalid state %s for transition to running.", str(self.current_state))
        self.current_state = SimulationController.states.RUNNING
        self.running = True

    def stop(self):
        self.running = False
        self.paused = False
        self.finished = True #maybe only set finished to True when entire DynDCOP is finished
        self.current_state = SimulationController.states.STOPPED

    def pause(self):
        if not self.running and self.current_state is not SimulationController.states.RUNNING:
            raise RuntimeError("Cannot pause a stopped simulation.")
        self.paused = True
        self.current_state = SimulationController.states.PAUSED

    def resume(self):
        pass
