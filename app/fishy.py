#!/Users/cadeadams/anaconda3/bin/python3
from flask import Flask, render_template, flash, request, redirect, url_for
#from flaskexample import app
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
import pandas as pd
import psycopg2
import os


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
#        if area is None:
#            return reload_after_error("Whoops, looks like that location isn't in Colorado! Please try again.")

        lat = location[0]
        lon = location[1]
        bbox_1 = lon - 0.036
        bbox_2 = lat - 0.036
        bbox_3 = lon + 0.036
        bbox_4 = lat + 0.036
        map_url = f"https://www.openstreetmap.org/export/embed.html?bbox={bbox_1}%2C{bbox_2}%2C{bbox_3}%2C{bbox_4}&amp;layer=mapnik&amp;marker={lat}%2C{lon}"

    return render_template('results.html',
                           location=input_location,
                           time=t,
                           map_url=map_url)



@app.route('/db')
def stream_page():
    sql_query = """                                                                       
                SELECT * FROM n"""+site_no[i]""";
                """
    query_results = pd.read_sql_query(sql_query,con)
    streams = ""
    for i in range(0,10):
        streams += query_results.iloc[i]['birth_month']
        streams += "<br>"
    return streams

#@app.route('/input')
#def cesareans_input():
#    return render_template("input.html")

#@app.route('/output')
#def cesareans_output():
#  #pull 'birth_month' from input field and store it
#  patient = request.args.get('birth_month')
#    #just select the Cesareans  from the birth dtabase for the month that the user inputs
#  query = "SELECT index, attendant, birth_month FROM birth_data_table WHERE delivery_method='Cesarean' AND birth_month='%s'" % patient
#  print(query)
#  query_results=pd.read_sql_query(query,con)
#  print(query_results)
#  births = []
#  for i in range(0,query_results.shape[0]):
#      births.append(dict(index=query_results.iloc[i]['index'], attendant=query_results.iloc[i]['attendant'], birth_month=query_results.iloc[i]['birth_month']))
#      the_result = ModelIt(patient,births)
#      return render_template("output.html", births = births, the_result = the_result)

if __name__ == "__main__":
#    args = initialize_params()
#    pg, ds_key = import_secrets(os.path.expanduser(args.ini_path))
    app.run(host='0.0.0.0', debug=False)
