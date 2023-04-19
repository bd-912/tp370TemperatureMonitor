#!/usr/bin/python3

import argparse
import sys
from threading import Event
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
import pandas as pd
import logging
import logging.config

''' DISABLE imported loggers. '''
logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': True,
})

root_logger = logging.getLogger()
root_logger.handlers = []

generate_stop = Event()                 # interrupt event
from sensorPoll import signal_condition # signals that poll has a new reading
logger = logging.getLogger('--Image Generator (genVisuals.py)')


def parse_arguments():
    ''' Parse command line arguments. '''
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--debug", help="Enable debug logs.",
                        action="store_true")
    parser.add_argument("-f", "--file", help="Specify file to read.",
                        default="temperatures.csv")
    parser.add_argument("-t", "--title", help="Specify title for plots.",
                        default="Temperatures and Humidity")
    parser.add_argument("-g", "--graph_name", help="Specify name of graph output file.",
                        default="testGraphs.png")

    return parser.parse_args()


def configure_logs(debug):
    '''Configure program logging.'''
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=level,
                        format='%(name)s - %(levelname)s - %(message)s')


def get_dataframe(file):
    '''Read in the data from csv'''
    if not file.endswith('.csv'):
        logger.error('Specified file is not a csv!')
        sys.exit(1)
    return pd.read_csv(file)


def wait_for_interrupt():
    '''  Handles sleep, interupt from main thread. '''
    while not stop_event.is_set():
        stop_event.wait(myTime)
        if stop_event.is_set():
            logger.info('Stopping generation due to interrupt...')
            exit(0)


def create_subplots(df, title, graph_name):
    '''Create all plot elements, including labeling.'''
    data_elements = df.columns[1:]                          # chop off the date column for now

    fig, axs = plt.subplots(nrows=len(data_elements))       # create subplots = num of columns


    for i, col in enumerate(data_elements):                 # plot subplots for each data element (temp, humid, etc.)
        logger.debug(f"i is: {i}")
        axs[i].plot(df[col][1:])
        logger.debug(f'Plotted {df[col][1:3]}')

        axs[i].set_xlabel('Reading')
        axs[i].set_ylabel(col)
        axs[i].set_title(col)

    fig.suptitle(title)
    plt.tight_layout()
    plt.savefig(graph_name, dpi=300, format='png')
    plt.close()                                             # close the figure (saves resources)


def create_start(inputFile, title, graph_name, debug):
    '''  This function is called by the controller '''
    ''' (see controller.py for details.) '''

    '''Configure options, read .csv, call plot.'''
    configure_logs(debug)
    df = get_dataframe(inputFile)
    logger.debug(f"The dataframe is:\n{df[0:3].to_string(index=False)}")

    logger.info('Starting generation cycle...')
    #logger.debug(f'generate_stop is {generate_stop.is_set()}.')

    while True:
        with signal_condition:
            if generate_stop.is_set():
                break

            signal_received = signal_condition.wait(1)  # wait for signal for up to 1 second
            if signal_received:
                logger.debug(f'Signal from sensorPoll.py received!')
                df = get_dataframe(inputFile)           # we have to reread csv every time
                create_subplots(df, title, graph_name)

    logger.info('Stopping generation due to interrupt...')
    exit(0)


def main():
    ''' This function is used to test the graph generator '''
    ''' independently, supporting extra command-line arguments. '''

    ''' Configure options, read .csv, call plot function. '''
    args = parse_arguments()

    if not args.graph_name.endswith('.png'):                        # hope user knows what they're doing
        logger.warning(f"Specified graph name does not end in \".png\"!")

    configure_logs(args.debug)

    df = get_dataframe(args.file)
    logger.debug(f"The dataframe is:\n{df[0:5].to_string(index=False)}")

    create_subplots(df, args.title, args.graph_name)

if __name__ == '__main__':
    main()
