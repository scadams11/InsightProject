import pandas as pd
import numpy as np

from sqlalchemy import create_engine
import psycopg2

import fbprophet 
from fbprophet.diagnostics import cross_validation

username = 'cadeadams'
dbname = 'usgs_stream_db_log'
engine = create_engine('postgres://%s@localhost/%s'%(username,dbname))
if not database_exists(engine.url):
    create_database(engine.url)

con = None
con = psycopg2.connect(database = dbname, user = username)

for site in site_no :
    sql_query = """
                SELECT * FROM n"""+site+""";
                """
    site_data_from_sql = pd.read_sql_query(sql_query,con)

    site_data_from_sql['y_orig'] = site_data_from_sql.y
    site_data_from_sql['y'] = np.log(site_data_from_sql.y)

    df_prophet = fbprophet.Prophet(changepoint_prior_scale=0.05, daily_seasonality=True, interval_width = 0.75)
    df_prophet.fit(site_data_from_sql)

    cv_results = cross_validation(df_prophet, initial = '1095 days', period = '180 days', horizon = '365 days')

    cv_results['y_rescaled'] = np.exp(cv_results['y'])
    cv_results['yhat_rescaled'] = np.exp(cv_results['yhat'])
    cv_results['yhat_upper_rescaled'] = np.exp(cv_results['yhat_upper'])
    cv_results['yhat_lower_rescaled'] = np.exp(cv_results['yhat_lower'])

    cv_results.to_sql("n"+str(site)+"_cv", engine, if_exists='replace')
