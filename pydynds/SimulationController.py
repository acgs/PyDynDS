__author__ = 'Victor Szczepanski'

"""
This module defines functions for controlling and coordinating the simulation. This module should be used to
run simulations in PyDynDS.
"""


class SimulationController(object):

    def __init__(self):
        self.running = False
        self.paused = False
        self.finished = False

    def setup(self, algorithm_name):
        """
        Sets up the Simulator, Algorithm, and Model using provided arguments.
        :returns Simulator, Algorithm, Model: references to the new Simualtor, Algorithm, and Model objects.
        """
        pass

    def start(self):
        self.running = True

    def stop(self):
        self.running = False
        self.paused = False
        self.finished = True #maybe only set finished to True when entire DynDCOP is finished

    def pause(self):
        if not self.running:
            raise RuntimeError("Cannot pause a stopped simulation.")
        self.paused = True
