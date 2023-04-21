#!/usr/bin/python3

''' Configure matplotlib for headless '''
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
''' Dataframes '''
import numpy as np
import pandas as pd
''' Manipulate time '''
from datetime import datetime
''' Multithreading tools '''
from threading import Event
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
logger = logging.getLogger('--Image Generator (genVisuals.py)')
generate_stop = Event()                                             # interrupt from controller.py
from sensorPoll import signal_condition                             # signaler from sensorPoll.py

'''-----------------------------------------'''
def parse_arguments():
    ''' Parse command line arguments. '''
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--debug", help="Enable debug logs.",
                        action="store_true")
    parser.add_argument("-f", "--file", help="Specify file to read.",
                        default="temperatures.csv")
    parser.add_argument("-g", "--graph_name", help="Specify name of graph output file.",
                        default="testGraphs.png")

    return parser.parse_args()


def configure_logs(debug):
    '''Configure program logging.'''
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=level,
                        format='%(name)s - %(asctime)s - %(levelname)s - %(message)s')


def get_dataframe(file):
    '''Read in the data from csv'''
    if not file.endswith('.csv'):
        logger.error('Specified file is not a csv!')
        sys.exit(1)
    return pd.read_csv(file)


def create_subplots(df, graph_name, time):
    '''Create all plot elements, including labeling.'''

    total = 24 * 60 * 60                                            # minutes in a day
    reading_max = int(total/time)                                   # display only a day of temps

    logger.info(f'reading max is {reading_max}')
    print(f'reading max is {reading_max}')

    if len(df) >= (reading_max):
        data_elements = df.iloc[-reading_max:, 1:3]                 # day of temps max
        timestamps = df.iloc[-reading_max:, 0]                      # grab timestamp
    else:
        data_elements = df.iloc[0:, 1:3]
        timestamps = df.iloc[0:, 0]

    logger.info(f'timestamps are: {timestamps}')
    print(f'timestamps are: {timestamps.values[1:]}')
    print(f'data_elements are: {data_elements.values[1:][:,[0]]}')
    print(len(data_elements.columns))

    fig, axs = plt.subplots(nrows=len(data_elements.columns))

    for i, col in enumerate(data_elements.columns):
        #axs[i].plot(timestamps.values[1:], data_elements.values[1:][:,[col]])         # don't plot header
        axs[i].plot(timestamps[1:], data_elements[col][1:])         # don't plot header

        axs[i].set_xlabel('Time')
        axs[i].set_ylabel(col)
        axs[i].set_title(col)

    fig.suptitle("24-Hour Readings")
    plt.tight_layout()
    plt.savefig(graph_name, dpi=300, format='png')
    plt.close()                                                     # close the figure (saves resources)

def create_start(inputFile, graph_name, time, debug):
    '''  This function is called by the controller '''
    ''' (see controller.py for details.) '''

    '''Configure options, read .csv, call plot.'''
    configure_logs(debug)
    df = get_dataframe(inputFile)
    #logger.debug(f"The dataframe is:\n{df[0:3].to_string(index=False)}")

    logger.info('Starting generation cycle...')
    #logger.debug(f'generate_stop is {generate_stop.is_set()}.')

    while True:
        with signal_condition:
            if generate_stop.is_set():
                break

            signal_received = signal_condition.wait(1)              # wait for signal for up to 1 second
            if signal_received:
                logger.debug(f'Signal from sensorPoll.py received!')
                df = get_dataframe(inputFile)                       # we have to reread csv every time
                create_subplots(df, graph_name, time)

    logger.info('Stopping generation due to interrupt...')
    exit(0)


def main():
    ''' This function is used to test the graph generator '''
    ''' independently, supporting extra command-line arguments. '''

    ''' Configure options, read .csv, call plot function. '''
    args = parse_arguments()
    configure_logs(args.debug)

    if not args.graph_name.endswith('.png'):                        # hope user knows what they're doing
        logger.warning(f"Specified graph name does not end in \".png\"!")

    df = get_dataframe(args.file)
    logger.debug(f"The dataframe is:\n{df[0:5].to_string(index=False)}")
    print(f"The dataframe is:\n{df[0:5].to_string(index=False)}")

    create_subplots(df, args.graph_name, 300)

if __name__ == '__main__':
   main()
