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

try:
    import matplotlib.pyplot as plt
except ImportError:
    print 'Error : need to install python-matplotlib'


LOG = logging.getLogger()

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

def record_http_time(url, record_file):
    # Write header line
    if not isfile(record_file):
        with open(record_file, 'a') as f:
            f.write( 'date,time\n')
    # Write one line of stats
    with open(record_file, 'a') as f:
        f.write( '%s,%s\n' % check_http(url))

def ensure_dir(path):
    if not os.path.isdir(path):
        os.makedirs(path)

def resampled_time_serie(time_serie, rows, step):
    # Resample datas. Merge all data for the same time and get last rows x step time
    time_serie = time_serie.resample(step, how='mean')[-rows:]
    return time_serie

def resample_csvs(config):
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
        # Resample datas for desired time periode
        time_serie =  pd.read_csv(csv_file, index_col=0, parse_dates=True)
        time_serie = resampled_time_serie(time_serie=time_serie,
                                         rows=render_rows,
                                         step=render_step)
        # Get datas and generate figure
        data_frame = pd.DataFrame(data=time_serie, index=time_serie.index, columns=['time'])
        plot = data_frame.plot()
        figure = plot.get_figure()
        figure.savefig(figure_file)


def start_fetch(config):
    # Ensure directory exist
    csv_path = config.get('csv_path')
    ensure_dir(csv_path)
    # Start fetch all urls
    for url_config in config.get('urls'):
        url = url_config.get('url')
        label = url_config.get('label')
        fetch_period = url_config.get('fetch_period')
        for i in range(10):
            record_http_time(url=url, record_file=os_join(csv_path, '%s.csv' % label))
            time.sleep(fetch_period)



if __name__ == '__main__':

    init_logger()

    args = get_args()

    # Load config
    config = load_yaml(args.config_file)
    print config

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

