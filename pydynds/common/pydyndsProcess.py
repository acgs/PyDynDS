from multiprocessing import Process
import queue
from threading import Thread, RLock

from common.SimulatorMessages import request_messages

__author__ = 'Victor Szczepanski'

class pydyndsProcess(Process):
    """
    Abstracts the interprocess communication API for PyDynDS subprocesses Algorithm, Model, and Simulator.

    Implementing classes must initialize the field `simulation_thread`.
    """
    def __init__(self, input_queue, output_queue, message_event):
        super().__init__(name=type(self).__name__)
        self._stop = False

        self.simulation_thread = None
        self._input_queue = input_queue
        self._output_queue = output_queue
        self._message_event = message_event

        #Set up communication thread
        self.control_thread = Thread(target=self._control)
        self.control_thread.start()

        self.pause_lock = RLock() #pause_lock lets us hold a lock on the run function of inheriting classes.

    def _control(self):
        """
        This function is responsible for monitoring the request queue for start, stop, and pause requests.
        :return:
        """
        print("Starting control thread for class " + type(self).__name__)
        while not self._stop:

            try:
                if not self._message_event.wait(1): #Wait for a message event so we don't do too much busy waiting
                    continue
                # print("Got message event in " + type(self).__name__ + "!")
                request = self._input_queue.get(block=False)
                print("Got request! " + str(request) + " To: " + type(self).__name__)
                if self._special_control(request):
                    continue
                if request is request_messages['START']:
                    self._start_control()
                    self._output_queue.put(request_messages['SUCCESS'])
                elif request is request_messages['STOP']:
                    print("Got stop event in " + type(self).__name__ + "!")
                    self._stop_control()
                    self._output_queue.put(request_messages['SUCCESS'])
                    break
                elif request is request_messages['PAUSE']:
                    self._pause_control()
                    self._output_queue.put(request_messages['SUCCESS'])
                elif request is request_messages['RESUME']:
                    self._resume_control()
                    self._output_queue.put(request_messages['SUCCESS'])
            except queue.Empty:
                continue
            except AttributeError: #in case the queue is None
                continue
        print("Done with control thread in class " + type(self).__name__)

    def _special_control(self, request):
        """
        To be implemented by subclasses to define custom handling of control requests.
        Should return True if request is handled. Else False.
        :return bool: True if request handled. Else False.
        """
        return False

    def pre_stop(self):
        """
        Virtual function to be implemented by implementing classes.
        :return:
        """
        pass

    def post_stop(self):
        pass

    def _stop_control(self):
        """
        Hooks to stop virtual function to allow inheriting classes to define additional behaviour.
        :return:
        """
        self.pre_stop()
        self._stop = True
        self.post_stop()

    def pre_pause(self):
        pass

    def post_pause(self):
        pass

    def _pause_control(self):
        """
        Pauses this process' main thread, but allows communication threads to continue.
        :return:
        """
        self.pre_pause()
        self.pause_lock.acquire()
        self.post_pause()

    def pre_resume(self):
        pass

    def post_resume(self):
        pass

    def _resume_control(self):
        self.pre_resume()
        self.pause_lock.release()
        self.post_resume()

    def pre_start(self):
        pass

    def post_start(self):
        pass

    def _start_control(self):
        self.pre_start()
        self.simulation_thread.start()
        self.post_start()
