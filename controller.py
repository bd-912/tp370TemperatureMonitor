#! /usr/bin/python3


import threading
import signal
import argparse
import logging
import logging.config
import sys


''' DISABLE imported loggers. '''
'''   EXCEPT project files.   '''
logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': True,
})


from sensorPoll import poll_start, stop_event   # controller function
###


logger = logging.getLogger('Household Monitor (controller.py)')


def interrupt_handler(signum, frame):
    ''' Handles SIGINT interrupts (Ctrl-C) '''
    ''' Handles SIGTERM interrupts (Kill)  '''
    logger.info(f'Handling signal {signum} ({signal.Signals(signum).name}).')
    logger.info(f'Signaling other threads...')

    stop_event.set();


def parse_arguments():
    ''' Parse command line arguments. '''
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--pin", help="Specify gpio pin sensor is connected to.",
                        default=4, type=int)    # default gpio is FOUR
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

    logger.info(f'Generating new sensorPoll thread...')
    logger.debug(f'pin is %d, outputFile is %s, delay is %d seconds, debug status %s',
                 args.pin, args.file, args.time, args.debug)

    threadPoll = threading.Thread(target=poll_start, args=(args.pin,
                        args.file, args.time, args.debug))
    threadPoll.start()


    threadPoll.join()

    logger.info(f'Program terminating.')


if __name__ == '__main__':
    ''' Handle force-stop signal, start main. '''
    signal.signal(signal.SIGINT, interrupt_handler)
    signal.signal(signal.SIGTERM, interrupt_handler)

    main()
