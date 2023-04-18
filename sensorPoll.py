#! /usr/bin/python3


import argparse
import logging
import logging.config
import sys
from threading import Event
import csv
import os
import time
from datetime import datetime
from gpiozero import InputDevice
import Adafruit_DHT


''' DISABLE imported loggers. '''
logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': True,
})


logger = logging.getLogger('----Sensor Poller (sensorPoll.py)')
stop_event = Event()
sensor = Adafruit_DHT.DHT22                                         # change if using different sensor


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
    parser.add_argument("-g", "--graph", help="Enable temperature graphs.",
                        action="store_true")                            # unimplemented

    return parser.parse_args()


def configure_logs(debug):
    '''Configure program logging.'''
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=level, filename='temperatures.log',
                        format='%(name)s - %(asctime)s - %(levelname)s - %(message)s')


def check_csv(file):
    '''Open/create csv file'''
    header = ['time','temperature(C)','humidity(%)']
    logger.info('Attempting to open file %s', file)

    if not file.endswith('.csv'):                                       # bad file specification
        logger.error('Specified file is not a csv!')
        sys.exit(1)
    if os.path.exists(file):                                            # file exists?
        logger.debug('File %s found.', file)
    else:                                                               # create new header
        logger.debug('Creating new file %s.', file)
        with open(file, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=header)
            writer.writeheader()


def wait_for_interrupt(myTime):
    '''  Handles sleep, interupt from main thread. '''
    while not stop_event.is_set():
        stop_event.wait(myTime)
        if stop_event.is_set():
            logger.info('Stopping sensor due to interrupt...')
            exit(0)

def poll(sensor, pin, myTime, file):
    '''Poll from sensor'''
    header = ['time','temperature(C)','humidity(%)']
    humidity, temperature = Adafruit_DHT.read_retry(sensor, pin)        # read temperature
    if temperature is not None and humidity is not None:
        #logger.debug('Recording new entry in %s.', file)
        with open(file, 'a', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=header)
            writer.writerow({'time': datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),      # ISO 8601, well rocognized format
                             'temperature(C)': round(temperature,4), 'humidity(%)': round(humidity,4)})
    else:
        logger.warning('Failed to read temperature.')
    wait_for_interrupt(myTime)


def poll_start(pin, outputFile, delay, debug):
    '''  This function is called by the controller '''
    ''' (see controller.py for details.) '''

    '''Configure options, set up files, writer.'''
    configure_logs(debug)
    check_csv(outputFile)

    logger.info('Starting sensor...')

    while True:                                                         # read until interrupt
        poll(sensor, pin, delay, outputFile)



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
            poll(sensor, args.pin, args.time, args.file)
    else:                                                               # read for number times
        while (args.number > 0):
            poll(sensor, args.pin, args.time, args.file)
            args.number = args.number - 1

    logger.info('Stopping sensor. Program completed successfully.')

if __name__ == '__main__':
    main()
