import pandas as pd
import numpy as np

from sqlalchemy import create_engine
import psycopg2

import fbprophet 
from fbprophet.diagnostics import cross_validation

username = 'cadeadams'
dbname = 'usgs_stream_db_log'
engine = create_engine('postgres://%s@localhost/%s'%(username,dbname))

con = None
con = psycopg2.connect(database = dbname, user = username)

for site in site_no :
    sql_query = """
                SELECT * FROM n"""+site+""";
                """
    site_data_from_sql = pd.read_sql_query(sql_query,con)

    df_prophet = fbprophet.Prophet(changepoint_prior_scale=0.05, daily_seasonality=True, interval_width = 0.75)
    df_prophet.fit(site_data_from_sql)

    cv_results = cross_validation(df_prophet, initial = '1095 days', period = '180 days', horizon = '365 days')
    cv_results.to_sql("n"+str(site)+"_cv", engine, if_exists='replace')
