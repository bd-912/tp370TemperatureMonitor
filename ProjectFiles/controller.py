#! /usr/bin/python3

''' Multithreading tools '''
import threading
import signal
''' Debugging tools '''
import argparse
import logging
import logging.config
''' Project files '''
from sensorPoll import SensorThread, poll_stop                      # import interupt event, default function (see sensorPoll.py)
from genVisuals import GenerateThread, generate_stop                  # import interupt event, default function (see genVisuals.py)

''' Global variables '''
controller_logger = logging.getLogger('Household Monitor (controller.py)')
poll_logger = logging.getLogger('----Sensor Poller (sensorPoll.py)')
gen_logger = logging.getLogger('--Image Generator (genVisuals.py)')

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
    parser.add_argument("-d", "--delay", help="Specify time inbetween sensor polls. Default is five minutes.",
                        default=300, type=int)
    parser.add_argument("-t", "--target", help="Specify time inbetween sensor polls. Default is five minutes.",
                        default=21, type=int)
    parser.add_argument("-v", "--verbose", help="Enable full debug logs. See householdMonitor.log for information.",
                        action="store_true")

    return parser.parse_args()


def configure_logs(verbose):
    '''Configure program logging level.'''
    level = logging.DEBUG if verbose else logging.INFO

    ''' Configure file handler '''
    file_handler = logging.FileHandler('./logs/householdMonitor.log')
    file_handler.setFormatter(logging.Formatter('%(name)s - %(asctime)s - %(levelname)s - %(message)s'))

    ''' For the controller script '''
    controller_logger.addHandler(file_handler)
    controller_logger.setLevel(level)

    ''' For the sensorPoll script '''
    poll_logger.addHandler(file_handler)
    poll_logger.setLevel(level)

    ''' For the genVisuals script '''
    gen_logger.addHandler(file_handler)
    gen_logger.setLevel(level)


def main():
    ''' This is the main function for the entire program. '''
    ''' Configure arguments, set up logger, generate new threads. '''
    args = parse_arguments()
    configure_logs(args.verbose)

    controller_logger.info(f'------------------------New session started:')
    controller_logger.info(f'Generating new sensorPoll thread...')
    controller_logger.debug(f'pin is %d, outputFile is %s, delay is %d seconds, debug status %s',
                 args.pin, args.file, args.delay, args.verbose)
    poll_thread = SensorThread(poll_logger, args.pin,
                               args.file, args.delay)

    controller_logger.info(f'Generating new genVisuals thread...')
    controller_logger.debug(f'inputFile is %s, target is %d C, debug status %s',
                 args.file, args.target, args.verbose)
    gen_thread = GenerateThread(gen_logger, args.file,
                                "defaultGraph.png", args.target, args.delay)

    poll_thread.start()                                             # calls the run() method
    gen_thread.start()

    poll_thread.join()
    gen_thread.join()

    controller_logger.info(f'Program terminating.')


if __name__ == '__main__':
    ''' Handle force-stop signal, start main. '''
    signal.signal(signal.SIGINT, interrupt_handler)
    signal.signal(signal.SIGTERM, interrupt_handler)

    main()
