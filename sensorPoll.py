#! /usr/bin/python3

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
import argparse
import logging
import logging.config

''' DISABLE imported loggers. '''
logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': True,
})
root_logger = logging.getLogger()
root_logger.handlers = []                                           # clear handlers from imports

''' Global variables '''
logger = logging.getLogger('----Sensor Poller (sensorPoll.py)')
poll_stop = Event()                                                 # interupt from controller.py
signal_condition = threading.Condition()                            # signaler to genVisuals.py
sensor = Adafruit_DHT.DHT22                                         # DHT22 sensor by Adafruit

'''-----------------------------------------'''
def parse_arguments():
    ''' Parse command line arguments. '''
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--number", help="Specify number of readings.",
                        default=0, type=int)
    parser.add_argument("-p", "--pin", help="Specify pin sensor is connected to.",
                        default=4, type=int)
    parser.add_argument("-f", "--file", help="Specify output file.",
                        default="testPoll.csv")
    parser.add_argument("-t", "--time", help="Specify time inbetween sensor polls.",
                        default=300, type=int)
    parser.add_argument("-d", "--debug", help="Enable debug logs.",
                        action="store_true")

    return parser.parse_args()


def configure_logs(debug):
    '''Configure program logging.'''
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=level,
                        format='%(name)s - %(asctime)s - %(levelname)s - %(message)s')


def check_csv(file):
    '''Open/create csv file'''

    ''' Define CSV header. '''
    header = ['time','temperature(C)','humidity(%)', 'avtemp(C)', 'avHum(%)']

    logger.info('Attempting to open file %s', file)
    if not file.endswith('.csv'):                                   # bad file specification
        logger.error('Specified file is not a csv!')
        sys.exit(1)
    if os.path.exists(file):                                        # file exists?
        logger.debug('File %s found.', file)
    else:                                                           # create new header
        logger.debug('File %s missing. Writing new header.', file)
        with open(file, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=header)
            writer.writeheader()


def get_deque(time):
    ''' Calculate the size of the deque '''
    ''' to store averages, given time. '''
    time_in_min = time/60
    deque_size = math.floor(240/time_in_min)                        # four-hour history (4*60)
    logger.debug('Creating deque of size {deque_size}...')
    return deque(maxlen=deque_size)


def get_averages(history):
    temp_sum = sum(temp for temp, _ in history)
    humidity_sum = sum(humidity for _, humidity in history)
    average_temp = temp_sum / len(history)
    average_humidity = humidity_sum / len(history)

    return average_temp, average_humidity


def poll(sensor, pin, file, history):
    ''' Poll and write to CSV '''

    ''' Define CSV header. '''
    header = ['time','temperature(C)','humidity(%)', 'avtemp(C)', 'avHum(%)']

    humidity, temperature = Adafruit_DHT.read_retry(sensor, pin)    # read temperature

    if temperature is not None and humidity is not None:            # read success

        history.append((temperature, humidity))                     # add to history
        avTemp, avHum = get_averages(history)

        with open(file, 'a', newline='') as csvfile:

            writer = csv.DictWriter(csvfile, fieldnames=header)
            writer.writerow({'time': datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),  # ISO 8601, well rocognized format
                             'temperature(C)': round(temperature,4),
                             'humidity(%)': round(humidity,4),
                             'avtemp(C)' : round(avTemp,4),
                             'avHum(%)' : round(avHum,4)})
    else:
        logger.warning('Failed to read temperature.')


def poll_start(pin, outputFile, delay, debug):
    '''  This function is called by the controller '''
    ''' (see controller.py for details.) '''

    '''Configure options, set up files, writer.'''
    configure_logs(debug)
    check_csv(outputFile)
    history = get_deque(delay)                                      # get deque history respective to delay

    logger.info('Starting sensor...')

    while not poll_stop.is_set():                                   # read loop
        poll(sensor, pin, outputFile, history)
        logger.debug(f'Notifying genVisuals.py...')
        with signal_condition:
            signal_condition.notify()
        poll_stop.wait(delay)                                       # wait for delay, unless interrupt

    logger.info('Stopping sensor due to interrupt...')
    exit(0)


def main():
    ''' This function is used to test poll sensor '''
    ''' independently, supporting extra command-line arguments. '''

    '''Configure options, set up files, writer.'''
    args = parse_arguments()
    configure_logs(args.debug)
    check_csv(args.file)

    logger.info('Starting sensor connected to pin %d...', args.pin)
    if (args.number == 0):                                              # read until interrupt
        while True:
            poll(sensor, args.pin, args.file)
            time.sleep(args.time)
    else:                                                               # read for number times
        while (args.number > 0):
            poll(sensor, args.pin, args.file)
            args.number = args.number - 1
            time.sleep(args.time)

    logger.info('Stopping sensor. Program completed successfully.')

    poll_start(4,"defaultOut.csv",5,True)

#if __name__ == '__main__':
#    main()
