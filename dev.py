import pandas as pd
import numpy as np
import requests
import time
from os.path import isfile


try:
    import matplotlib.pyplot as plt
except ImportError:
    print 'Error : need to install python-matplotlib'


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

# date,time
for i in range(10):
    record_http_time(url='http://www.google.com', record_file="/tmp/test.csv")
    time.sleep(0.10)

# # For debug
# # Init some datas : period seconde
# data_range = pd.date_range(start='1/1/2012', periods=10, freq='S')
# time_serie = pd.Series(np.random.randint(0, 500, len(data_range)), index=data_range)
# # Dump datas in csv file
# time_serie.to_csv('/tmp/test.csv', header=['time'], index_label='date')


# Load datas from csv
time_serie =  pd.read_csv("/tmp/test.csv", index_col=0, parse_dates=True)
print time_serie
print '-------------'
# Resample datas. Merge all data for the same time and get last 8 min
#time_serie = time_serie.resample('1min', how='mean')[-10:]
time_serie = time_serie.resample('1s', how='mean')[-10:]
print time_serie


#ts = pd.Series(np.random.randn(365), index=pd.date_range('1/1/2000', periods=365, freq='D'))
#df = pd.DataFrame(np.random.randn(365, 4), index=ts.index, columns=list('ABCD'))

#df = pd.DataFrame(data=time_serie, index=time_serie.index, columns=list('ABCD'))
df = pd.DataFrame(data=time_serie, index=time_serie.index, columns=['time'])

# Format serie with a sum of all values
# df = df.cumsum()

plot = df.plot()
fig = plot.get_figure()
#fig = plot.gcf()
fig.savefig("/tmp/output.png")
#plt.figure(); df.plot();

