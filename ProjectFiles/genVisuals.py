#!/usr/bin/python3

''' Configure matplotlib for headless '''
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
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
    def __init__(self, logger, input_file, output_file, target, delay):
        super().__init__()                                          # ???
        ''' Initialize fields required by generator. '''

        self.logger = logger
        self.input_file = input_file
        self.output_file = output_file
        self.targets = (target, 30)                                 # ideal (or unideal) readings for reference
        self.max_display = int((24*60*60)/delay)                    # 24 hours of readings (size of graph x-axis

        self.df = None                                              # initialized in _get_dataframe()
        self.px = 1/plt.rcParams['figure.dpi']                      # for defining figuresize in pixels, matplotlib
        self.colors = {                                             # dictionary containing all color information
            'background': '#444444',
            'subplot': '#555555',
            'label': '#FFFFFF',
            'title': '#008000',
            'data': '#ffff00',
            0: 'g',                                                 # colors to draw target values
            1: 'r'
        }

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
                    self._create_table()

        self.logger.info('Stopping generation due to interrupt...')
        exit(0)


    def debug(self):                                                # called by main (see below)
        self.logger.debug(f'Getting dataframe...')
        self._get_dataframe()
        self.logger.debug(f'Generating {self.output_file}...')
        self._create_subplots()
        self.logger.debug(f'Creating tables...')
        self._create_table()


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

        timestamps = pd.to_datetime(timestamps, format='%Y-%m-%dT%H:%M:%S', errors='ignore')
        print(type(timestamps))

        fig, axs = plt.subplots(figsize=(1260*self.px, 1575*self.px),
                                nrows=len(data_elements.columns),
                                facecolor=self.colors['background'])
        mdates.HourLocator()
        for i, col in enumerate(data_elements.columns):
            axs[i].set_facecolor(self.colors['subplot'])
            axs[i].plot(timestamps[1:], data_elements[col][1:], color=self.colors['data'])

            axs[i].set_xlabel('Hour', color=self.colors['label'])
            axs[i].set_ylabel(col, color=self.colors['label'])
            axs[i].axhline(y=self.targets[i], color=self.colors[i], linestyle='dashed')
            axs[i].tick_params(labelcolor=self.colors['label'])

            axs[i].set_title(col, color=self.colors['title'])


        fig.suptitle('24-Hour Readings', color=self.colors['title'])
        plt.tight_layout()                                          # fixes overlapping
        plt.savefig(self.output_file, format='png')
        plt.close()                                                 # close the figure (saves resources)


    def _create_table(self):
        table = self.df.iloc[3:, -1]                                # grab table elements
        self.df.to_html("defaultTable.htm")


'''Testing-Section--------------------------'''

def parse_arguments():
    ''' Parse command line arguments. '''
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--debug", help="Enable debug logs.",
                        action="store_true")
    parser.add_argument("-f", "--file", help="Specify file to read.",
                        default="defaultRecords.csv")
    parser.add_argument("-g", "--graph_name", help="Specify name of graph output file.",
                        default="testGraph.png")

    return parser.parse_args()


def configure_logs(debug):
    '''Configure program logging.'''
    test_logger = logging.getLogger(__name__)
    level = logging.DEBUG if debug else logging.INFO

    file_handler = logging.FileHandler('./logs/genVisuals.log')
    file_handler.setFormatter(logging.Formatter('%(name)s - %(levelname)s - %(message)s'))

    test_logger.addHandler(file_handler)
    test_logger.setLevel(level)

    return test_logger


def main():
    ''' This function is used to test the graph generator '''
    ''' independently, supporting extra command-line arguments. '''

    ''' Configure options, read .csv, call plot function. '''
    args = parse_arguments()
    test_logger = configure_logs(args.debug)

    if not args.graph_name.endswith('.png'):                        # hope user knows what they're doing
        test_logger.warning(f"Specified graph name does not end in \".png\"!")

    generator = GenerateThread(test_logger, args.file, args.graph_name, 21, 5)
    generator.debug()

    test_logger.debug(f'Exiting genVisuals.py test...')


if __name__ == '__main__':
    main()
