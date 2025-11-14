#!/usr/bin/env python3

'''
    A simple script to run a speed test and save the details to a database
'''

__author__ = 'Eric J. Harlan'
__license__ = 'BSD-3'

# TODO:
# - Args for different options (test, history, graphs?)
# - Write readme

import duckdb
import json
import speedtest

import logging
from logging.config import fileConfig
from pathlib import Path
import os

# Set working directory to script location
os.chdir(Path(__file__).resolve().parent)

# Create logs directory if it's missing
Path('logs/').mkdir(exist_ok=True)

# Set up logger
logging_config_path = Path('logging_config.ini')
fileConfig(logging_config_path, disable_existing_loggers=False)
log = logging.getLogger()

def main():
    logging.info('Entering main()')

    results_dict = test_speeds()
    db_insert_results(results_dict)
    db_review_results()

    logging.info('Exiting main()')

def test_speeds() -> dict:
    logging.info('Entering test_speeds()')

    servers = []
    # If you want to test against a specific server
    # servers = [1234]

    threads = None
    # If you want to use a single threaded test
    # threads = 1

    logging.debug('Initializing')
    s = speedtest.Speedtest(secure=True)
    s.get_servers(servers)

    logging.debug('Finding best server')
    s.get_best_server()

    logging.debug('Testing download speed')
    s.download(threads=threads)

    logging.debug('Testing upload speed')
    s.upload(threads=threads)

    results_dict = s.results.dict()

    logging.debug(f'Results:\n{json.dumps(results_dict, indent=4)}')

    logging.info('Exiting test_speeds()')
    return results_dict

def db_insert_results(results_dict: dict):
    logging.info('Entering db_insert_results()')

    query = '''
        insert into results
        values (?, ?, ?, ?, ?, ?, ?, ?, ?)
    '''

    # Create a list with all of the values to insert
    results_list = [
        json.dumps(results_dict), # results_json
        results_dict['client']['isp'], # client_isp
        results_dict['server']['sponsor'], # server_sponsor
        results_dict['download'] / 1000000, # download_mbps
        results_dict['upload'] / 1000000, # upload_mbps
        results_dict['ping'], # ping_ms
        results_dict['timestamp'], # event_timestamp_utc
        results_dict['bytes_sent'], # bytes_sent
        results_dict['bytes_received'] # bytes_received
    ]

    if not Path('speed test results.db').is_file():
        log.debug('Database does not exist. Creating new database.')
        db_init()

    logging.debug('Creating connection to database')
    conn = duckdb.connect('speed test results.db')

    logging.debug('Inserting record into database')
    try:
        conn.execute(query, parameters=results_list)
        conn.close()
    except:
        logging.exception('Unable to insert results')
        raise

    logging.info('Exiting db_insert_results()')

def db_review_results(record_count: int = 10):
    logging.info('Entering db_review_results()')

    # This query will select the most recent records from the results table
    query = '''
        SELECT *
        FROM results
        order by event_timestamp_utc desc
        limit ?
    ;'''

    logging.debug('Creating connection to database')
    conn = duckdb.connect('speed test results.db')

    logging.debug(f'Displaying most recent {record_count} records.')
    conn.sql(query, params=[record_count]).show()
    conn.close()

    logging.info('Exiting db_review_results()')

def db_init():
    logging.info('Entering db_init()')

    logging.debug('Creating connection to database')
    try:
        conn = duckdb.connect('speed test results.db')

        conn.execute('CREATE TABLE results ('
                '    results_json varchar not null,'
                '    client_isp varchar not null,'
                '    server_sponsor varchar not null,'
                '    download_mbps float not null,'
                '    upload_mbps float not null,'
                '    ping_ms float not null,'
                '    event_timestamp_utc timestamptz not null,'
                '    bytes_sent int not null,'
                '    bytes_received int not null'
                ');'
        )

        conn.close()
    except:
        logging.exception('Unable to initalize database')
        raise

    logging.info('Exiting db_init()')

def load_results_json():
    try:
        with open('results.json') as j:
            results_dict = json.load(j)
            return results_dict
    except:
        log.exception('Unable to load results.json')
        raise

if __name__ == '__main__':
    try:
        main()
    except:
        log.exception('Exception caught at the top level')
        raise