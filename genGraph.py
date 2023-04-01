#!/usr/bin/python3

import argparse
import sys
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import pandas as pd
import logging
import logging.config

'''All of this is disable all imported loggers,
while allowing use of the root logger.'''
logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': True,
})

root_logger = logging.getLogger()
root_logger.handlers = []

logger = logging.getLogger('genGraph.py')

def parse_arguments():
    ''' Parse command line arguments. '''
    parser = argparse.ArgumentParser()    
    parser.add_argument("-d", "--debug", help="Enable debug logs.",
                        action="store_true")
    parser.add_argument("-f", "--file", help="Specify file to read.",
                        default="temperatures.csv")
    parser.add_argument("-t", "--title", help="Specify title for plots.",
                        default="Temperatures and Humidity")

    return parser.parse_args()

def configure_logs(debug):
    '''Configure program logging.'''
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=level, format='%(name)s - %(levelname)s - %(message)s')

def get_dataframe(file):
    '''Read in the data from csv'''
    if not file.endswith('.csv'):
        logger.error('Specified file is not a csv!')
        sys.exit(1)
    return pd.read_csv(file)

def create_subplots(df, title, debug):
    '''Create all plot elements, including labeling.'''
    data_elements = df.columns[1:]                          # chop off the date column for now

    fig, axs = plt.subplots(nrows=len(data_elements))       # create subplots = num of columns

    for i, col in enumerate(data_elements):                 # plot subplots for each data element (temp, humid, etc.)
        logger.debug(f"i is: {i}")
        axs[i].plot(df[col][1:])

        axs[i].set_xlabel('Reading')
        axs[i].set_ylabel(col)
        axs[i].set_title(col)

    fig.suptitle(title)
    plt.tight_layout()
    plt.show()

def main():
    '''Configure options, set up files, writer.'''
    args = parse_arguments()
    configure_logs(args.debug)

    df = get_dataframe(args.file)
    logger.debug(f"The dataframe is:\n{df[0:5].to_string(index=False)}")

    create_subplots(df, args.title, args.debug)

if __name__ == '__main__':
    main()
