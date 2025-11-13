#!/usr/bin/env python3

'''
    A simple script to run a speed test and save the details to a database
'''

__author__ = 'Eric J. Harlan'
__license__ = "GPLv3"

import speedtest
import json

import logging
from logging.config import fileConfig

# Set working directory to script location
os.chdir(Path(__file__).resolve().parent)

# Create logs directory if it's missing
Path('logs/').mkdir(exist_ok=True)

# Set up logger
logging_config_path = Path('logging_config.ini')
fileConfig(logging_config_path, disable_existing_loggers=False)
log = logging.getLogger()

def main():
    servers = []
    # If you want to test against a specific server
    # servers = [1234]

    threads = None
    # If you want to use a single threaded test
    # threads = 1

    logging.debug('Initializing')
    s = speedtest.Speedtest()
    s.get_servers(servers)

    logging.debug('Finding best server')
    s.get_best_server()

    logging.debug('Testing download speed')
    s.download(threads=threads)

    logging.debug('Testing upload speed')
    s.upload(threads=threads)

    # wtf is this
    s.results.share()

    results_dict = s.results.dict()

    print(results_dict)

    logging.debug('Writing results to json file')
    with open('results.json', 'w') as file:
        json.dump(results_dict, file)


if __name__ == '__main__':
    main()