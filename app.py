import numpy as np
import pandas as pd
import datetime as dt

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

from flask import Flask, jsonify




#---------------Database Setup-------------------

engine = create_engine("sqlite:///Resources/hawaii.sqlite")

Base = automap_base()

Base.prepare(engine, reflect=True)

measurement = Base.classes.measurement
Station = Base.classes.station


#----------------Flask Setup--------------------
app = Flask(__name__)

# Grabbing most recent entry and saving the date one year prior
session = Session(engine)

most_recent_date = session.query(measurement).order_by(measurement.date.desc()).first()
most_recent_date = pd.to_datetime(most_recent_date.date, format='%Y-%m-%d')

last_year = most_recent_date - dt.timedelta(days=365)
last_year = last_year.strftime('%Y-%m-%d')

session.close()

#---------------Flask Routes--------------------


@app.route("/")
def Home():
    """List all available api routes."""
    return(
        f"Available Routes:<br/>"
        f"<a href='/api/v1.0/precipitation'>/api/v1.0/precipitation</a><br/>"
        f"<a href='/api/v1.0/stations'>/api/v1.0/stations<a/><br/>"
        f"<a href='/api/v1.0/tobs'>/api/v1.0/tobs<a/><br/>"
        f"/api/v1.0/start<br/>"
        f"/api/v1.0/start/end <br/>"
    )


@app.route("/api/v1.0/precipitation")
def Precipitation():
    # Create our session (link) from Python to the DB
    session = Session(engine)
    # Query the DB
    results = session.query(measurement.date, measurement.prcp).filter(measurement.date > last_year).all()
    # close the session
    session.close()

    prcp_data = []
    for item in results:
        prcp_dict = {}
        prcp_dict[item.date] = item.prcp
        prcp_data.append(prcp_dict)

    return jsonify(prcp_data)


@app.route("/api/v1.0/stations")
def Stations():
    # Create our session (link) from Python to the DB
    session = Session(engine)
    # Query the DB
    results = session.query(Station)
    # close the session
    session.close()

    # Create a dictionary from the row data 
    stations = []
    for station in results:
        station_dict = {}
        station_dict["station"] = station.station
        station_dict["name"] = station.name
        station_dict["latitude"] = station.latitude
        station_dict["longitude"] = station.longitude
        station_dict["elevation"] = station.elevation
        stations.append(station_dict)
    
    return jsonify(stations)


@app.route("/api/v1.0/tobs")
def Tobs():
    # Create our session (link) from Python to the DB
    session = Session(engine)
    # Query the DB
    most_active_station = session.query(measurement.station, func.count(measurement.station)).\
            group_by(measurement.station).\
            order_by(func.count(measurement.station).desc()).first()

    results = session.query(measurement.date, measurement.tobs).\
            filter(measurement.date > last_year).filter(measurement.station == most_active_station.station).all()

    # close the session
    session.close()

    temp_data = []
    for item in results:
        temp_dict = {}
        temp_dict[item.date] = item.tobs
        temp_data.append(temp_dict)

    return jsonify(temp_data)


@app.route("/api/v1.0/<start_date>")
def AfterDate(start_date):
    # Create our session (link) from Python to the DB
    session = Session(engine)
    # Query the DB
    try:
        results = session.query(func.min(measurement.tobs), func.max(measurement.tobs), func.avg(measurement.tobs)).filter(measurement.date >= start_date).all()
        session.close()
        summary_data = [{
            "Low" : results[0][0],
            "High" : results[0][1],
            "Avg" : round(results[0][2], 2)
        }]
        return jsonify(summary_data)
    except:
        session.close()
        return "Sorry, a record for that date could not be found."


@app.route("/api/v1.0/<start_date>/<end_date>")
def DateRange(start_date, end_date):
    # Create our session (link) from Python to the DB
    session = Session(engine)
    # Query the DB
    try:
        results = session.query(func.min(measurement.tobs),func.max(measurement.tobs), func.avg(measurement.tobs)).\
            filter(measurement.date >= start_date).\
            filter(measurement.date <= end_date).all()
        summary_data = [{
            "Low" : results[0][0],
            "High" : results[0][1],
            "Avg" : round(results[0][2], 2)
        }]
        session.close()
        return jsonify(summary_data)
    except:
        session.close()
        return "Sorry, a record for that date could not be found."


if __name__ == '__main__':
    app.run(debug=True)