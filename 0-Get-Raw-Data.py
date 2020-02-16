import pandas as pd
import numpy as np

import hydrofunctions as hf

from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database

## Reading in site data from 'Gage_sites.txt'
file = '~/InsightProject/EDAandVIS/Gage_sites.txt'
sites = pd.read_csv(file, sep = '\t', header = 39, skiprows = [40], dtype = {"site_no" : "str"})

##Removes sites with no data for past 20 years. (12 sites)
sites = sites.drop([65, 71, 77, 117, 118, 138, 203, 225, 320, 330, 331, 338])
sites = sites.reset_index(drop = True)

##Removes data that is unable to be cross validated due to too few observations. (25 sites)
sites = sites.drop([18, 83, 84, 85, 89, 92, 101, 103, 104, 136, 138, 146, 148, 149, 150, 151, 179, 208, 209, 224, 228, 231, 236, 293, 314])
sites = sites.reset_index(drop = True)

site_no = list(sites["site_no"])
site_nm = list(sites["station_nm"])
site_loc = sites.filter(['site_no', 'station_nm', 'dec_lat_va', 'dec_long_va'])

##Access PostgreSQL database to store data.
username = 'cadeadams'
dbname = 'usgs_stream_db_log'
engine = create_engine('postgres://%s@localhost/%s'%(username,dbname))

if not database_exists(engine.url):
    create_database(engine.url)

site_loc.to_sql('site_locations', engine, if_exists='replace')

##
# Pulling in data using hydrofunctions and saving to PostgreSQL database.
##
start = '2000-01-01'
end = str(datetime.datetime.today().strftime('%Y-%m-%d')) #Gets today's date.

for site in site_no :
    usgs_site = hf.NWIS(site, 'dv', start, end)
    usgs_site.get_data()
    usgs_dict = usgs_site.json()
    df = hf.extract_nwis_df(usgs_dict)

#   Need to rename columns to "y" and "ds" for FBProphet later.
#   I also rename the flag columns to "flags" for better documentation.
    df.rename(index=str, columns = {"USGS:"+site+":00060:00003" : "y", 
                                    "USGS:"+site+":00060:00003_qualifiers" : "flags"}, 
             inplace = True)

#   The index is the datetime for each observation. I add a "ds" column using the index.
    df['ds'] = df.index[:]
    df['ds'].str.split(pat = ' ', expand = True)

#   I add in all sites to the PostgreSQL database.
    df.to_sql("n"+str(site), engine, if_exists='replace')
