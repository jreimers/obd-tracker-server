from flask import Flask
from flask import Response
from flask import request
from flask import render_template

from firebase import firebase
from datetime import datetime
import config # config.py file

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        pass

    try:
        import unicodedata
        unicodedata.numeric(s)
        return True
    except (TypeError, ValueError):
        pass

    return False

def poll_firebase(startAt):
    fb = firebase.FirebaseApplication(config.firebase_url, None)
    try:
        points = fb.get('/', config.firebase_key,  params = { 'orderBy': '"$key"', 'startAt': '"' + str(startAt) + '"' })
        sorted_keys = sorted(points, key=lambda key: int(key)) # maybe nosql wasn't such a good idea after all
        return sorted_keys,points
    except:
        return [], {}



app = Flask(__name__)

lastPoll = 0;
min_time = None
initUrl = None

@app.route("/initialize")
def initialize():
    global initUrl
    initUrl = request.url
    return app.send_static_file('initialize.kml')

@app.route("/")
def start():
    global lastPoll
    global min_time

    sorted_keys,points = poll_firebase(lastPoll)
    if(len(sorted_keys) == 0):
        return "", 304
    lastPoll = int(sorted_keys[-1])


    max_time = None

    when = []
    coords = []

    pids = [
        "speed",
        "rpm",
        "throttle position",
        "air temperature",
        "coolant temperature",
        "fuel pressure",
    ]

    pid_data = {}

    for pid in pids:
        pid_data[pid] = []


    for ts in sorted_keys:
        point = points[ts]
        if(not "gps" in point):
            continue
        if("msg" in point["gps"]):
            lat = point["gps"]["msg"]["lat"]
            lon = point["gps"]["msg"]["lon"]
            if(is_number(lat) and is_number(lon)):
                date = point["gps"]["msg"]["date"] # 230615
                time = point["gps"]["msg"]["time"] # 22:02:07.000

                date_object = datetime.strptime(date + " " + time, "%d%m%y %H:%M:%S.%f")
                if min_time == None:
                    min_time = date_object
                if max_time == None:
                    max_time = date_object
                if date_object < min_time:
                    min_time = date_object
                if date_object > max_time:
                    max_time = date_object
                when.append(date_object.strftime("%Y-%m-%dT%H:%M:%SZ"))

                # convert from seconds to degrees
                lat = float(lat[0:2]) + float(lat[2:len(lat)])/60;
                lon = float(lon[0:3]) + float(lon[3:len(lon)])/60;
                coords.append((-lon, lat, 0.0))

                for pid in pids:
                    if("msg" in point[pid]):
                        pid_data[pid].append(point[pid]["msg"])
    if len(coords) == 0:
        return "", 304

    return render_template("update.kml.tpl",
        lookAt = {
            "lon": coords[0][0],
            "lat": coords[0][1],
            "alt": 100,
            "range": 100,
            "begin": min_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "end": max_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        },
        targetHref = initUrl,
        when = when,
        coords = coords,
        pids = pids,
        pid_data = pid_data
    )


if __name__ == "__main__":
    app.run(debug=True)
