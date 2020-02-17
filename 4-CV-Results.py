import pandas as pd
import numpy as np

import psycopg2

def mean_absolute_percentage_error(y_true, y_pred):
    y_true, y_pred = np.array(y_true), np.array(y_pred)
    return np.mean(np.abs((y_true - y_pred) / y_true)) * 100

username = 'cadeadams'
dbname = 'usgs_stream_db_log'

engine = create_engine('postgres://%s@localhost/%s'%(username,dbname))
if not database_exists(engine.url):
    create_database(engine.url)

con = None
con = psycopg2.connect(database = dbname, user = username)

cross_val_all = pd.DataFrame()

file = '~/InsightProject/EDAandVIS/Gage_sites.txt'

sites_cv = pd.read_csv(file, sep = '\t', header = 39, skiprows = [40], dtype = {"site_no" : "str"})

##Removes sites with no data for past 20 years.
sites_cv = sites_cv.drop([65, 71, 77, 117, 118, 138, 203, 225, 320, 330, 331, 338])
sites_cv = sites_cv.reset_index(drop = True)

##Removes data that is unable to be cross validated due to too few observations.
sites_cv = sites_cv.drop([18, 83, 84, 85, 89, 92, 101, 103, 104, 136, 138, 146, 148, 149, 150, 151, 179, 208, 209, 224, 228, 231, 236, 293, 314])
sites_cv = sites_cv.reset_index(drop = True)

site_no_cv = list(sites_cv["site_no"])
site_nm_cv = list(sites_cv["station_nm"])
site_ele_cv = list(sites_cv["alt_va"])

cross_val_all["site_no"] = site_no_cv

mae_baseline = []
mae_model = []
mape_baseline = list()
mape_model = list()
for site in site_no_cv :
    sql_query = """
                SELECT * FROM n"""+site+"""_cv;
                """
    site_cv_from_sql = pd.read_sql_query(sql_query,con)
    site_cv_from_sql['mean'] = pd.Series([0 for x in range(len(site_cv_from_sql.index))], index=site_cv_from_sql.index)
    site_cv_from_sql['mean'] = np.mean(site_cv_from_sql['y_rescaled'])
    mae_baseline.append(mean_absolute_error(site_cv_from_sql['y_rescaled'], site_cv_from_sql['mean']))
    mae_model.append(mean_absolute_error(site_cv_from_sql['y_rescaled'], site_cv_from_sql['yhat_rescaled']))
    mape_baseline.append(mean_absolute_percentage_error(site_cv_from_sql['y_rescaled'], site_cv_from_sql['mean']))
    mape_model.append(mean_absolute_percentage_error(site_cv_from_sql['y_rescaled'], site_cv_from_sql['yhat_rescaled']))

cross_val_all["mae_baseline"] = mae_baseline
cross_val_all["mae_model"] = mae_model
cross_val_all["mae_improvement"] = mae_baseline / mae_model
cross_val_all["mape_baseline"] = mape_baseline
cross_val_all["mape_model"] = mape_model
cross_val_all["mape_improvement"] = mape_baseline / mape_model
cross_val_all["elevation"] = site_ele_cv

cross_val_all.to_sql("cross_val_all", engine, if_exists='replace')
