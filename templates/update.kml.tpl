<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2" xmlns:gx="http://www.google.com/kml/ext/2.2">
  <NetworkLinkControl>
    <LookAt>
      <longitude>{{lookAt.lon}}</longitude>
      <latitude>{{lookAt.lat}}</latitude>
      <altitude>{{lookAt.alt}}</altitude>
      <range>{{lookAt.range}}</range>
      <gx:TimeSpan id="time_1">
        <begin>{{lookAt.begin}}</begin>
        <end>{{lookAt.end}}</end>
      </gx:TimeSpan>
    </LookAt>
    <Update>
      <targetHref>{{targetHref}}</targetHref>
      <Change>
        <gx:Track targetId="obdtrack">
        {% for w in when %}
          <when>{{w}}</when>
        {% endfor %}
        {% for c in coords %}
          <gx:coord>{{c[0]}} {{c[1]}} {{c[2]}}</gx:coord>
        {% endfor %}
        </gx:Track>
      </Change>
    {% for pid in pids %}
      <Change>
        <gx:SimpleArrayData targetId="{{pid.replace(" ", "_")}}">
        {% for data in pid_data[pid] %}
          <gx:value>{{data}}</gx:value>
        {% endfor %}
        </gx:SimpleArrayData>
      </Change>
    {% endfor %}
    </Update>
  </NetworkLinkControl>
</kml>
