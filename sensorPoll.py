''' File tools '''
import csv
import os
''' Data structures '''
import time
from datetime import datetime
from collections import deque
import math
''' Collection tools '''
from gpiozero import InputDevice
import Adafruit_DHT
''' Multithreading tools '''
from threading import Condition, Event
import threading
''' Debugging tools '''
import logging
import logging.config
import sys

''' Global variables '''
logger = logging.getLogger('----Sensor Poller (sensorPoll.py)')
poll_stop = Event()                                                     # interupt from controller.py
signal_condition = threading.Condition()                                # signaler to genVisuals.py

'''-----------------------------------------'''

class SensorThread(threading.Thread):
    def __init__(self, logger, pin, outputFile, delay):
        super().__init__()
        ''' Initialize fields required by sensor. '''

        self.logger = logger
        self.pin = pin
        self. outputFile = outputFile
        self.delay = delay

        self.header = ['time','temperature(C)','humidity(%)', 'avtemp(C)', 'avHum(%)']
        self.average_humidity = None                                    # defined in get_averqages
        self.average_temp = None
        self.sensor = Adafruit_DHT.DHT22                                # DHT22 sensor by Adafruit

        self.history = None                                             # initialized in get_deque
        self._check_csv()
        self._get_deque()

        self.logger.debug("Sensor fields initialized.")


    def run(self):
        self.logger.info('Starting sensor...')

        while not poll_stop.is_set():                                   # read loop
            self._poll()
            self.logger.debug(f'Notifying genVisuals.py...')
            with signal_condition:
                signal_condition.notify()
            poll_stop.wait(self.delay)                                  # wait for delay, unless interrupt

        self.logger.info('Stopping sensor due to interrupt...')
        exit(0)


    def _check_csv(self):
        '''Open/create csv file'''

        self.logger.info('Attempting to open file %s', self.outputFile)
        if not self.outputFile.endswith('.csv'):                        # bad file specification
            self.logger.error('Specified file is not a csv!')
            sys.exit(1)
        if os.path.exists(self.outputFile):                             # file exists?
            self.logger.debug('File %s found.', self.outputFile)
        else:                                                           # create new header
            self.logger.debug('File %s missing. Writing new header.', self.outputFile)
            with open(self.outputFile, 'w', newline='') as csvfile:     # open in write mode
                writer = csv.DictWriter(csvfile, fieldnames=self.header)
                writer.writeheader()


    def _get_deque(self):
        ''' Calculate the size of the deque '''
        ''' to store averages, given time. '''
        deque_size = math.floor(240/(self.delay/60))                    # four-hour history (4*60)
        logger.debug('Creating deque of size {deque_size}...')
        self.history = deque(maxlen=deque_size)


    def _poll(self):
        ''' Poll and write to CSV '''
        humidity, temperature = Adafruit_DHT.read_retry(self.sensor, self.pin)

        if temperature is not None and humidity is not None:            # read success

            self.history.append((temperature, humidity))                # add to history
            self._update_averages()                                     # update averages

            with open(self.outputFile, 'a', newline='') as csvfile:     # open in append mode

                writer = csv.DictWriter(csvfile, fieldnames=self.header)
                writer.writerow({'time': datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),  # ISO 8601
                                      'temperature(C)': round(temperature,4),
                                      'humidity(%)': round(humidity,4),
                                      'avtemp(C)' : round(self.average_temp,4),
                                      'avHum(%)' : round(self.average_humidity,4)})
        else:
            self.logger.warning(f'Failed to read temperature. Check specified pin. ({self.pin})')


    def _update_averages(self):
        temp_sum = sum(temperature for temperature, _ in self.history)
        humidity_sum = sum(humidity for _, humidity in self.history)
        self.average_temp = temp_sum / len(self.history)
        self.average_humidity = humidity_sum / len(self.history)

