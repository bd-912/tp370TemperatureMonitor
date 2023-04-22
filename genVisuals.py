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
import threading
''' Debugging tools '''
import argparse
import logging

''' Global variables '''
generate_stop = Event()                                             # interrupt from controller.py
from sensorPoll import signal_condition                             # signaler from sensorPoll.py

'''Main-------------------------------------'''

class GenerateThread(threading.Thread):
    def __init__(self, logger, input_file, output_file, delay):
        super().__init__()                                          # ???
        ''' Initialize fields required by generator. '''

        self.logger = logger
        self.input_file = input_file
        self.output_file = output_file
        self.max_display = int((24*60*60)/delay)                    # 24 hours of readings (size of graph x-axis

        self.df = None                                              # initialized in _get_dataframe()

        self.logger.info('Generator fields initialized')


    def run(self):
        self.logger.info('Starting generation cycle...')

        while True:
            with signal_condition:
                if generate_stop.is_set():
                    break

                signal_received = signal_condition.wait(1)          # wait for signal for up to 1 second
                if signal_received:
                    self.logger.debug(f'Signal from sensorPoll.py received!')
                    self._get_dataframe()                           # we have to reread csv every time
                    self._create_subplots()

        self.logger.info('Stopping generation due to interrupt...')
        exit(0)


    def _get_dataframe(self):
        '''Read in the data from csv'''
        if not self.input_file.endswith('.csv'):
            logger.error('Specified file is not a csv!')
            exit(1)
        self.df = pd.read_csv(self.input_file)


    def _create_subplots(self):
        '''Create all plot elements, including labeling.'''

        if len(self.df) >= self.max_display:
            data_elements = self.df.iloc[-self.max_display:, 1:3]   # day of temps max
            timestamps = self.df.iloc[-self.max_display:, 0]        # grab timestamp
        else:
            data_elements = self.df.iloc[0:, 1:3]
            timestamps = self.df.iloc[0:, 0]

        fig, axs = plt.subplots(nrows=len(data_elements.columns))
        for i, col in enumerate(data_elements.columns):
            axs[i].plot(timestamps[1:], data_elements[col][1:])     # don't plot header

            axs[i].set_xlabel('Time')
            axs[i].set_ylabel(col)
            axs[i].set_title(col)

        fig.suptitle("24-Hour Readings")
        plt.tight_layout()
        plt.savefig(self.output_file, dpi=300, format='png')
        plt.close()                                                 # close the figure (saves resources)


'''Testing-Section--------------------------'''

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
