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

def pollFirebase(startAt):
    fb = firebase.FirebaseApplication(config.firebase_url, None)
    try:
        trackPoints = fb.get('/', config.firebase_key,  params = { 'orderBy': '"$key"', 'startAt': '"' + str(startAt) + '"' })
        sortedKeys = sorted(trackPoints, key=lambda key: int(key)) # maybe nosql wasn't such a good idea after all
        return sortedKeys,trackPoints
    except:
        return [], {}

app = Flask(__name__)

lastPollTimestamp = 0;
trackStartTime = None

@app.route("/initialize")
def initialize():
    return app.send_static_file('initialize.kml')

@app.route("/")
def start():
    global lastPollTimestamp
    global trackStartTime

    sortedKeys,trackPoints = pollFirebase(lastPollTimestamp)
    if(len(sortedKeys) == 0):
        return "", 304

    lastPollTimestamp = int(sortedKeys[-1])

    trackEndTime = None

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

    for timestamp in sortedKeys:

        point = trackPoints[timestamp]

        if(not "gps" in point or not "msg" in point["gps"]):
            continue

        lat = point["gps"]["msg"]["lat"]
        lon = point["gps"]["msg"]["lon"]

        if(not is_number(lat) or not is_number(lon)):
            continue

        date = point["gps"]["msg"]["date"] # 230615
        time = point["gps"]["msg"]["time"] # 22:02:07.000

        gpsTime = datetime.strptime(date + " " + time, "%d%m%y %H:%M:%S.%f")
        if trackStartTime == None:
            trackStartTime = gpsTime
        if trackEndTime == None:
            trackEndTime = gpsTime
        if gpsTime < trackStartTime: # should never happen
            trackStartTime = gpsTime
        if gpsTime > trackEndTime:
            trackEndTime = gpsTime
        when.append(gpsTime.strftime("%Y-%m-%dT%H:%M:%SZ"))

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
            "alt": 300,
            "range": 300,
            "begin": trackStartTime.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "end": trackEndTime.strftime("%Y-%m-%dT%H:%M:%SZ")
        },
        targetHref = request.url_root + "/initialize",
        when = when,
        coords = coords,
        pids = pids,
        pid_data = pid_data
    )


if __name__ == "__main__":
    app.run(debug=True)
