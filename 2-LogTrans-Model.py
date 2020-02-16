import pandas as pd
import numpy as np

from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
import psycopg2

import fbprophet 

username = 'cadeadams'
dbname = 'usgs_stream_db_log'
engine = create_engine('postgres://%s@localhost/%s'%(username,dbname))

if not database_exists(engine.url):
    create_database(engine.url)

##
# Modeling data using fbprophet and saving to PostgreSQL database.
##
con = None
con = psycopg2.connect(database = dbname, user = username)

for site in site_no :
    sql_query = """
    SELECT * FROM n"""+site+""";
    """
    site_data_from_sql = pd.read_sql_query(sql_query,con)
    nonzero_mean = site_data_from_sql[ site_data_from_sql.y != 0 ].mean()
    site_data_from_sql.loc[ site_data_from_sql.y == 0, "y" ] = nonzero_mean

    df_site = site_data_from_sql
    df_site = df_site.rename(columns={'datetime':'ds'})
    df_site['y'] = np.log(df_site['y'])
    
    df_prophet = fbprophet.Prophet(changepoint_prior_scale=0.05, yearly_seasonality=True, interval_width = 0.75)
    df_prophet.fit(df_site)
    
    df_forecast = df_prophet.make_future_dataframe(periods=450 * 1, freq='D')
    df_forecast = df_prophet.predict(df_forecast)
    
    df_site.set_index('ds', inplace=True)
    df_forecast.set_index('ds', inplace=True)

    site_data_from_sql = pd.DataFrame(site_data_from_sql)

    site_data_from_sql.set_index('datetime', inplace=True)

    viz_df = site_data_from_sql.join(df_forecast[['yhat', 'yhat_lower','yhat_upper']], how = 'outer')

    viz_df['ds'] = viz_df.index
    viz_df['yhat_rescaled'] = np.exp(viz_df['yhat'])
    viz_df['yhat_upper_rescaled'] = np.exp(viz_df['yhat_upper'])
    viz_df['yhat_lower_rescaled'] = np.exp(viz_df['yhat_lower'])

    viz_df.to_sql("n"+str(site)+"_forecast", engine, if_exists='replace')
