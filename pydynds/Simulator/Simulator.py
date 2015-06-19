from multiprocessing import Process

__author__ = 'Victor Szczepanski'

class Simulator(Process):
    def __init__(self, simulator_input_queue=None, simulator_output_queue=None, algorithm_input_queue=None,
                 algorithm_output_queue=None, model_input_queue=None, model_output_queue=None):

        self.simulator_input_queue=simulator_input_queue
        self.simulator_output_queue=simulator_output_queue
        self.algorithm_input_queue = algorithm_input_queue
        self.algorithm_output_queue = algorithm_output_queue
        self.model_input_queue = model_input_queue
        self.model_output_queue = model_output_queue
