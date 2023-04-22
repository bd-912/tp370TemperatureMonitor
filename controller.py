#! /usr/bin/python3

''' Multithreading tools '''
import threading
import signal
''' Debugging tools '''
import argparse
import logging
import logging.config

''' DISABLE imported loggers. '''
'''   EXCEPT project files.   '''
logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': True,
})
root_logger = logging.getLogger()
root_logger.handlers = []                                           # clear handlers from imports

''' Project files '''
from sensorPoll import SensorThread, poll_stop                      # import interupt event, default function (see sensorPoll.py)
from genVisuals import create_start, generate_stop                  # import interupt event, default function (see genVisuals.py)

''' Global variables '''
controller_logger = logging.getLogger('Household Monitor (controller.py)')
poll_logger = logging.getLogger('----Sensor Poller (sensorPoll.py)')

'''-----------------------------------------'''
def interrupt_handler(signum, frame):
    ''' Handles SIGINT interrupts (Ctrl-C) '''
    ''' Handles SIGTERM interrupts (Kill)  '''
    controller_logger.info(f'Handling signal {signum} ({signal.Signals(signum).name}).')
    controller_logger.info(f'Terminating other threads...')

    poll_stop.set()                                                 # set interrupt
    generate_stop.set()


def parse_arguments():
    ''' Parse command line arguments. '''
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--pin", help="Specify gpio pin sensor is connected to.",
                        default=4, type=int)                        # default gpio is FOUR
    parser.add_argument("-f", "--file", help="Specify output file Set this to a pre-existing file to resume session.",
                        default="defaultRecords.csv")
    parser.add_argument("-t", "--time", help="Specify time inbetween sensor polls. Default is five minutes.",
                        default=300, type=int)
    parser.add_argument("-d", "--debug", help="Enable full debug logs. See householdMonitor.log for information.",
                        action="store_true")

    return parser.parse_args()


def configure_logs(debug):
    '''Configure program logging level.'''
    level = logging.DEBUG if debug else logging.INFO

    ''' Configure file handler '''
    file_handler = logging.FileHandler('controller.log')
    file_handler.setFormatter(logging.Formatter('%(name)s - %(asctime)s - %(levelname)s - %(message)s'))

    ''' For the controller script '''
    controller_logger.addHandler(file_handler)
    controller_logger.setLevel(level)

    ''' For the sensorPoll script '''
    poll_logger.addHandler(file_handler)
    poll_logger.setLevel(level)


def main():
    ''' This is the main function for the entire program. '''
    ''' Configure arguments, set up logger, generate new threads. '''
    args = parse_arguments()
    configure_logs(args.debug)

    controller_logger.info(f'------------------------New session started:')
    controller_logger.info(f'Generating new sensorPoll thread...')
    controller_logger.debug(f'pin is %d, outputFile is %s, delay is %d seconds, debug status %s',
                 args.pin, args.file, args.time, args.debug)
    poll_thread = SensorThread(poll_logger, args.pin,
                               args.file, args.time)

    controller_logger.info(f'Generating new genVisuals thread...')
    controller_logger.debug(f'inputFile is %s, debug status %s',
                 args.file, args.debug)
    threadGenerate = threading.Thread(target=create_start, args=(args.file,
                                      "defaultGraph.png",
                                      args.time, args.debug))

    poll_thread.start()                                             # calls the run() method
    threadGenerate.start()

    poll_thread.join()
    threadGenerate.join()

    controller_logger.info(f'Program terminating.')


if __name__ == '__main__':
    ''' Handle force-stop signal, start main. '''
    signal.signal(signal.SIGINT, interrupt_handler)
    signal.signal(signal.SIGTERM, interrupt_handler)

    main()
