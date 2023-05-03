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
    def __init__(self, logger, input_file, output_file, targetT, targetH, scale, delay):
        super().__init__()                                          # ???
        ''' Initialize fields required by generator. '''

        self.logger = logger
        self.input_file = input_file
        self.output_file = output_file
        self.targets = (targetT, targetH, targetT*(9/5)+32)         # ideal readings user-specified
        self.scale = (scale, scale*(9/5));                          # converting with +32 would be wrong for scale
        self.max_display = int((24*60*60)/delay)                    # 24 hours of readings (size of graph x-axis

        self.df = None                                              # initialized in _get_dataframe()
        self.px = 1/plt.rcParams['figure.dpi']                      # for defining figuresize in pixels, matplotlib

        self.colors = {                                             # CHANGE COLORS HERE
            'background': '#000000',
            'label': '#FFFFFF',                                     # spines, text, etc
            'title': '#009933',                                     # also used for targets
            'temp': '#0000ff',                                      # temperature data color
            'humid': '#9900cc',                                     # humidity data color
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
        '''Create all plot elements, including labeling. '''

        ''' Read in data split into time and readings. '''
        if len(self.df) >= self.max_display:
            temperatures = self.df.iloc[-self.max_display:, 1]      # 24hr of temps max
            humidities = self.df.iloc[-self.max_display:, 2]        # humid
            timestamps = self.df.iloc[-self.max_display:, 0]        # grab timestamp
        else:
            temperatures = self.df.iloc[0:, 1]
            humidities = self.df.iloc[0:, 2]
            timestamps = self.df.iloc[0:, 0]

        timestamps = pd.to_datetime(timestamps,                     # convert time to 'datetime' objects
                                    format='%Y-%m-%dT%H:%M:%S',     # allowing them to be automatically sized on axis
                                    errors='ignore')

        ''' Define resolution (1280x1024) '''
        fig, ax1 = plt.subplots(figsize=(1690*self.px, 1050*self.px),
                                facecolor=self.colors['background'])
        fig.subplots_adjust(left=0.12)                               # move over for two temp axis

        ax1.set_facecolor(self.colors['background'])                # TEMPERATURE
        ax1.scatter(timestamps, temperatures,
                    color=self.colors['temp'],
                    label='Temperature')
        ax1.axhline(y=self.targets[0],                              # user-specified target value
                    color=self.colors['title'],
                    linestyle='dashdot',
                    label='Target')
        ax1.set_xlabel('time', color=self.colors['label'])
        ax1.set_ylabel('Temperature (celsius)',
                        color=self.colors['label'])
        ax1.set_ylim(self.targets[0]-self.scale[0],                 # specify graph axis to get within +-scale from target
                     self.targets[0]+self.scale[0])
        ax1.tick_params(colors=self.colors['label'], which='both')
        ax1.spines[:].set_color(self.colors['label'])               # frame around graph
        ax1.legend(loc='upper right')
        plt.grid(axis='both',                                       # draw grid
                 which='both',
                 color=self.colors['label'],
                 linestyle='dotted',
                 linewidth=1)

        ax2 = ax1.twinx()                                           # plot humidity on same graph
        ax2.set_facecolor(self.colors['background'])                # HUMIDITY
        ax2.scatter(timestamps, humidities,
                 color=self.colors['humid'],
                 label='Humidity')
        ax2.axhline(y=self.targets[1],                              # user-specified target value
                    color=self.colors['title'],
                    linestyle='dotted',
                    label='Target')
        ax2.set_ylabel('Humidity (percent)',
                       color=self.colors['label'])
        ax2.set_ylim(self.targets[1]-self.scale[0],
                     self.targets[1]+self.scale[0])
        ax2.tick_params(colors=self.colors['label'], which='both')
        ax2.spines[:].set_color(self.colors['label'])               # frame around graph
        ax2.legend(loc='lower right')

        ax3 = ax1.twinx()
        ax3.spines["left"].set_position(("axes", -0.06))            # move floating spine near deg C
        ax3.set_ylabel('Temperature (fahrenheit)',
                        color=self.colors['label'])
        ax3.set_ylim(self.targets[2]-self.scale[1],
                     self.targets[2]+self.scale[1])
        ax3.tick_params(colors=self.colors['label'], which='both')
        ax3.yaxis.set_label_position('left')
        ax3.yaxis.set_ticks_position('left')
        ax3.spines[:].set_color(self.colors['label'])               # frame around graph

        #fig.suptitle('24-Hour Readings',                           # Website contains this information
        #             color=self.colors['title'],
        #             fontsize=20)
        #plt.tight_layout()                                          # fixes overlapping
        plt.savefig(self.output_file, format='png')
        plt.close()                                                 # close the figure (saves resources)

    def _create_table(self):
        averages = self.df.iloc[-1:,-2:]                            # get last row of the last two columns
        # self.logger.debug(type(averages))
        # self.logger.debug(type(self.df))
        # self.logger.debug(averages.shape)
        averages.to_html("averageTable.htm")
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

    generator = GenerateThread(test_logger, args.file, args.graph_name, 20, 40, 7.5, 300)
    generator.debug()                                               # calls the single-iteration debug method

    test_logger.debug(f'Exiting genVisuals.py test...')


if __name__ == '__main__':
    main()
