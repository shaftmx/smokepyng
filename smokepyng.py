#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Author: Gaël Lambert (gaelL) <gael.lambert@netwiki.fr>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import pandas as pd
import numpy as np
import requests
import time
import logging
from os.path import isfile
from os.path import join as os_join
import os
from yaml import load as load_yaml
import argparse
from Queue import Empty
from multiprocessing import Process, Queue, current_process, freeze_support
from multiprocessing.sharedctypes import Value
from scheduler import Job
import signal
import sys

try:
    import matplotlib.pyplot as plt
except ImportError:
    print 'Error : need to install python-matplotlib'


LOG = logging.getLogger('smokepyng')

def init_logger():
    "Init logger and handler"
    LOG.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s %(levelname)s -: %(message)s')
    hdl = logging.StreamHandler(); hdl.setFormatter(formatter); LOG.addHandler(hdl)

def get_args():
    "Init and return args from argparse"
    parser = argparse.ArgumentParser()

    parser.add_argument("-f", "--config-file",
            help="Config file.: ex conf.yaml.sample",
            type=file,
            required=True)

    parser.add_argument("--resample",
            help="Resample data in csv to optimize csv size",
            action='store_true',
            default=False
            )

    parser.add_argument("--fetch",
            help="Start fetch urls",
            action='store_true',
            default=False
            )

    parser.add_argument("--plot",
            help="Generate graphs fro all csv files",
            action='store_true',
            default=False
            )
    return parser.parse_args()



def check_http(url):
    "Return date when request start. And latency time"
    start = time.time()
    requests.get(url)
    local_time = time.localtime(start)
    date_format = time.strftime('%Y-%m-%d %H:%M:%S', local_time)
    return date_format, time.time() - start

def record_http_time(record, record_file):
    """Write new line in csv file. If the file is new
    write also the header"""
    # Write header line
    if not isfile(record_file):
        with open(record_file, 'a') as f:
            f.write( 'date,time\n')
    # Write one line of stats
    with open(record_file, 'a') as f:
        f.write( '%s,%s\n' % record)

def ensure_dir(path):
    "Ensure a directory exist or create it."
    if not os.path.isdir(path):
        os.makedirs(path)

def resampled_time_serie(time_serie, rows, step):
    """Resample datas. Merge all data for the same time and
       get last rows * step time"""
    time_serie = time_serie.resample(step, how='mean')[-rows:]
    return time_serie

def resample_csvs(config):
    """Resample csv files to match the config.
     Do the average and delete spared values"""
    csv_path = config.get('csv_path')
    # For each urls
    for url_config in config.get('urls'):
        label = url_config.get('label')
        render_step = url_config.get('render_step')
        render_rows = url_config.get('render_rows')
        # Get filename
        csv_file = os_join(csv_path, '%s.csv' % label)

        if not isfile(csv_file):
            continue
        # Load time serie
        time_serie =  pd.read_csv(csv_file, index_col=0, parse_dates=True)
        # Resample datas for desired time periode
        time_serie = resampled_time_serie(time_serie=time_serie,
                                         rows=render_rows,
                                         step=render_step)

        # Dump datas in csv file (resampled file)
        time_serie.to_csv(csv_file, header=['time'], index_label='date')

def plot_csvs(config):
    """Generate png graphs for all urls. From csv files"""
    # Ensure directory exist
    plot_path = config.get('plot_path')
    csv_path = config.get('csv_path')
    ensure_dir(plot_path)

    # Open csv and plot thems   
    for url_config in config.get('urls'):
        label = url_config.get('label')
        render_step = url_config.get('render_step')
        render_rows = url_config.get('render_rows')
        # Get filename
        csv_file = os_join(csv_path, '%s.csv' % label)
        figure_file = os_join(plot_path, '%s.png' % label)

        if not isfile(csv_file):
            continue
        # Resample datas to display desired time periode
        time_serie =  pd.read_csv(csv_file, index_col=0, parse_dates=True)
        time_serie = resampled_time_serie(time_serie=time_serie,
                                         rows=render_rows,
                                         step=render_step)
        # Get datas and generate figure
        data_frame = pd.DataFrame(data=time_serie, index=time_serie.index, columns=['time'])
        plot = data_frame.plot()
        figure = plot.get_figure()
        figure.savefig(figure_file)

def worker(stop_process, result_queue, global_config, url_config):
    """Just fetch url every fetch_periode"""

    # Disable ctrl + c
    signal.signal(signal.SIGINT, signal.SIG_IGN)

    url = url_config.get('url')
    label = url_config.get('label')
    fetch_period = url_config.get('fetch_period')

    LOG.info('worker - Start worker %s' % label)

    job = Job(name=label,
              every=fetch_period,
              func=check_http,
              func_args={'url':url})

    while stop_process.value != 1:
        # If scheduled curl go or do nothing
        if job.should_run():
            LOG.info('worker - curl url %s' % url)
            job_result = job.run()
            
            result_queue.put({'job_result': job_result, 'url_config': url_config})
        time.sleep(0.1)


def consumer(stop_process, result_queue, config):
    "Consume results from workers. And write them in csv files"
    # Disable ctrl + c
    signal.signal(signal.SIGINT, signal.SIG_IGN)

    # Ensure directory exist (move to consumer)
    csv_path = config.get('csv_path')
    ensure_dir(csv_path)

    # Get and print results
    LOG.info('consumer - Start consumer')
    while stop_process.value != 1:
        try:
            msg = result_queue.get_nowait()
            label = msg['url_config']['label']
            record = msg['job_result']
            record_file = os_join(csv_path, '%s.csv' % label)
            LOG.debug('consumer - Receved ->>> %s\n' % str(msg))
            LOG.info('consumer - Save record %s in %s\n' % (str(record), record_file))
            record_http_time(record=record, record_file=record_file)
        except Empty:
            sys.stdout.write('.')
            sys.stdout.flush()
            time.sleep(0.1)

def start_fetch(config):
    """Launch workers and consumer.
         * Workers : one by url. The worker fetch a url and return fetch time
         * consumer : Just one. Get datas returned by workers
                      and write them to csv files"""

    # Create queues
    result_queue = Queue() # for results
    stop_process = Value('i', 0) # Integer shared value

    # Start fetch all urls
    for url_config in config.get('urls'):
        # Launch workers : process who fetch website and push result in result_queue
        Process(target=worker, args=(stop_process, result_queue, config, url_config)).start()

    # Launch consumer : process that write results from result_queue in csv files
    consumer_process = Process(target=consumer, args=(stop_process, result_queue, config))
    consumer_process.start()

    # run forever
    try:
        consumer_process.join()
        #while True:
        #    time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        stop_process.value = 1




if __name__ == '__main__':

    init_logger()

    args = get_args()

    # Load config
    config = load_yaml(args.config_file)

    if args.fetch:
        start_fetch(config)
    elif args.resample:
        resample_csvs(config)
    elif args.plot:
        plot_csvs(config)



# # For debug generate data sample
# # Init some datas : period seconde
# data_range = pd.date_range(start='1/1/2012', periods=10, freq='S')
# time_serie = pd.Series(np.random.randint(0, 500, len(data_range)), index=data_range)

# Format serie with a sum of all values
# df = df.cumsum()

