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
dbname = 'usgs_stream_db'
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
    query = re.sub(r'\s+', '\+', location+', CO')
    request = f'https://nominatim.openstreetmap.org/search?q={query}&format=json'
    res = requests.get(request)
    if res.status_code == 200:
        lat = float(res.json()[0]['lat'])
        lon = float(res.json()[0]['lon'])
        return (lat, lon)
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
        t = request.form.get('date')
        t = dateparser.parse(t)
        if t < datetime.datetime.now():
            return reload_after_error("Whoops, looks like you chose a time that's already happened!")
        if t > datetime.datetime.now() + datetime.timedelta(days=365):
            return reload_after_error("Whoops, looks like you chose a time that's too far in the future.")
        location = geocode_location(input_location)
        if location[0] is None:
            return reload_after_error("Whoops, looks like we can't find that location on the map. Please try again.")
#        area = loc_to_area(location)
        if (location[0] > 40.95 or location[0] < 36.97 or location[1] < -109.03 or location[1] > -102.00) :
            return reload_after_error("Whoops, looks like that location isn't in Colorado! Please try again.")

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
        query_results = query_results.sort_values(by = ["distance"])

        loc1_lat = float(query_results[0:1]["dec_lat_va"])
        loc1_lon = float(query_results[0:1]["dec_long_va"])
        location_1 = pd.DataFrame([loc1_lat, loc1_lon])

        bbox_1 = loc1_lon - 0.036
        bbox_2 = loc1_lat - 0.036
        bbox_3 = loc1_lon + 0.036
        bbox_4 = loc1_lat + 0.036
        map_url = f"https://www.openstreetmap.org/export/embed.html?bbox={bbox_1}%2C{bbox_2}%2C{bbox_3}%2C{bbox_4}&amp;layer=mapnik&amp;marker={loc1_lat}%2C{loc1_lon}"

    return render_template('results.html',
                           location=input_location,
                           time=t,
                           map_url=map_url)

##
#For pulling stream information based off input location.
##
#@app.route('/db')
#def stream_page():
#    sql_query = """                                                                       
#                SELECT * FROM n"""+site_no[i]""";
#                """
#    query_results = pd.read_sql_query(sql_query,con)
#    streams = ""
#    for i in range(0,10):
#        streams += query_results.iloc[i]['birth_month']
#        streams += "<br>"
#    return streams

#@app.route('/input')
#def cesareans_input():
#    return render_template("input.html")

#@app.route('/output')
#def locations_output():
#  #pull 'location' from input field and store it
#  input_location = request.args.get('location')
#    #just select the nearest stream sites from the input location from the front page.
#  query_sites = "SELECT * FROM site_locations WHERE distance='%s'" % input_location
#  print(query_sites)
#  query_results=pd.read_sql_query(query_sites,con)
#  print(query_results)
#  near_locations = []
#  for i in range(0,query_results.shape[0]):
#      near_locations.append(dict(index=query_results.iloc[i]['index'], distance=query_results.iloc[i]['distance']))
#      return render_template("output.html", near_locations = near_locations)

if __name__ == "__main__":
#    args = initialize_params()
#    pg, ds_key = import_secrets(os.path.expanduser(args.ini_path))
    app.run(host='0.0.0.0', debug=False)
