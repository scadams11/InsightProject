#!/Users/cadeadams/anaconda3/bin/python3
from flask import Flask, render_template, flash, request, redirect, url_for
#from flaskexample import app
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
import pandas as pd
import psycopg2
import os

import geopy.distance

from fbprophet import Prophet
import datetime, re, requests
import dateparser

app = Flask(__name__)

##
#Connect to postgre
##
user = 'cadeadams' #add your username here (same as previous postgreSQL)                      
host = 'localhost'
dbname = 'usgs_stream_db_log'
db = create_engine('postgres://%s%s/%s'%(user,host,dbname))
con = None
con = psycopg2.connect(database = dbname, user = user)

##
#Define functions.
##
def calc_nowish():
    now = datetime.datetime.now() + datetime.timedelta(hours=3)
    now = datetime.datetime(now.year, now.month, now.day, now.hour,
                            15*round((float(now.minute) + float(now.second) / 60) // 15))
    now = now.strftime("%m-%d-%Y %H:%M")
    return now

def geocode_location(location):
    query = re.sub(r'\s+', '\+', location+',CO')
    request = f'https://nominatim.openstreetmap.org/search?q={query}&format=json'
    headers = {'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.100 Safari/537.36'}
    res = requests.get(request, headers=headers)
    print(res.status_code)
    if res.status_code == 200:
        try:
            lat = float(res.json()[0]["lat"])
            lon = float(res.json()[0]["lon"])
            return (lat, lon)
        except IndexError:
            return (None, None)
    else:
        return (None, None)

def reload_after_error(error):
    now = calc_nowish()
    return render_template('index.html', now=now, error=error)

##
#Get to the web interface.
##
@app.route('/')
def index():
    now = calc_nowish()
    return render_template("index.html", now = now)

##
#Go to the results.
##
@app.route('/results', methods=['POST'])
def results():
    if request.method == 'POST':
        input_location = request.form.get('location')
        input_date = request.form.get('date')
        t = request.form.get('date')
        t = dateparser.parse(t)
        if t < datetime.datetime.now():
            return reload_after_error("Whoops, looks like you chose a time that's already happened!")
        if t > datetime.datetime.now() + datetime.timedelta(days=365):
            return reload_after_error("Whoops, looks like you chose a time that's too far in the future.")
        location = geocode_location(input_location)
        if location[0] is None:
            return reload_after_error("We can't find that location on the map. Please try again.")
        if (location[0] > 40.95 or location[0] < 36.97 or location[1] < -109.03 or location[1] > -102.00) :
            return reload_after_error("That location isn't in Colorado! Please try again.")

        lat = location[0]
        lon = location[1]

        sql_query = """
                    SELECT * FROM site_locations;
                    """
        query_results = pd.read_sql_query(sql_query,con)

        site_no = query_results["site_no"]
        site_lat = query_results["dec_lat_va"]
        site_long = query_results["dec_long_va"]

        sites_coord = pd.DataFrame([site_no, site_lat, site_long])
        sites_coord = sites_coord.T

        distance = []
        for i in range(len(sites_coord)) :
            distance.append(geopy.distance.distance(location, sites_coord.iloc[i,1:]).miles)

        query_results["distance"] = distance
        site_no = pd.DataFrame(site_no)
        site_no["distance"] = distance
        query_results = query_results.sort_values(by = ["distance"])
        site_no = site_no.sort_values(by = ["distance"])

        count = 0
        loc_lat = list()
        loc_lon = list()
        flow = list()
        flow_upper = list()
        flow_lower = list()
        good_site = list()
        good_site_nm = list()
        good_dist = list()

        for i in range(len(site_no)) :
            sql_query_model = """
                              SELECT * FROM n"""+site_no['site_no'].iloc[i]+"""_forecast;
                              """
            query_results_model = pd.read_sql_query(sql_query_model,con)
            if (t == query_results_model['ds']).any() :
                temp = query_results_model.loc[query_results_model['ds'] == t]
                if (temp['yhat_rescaled'].iloc[0] > 100 and temp['yhat_rescaled'].iloc[0] < 400) :
                    loc_lat.append(float(query_results[i:i+1]["dec_lat_va"]))
                    loc_lon.append(float(query_results[i:i+1]["dec_long_va"]))
                    good_site.append(query_results[i:i+1]["site_no"].iloc[0])
                    good_site_nm.append(query_results[i:i+1]["station_nm"].iloc[0])
                    good_dist.append(query_results[i:i+1]["distance"].iloc[0])
                    flow.append(temp['yhat_rescaled'].iloc[0])
                    flow_upper.append(temp['yhat_upper_rescaled'].iloc[0])
                    flow_lower.append(temp['yhat_lower_rescaled'].iloc[0])
                    count = count + 1
                    if count == 3 :
                        break
            else :
                continue


        loc1_lat = loc_lat[0] #float(query_results[0:1]["dec_lat_va"].iloc[0])
        loc1_lon = loc_lon[0] #float(query_results[0:1]["dec_long_va"].iloc[0])
        location_1 = pd.DataFrame([loc1_lat, loc1_lon])
        loc1_name = good_site_nm[0] #query_results[0:1]["station_nm"].iloc[0]
        loc1_dist = round(good_dist[0])
        loc1_flow = round(flow[0])
        loc1_flow_up = round(flow_upper[0])

        bbox_1_1 = loc1_lon - 0.010
        bbox_1_2 = loc1_lat - 0.010
        bbox_1_3 = loc1_lon + 0.010
        bbox_1_4 = loc1_lat + 0.010
        map_url_1 = f"https://www.openstreetmap.org/export/embed.html?bbox={bbox_1_1}%2C{bbox_1_2}%2C{bbox_1_3}%2C{bbox_1_4}&amp;layer=mapquest&amp;marker={loc1_lat}%2C{loc1_lon}"

        loc2_lat = loc_lat[1] #float(query_results[1:2]["dec_lat_va"].iloc[0])
        loc2_lon = loc_lon[1] #float(query_results[1:2]["dec_long_va"].iloc[0])
        location_2 = pd.DataFrame([loc1_lat, loc1_lon])
        loc2_name = good_site_nm[1] #query_results[1:2]["station_nm"].iloc[0]
        loc2_dist = round(good_dist[1])
        loc2_flow = round(flow[1])
        loc2_flow_up = round(flow_upper[1])

        bbox_2_1 = loc2_lon - 0.010
        bbox_2_2 = loc2_lat - 0.010
        bbox_2_3 = loc2_lon + 0.010
        bbox_2_4 = loc2_lat + 0.010
        map_url_2 = f"https://www.openstreetmap.org/export/embed.html?bbox={bbox_2_1}%2C{bbox_2_2}%2C{bbox_2_3}%2C{bbox_2_4}&amp;layer=mapnik&amp;marker={loc2_lat}%2C{loc2_lon}"

        loc3_lat = loc_lat[2] #float(query_results[2:3]["dec_lat_va"].iloc[0])
        loc3_lon = loc_lon[2] #float(query_results[2:3]["dec_long_va"].iloc[0])
        location_3 = pd.DataFrame([loc3_lat, loc3_lon])
        loc3_name = good_site_nm[2] #query_results[2:3]["station_nm"].iloc[0]
        loc3_dist = round(good_dist[2])
        loc3_flow = round(flow[2])
        loc3_flow_up = round(flow_upper[2])

        bbox_3_1 = loc3_lon - 0.010
        bbox_3_2 = loc3_lat - 0.010
        bbox_3_3 = loc3_lon + 0.010
        bbox_3_4 = loc3_lat + 0.010
        map_url_3 = f"https://www.openstreetmap.org/export/embed.html?bbox={bbox_3_1}%2C{bbox_3_2}%2C{bbox_3_3}%2C{bbox_3_4}&amp;layer=mapnik&amp;marker={loc3_lat}%2C{loc3_lon}"

    return render_template('results.html',
                           location=input_location,
                           date=input_date,
                           map_url_1=map_url_1,
                           map_url_2=map_url_2,
                           map_url_3=map_url_3, 
                           loc1_name=loc1_name,
                           loc2_name=loc2_name,
                           loc3_name=loc3_name,
                           loc1_dist=loc1_dist,
                           loc2_dist=loc2_dist,
                           loc3_dist=loc3_dist,
                           loc1_flow=loc1_flow, 
                           loc2_flow=loc2_flow, 
                           loc3_flow=loc3_flow, 
                           loc1_flow_up=loc1_flow_up, 
                           loc2_flow_up=loc2_flow_up,
                           loc3_flow_up=loc3_flow_up)


if __name__ == "__main__":
#    args = initialize_params()
#    pg, ds_key = import_secrets(os.path.expanduser(args.ini_path))
    app.run(host='0.0.0.0', debug=False)
