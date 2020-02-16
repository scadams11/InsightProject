import pandas as pd
import numpy as np

%matplotlib inline
import matplotlib.pyplot as plt
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()

import psycopg2

import datetime
import dateparser

username = 'cadeadams'
dbname = 'usgs_stream_db_log'

con = None
con = psycopg2.connect(database = dbname, user = username)

sql_query = """
SELECT * FROM n06730500;
"""

site_data_from_sql = pd.read_sql_query(sql_query,con)

df_site = site_data_from_sql
df_site = df_site.rename(columns={'datetime':'ds'})
print(df_site.head())

x = pd.to_datetime(df_site['ds'])

fig, ax1 = plt.subplots(figsize=(15,10))
ax1.plot(x, df_site.y, color='blue')

ax1.set_title('Daily Mean Discharge (2018-2020)')

ax1.set_ylabel('Discharge (cubic feet per second)')
ax1.set_yscale('log')

ax1.set_xlabel('Date')
ax1.set_xlim(pd.Timestamp('2018-01-01'), pd.Timestamp('2020-01-01'))

fig.savefig('test1.png')
plt.close(fig)
