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
from sensorPoll import poll_start, poll_stop                        # import interupt event, default function (see sensorPoll.py)
from genVisuals import create_start, generate_stop                  # import interupt event, default function (see genVisuals.py)

''' Global variables '''
logger = logging.getLogger('Household Monitor (controller.py)')

'''-----------------------------------------'''
def interrupt_handler(signum, frame):
    ''' Handles SIGINT interrupts (Ctrl-C) '''
    ''' Handles SIGTERM interrupts (Kill)  '''
    logger.info(f'Handling signal {signum} ({signal.Signals(signum).name}).')
    logger.info(f'Terminating other threads...')

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
    '''Configure program logging.'''
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=level, filename='controller.log',
                        format='%(name)s - %(asctime)s - %(levelname)s - %(message)s')


def main():
    ''' This is the main function for the entire program. '''
    ''' Configure arguments, set up logger, generate new threads. '''
    args = parse_arguments()
    configure_logs(args.debug)

    logger.info(f'------------------------New session started:')
    logger.info(f'Generating new sensorPoll thread...')
    logger.debug(f'pin is %d, outputFile is %s, delay is %d seconds, debug status %s',
                 args.pin, args.file, args.time, args.debug)
    threadPoll = threading.Thread(target=poll_start, args=(args.pin,
                        args.file, args.time, args.debug))

    logger.info(f'Generating new genVisuals thread...')
    logger.debug(f'inputFile is %s, debug status %s',
                 args.file, args.debug)
    threadGenerate = threading.Thread(target=create_start, args=(args.file,
                                      "24-Hour Readings", "defaultGraph.png",
                                      args.debug))

    threadPoll.start()
    threadGenerate.start()

    threadPoll.join()
    threadGenerate.join()

    logger.info(f'Program terminating.')


if __name__ == '__main__':
    ''' Handle force-stop signal, start main. '''
    signal.signal(signal.SIGINT, interrupt_handler)
    signal.signal(signal.SIGTERM, interrupt_handler)

    main()
