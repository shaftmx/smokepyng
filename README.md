# smokepyng

Simple HTTP smoke ping in python. Based on panda timeseries an pygal graphs

Usage ::

  usage: smokepyng.py [-h] -f CONFIG_FILE [--resample] [--fetch] [--plot]
  
  optional arguments:
    -h, --help            show this help message and exit
    -f CONFIG_FILE, --config-file CONFIG_FILE
                          Config file.: ex conf.yaml.sample
    --resample            Resample data in csv to optimize csv size
    --fetch               Start fetch urls
    --plot                Generate graphs fro all csv files

Launch the script to fetch urls (ctrl + c to exit) ::

  python smokepyng.py -f conf.yaml.sample --fetch

Generate graph for all urls ::

  python smokepyng.py -f conf.yaml.sample --plot

Resample datas. Merge datas between steps ::

  python smokepyng.py -f conf.yaml.sample --resample

