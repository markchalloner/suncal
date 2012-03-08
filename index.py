#!/usr/bin/env python

# -*- coding: iso-8859-1 -*-

"""A mod_python script to output ICS calendar files of sunrise and sunset times
at a given lat/long.

Note: The Sun.py library used seems to follow the long/lat convention, which is
different from the more-commonly used lat/long convention. We attempt to use
lat/long where possible."""

import vobject
from datetime import datetime, timedelta
import calendar
import gzip
import cStringIO
from mod_python import apache


class Suncal:
    """Wrapper class for the Sun class. One useful method which returns a
       string representation of the ICS."""

    def __init__(self, lat, lon, date, days, cal="sunRiseSet"):
        from Sun import Sun
        f = getattr(Sun, cal, Sun.sunRiseSet)
        self.utc = vobject.icalendar.utc
        self.v = vobject.iCalendar()
        self.lat = lat
        self.lon = lon
        self.d = date
        self.d2 = date + timedelta(days=1);
        if cal == "sunRiseSet":
            name = "Sunrise and Sunset times for %fN, %fW"
            start = "Sunrise"
            end = "Sunset"
        elif cal == "civilTwilight":
            name = "Civil dawn and dusk times for %fN, %fW"
            start = "Civil dawn"
            end = "Civil dusk"
        elif cal == "nauticalTwilight":
            name = "Nautical dawn and dusk times for %fN, %fW"
            start = "Nautical dawn"
            end = "Nautical dusk"
        elif cal == "astronomicalTwilight":
            name = "Astronomical dawn and dusk times for %fN, %fW"
            start = "Astronomical dawn"
            end = "Astronomical dusk"
        elif cal == "aviationTime":
            name = "First launch and last landing times for %fN, %fW"
            start = "First launch"
            end = "Last landing"
        elif cal == "dayNightTime":
            name = "Daytime and Nighttime for %fN, %fW"
            start = "Daytime"
            end = "Nightime"
        else:
            name = "Times for %fN, %fW" # but it will error anyway.
            start = "Start"
            end = "End"
        self.v.add('x-wr-calname').value = name % (lat, lon)
        self.v.add('prodid').value = \
            "-//Bruce Duncan//Sunriseset Calendar 1.2//EN"
        self.v.add('description').value = "Show the sunrise and sunset times" \
            + " for a given location for one year from the current date."
        for date in range(days):
            riseTime, setTime = f(self.d.year, self.d.month, self.d.day, lon, lat) # lat/long reversed.
            riseTime2, setTime2 = f(self.d2.year, self.d2.month, self.d2.day, lon, lat) # lat/long reversed.
            if cal == "dayNightTime":
                self.__addPoint(riseTime, (setTime - (1.0 / 3600)) % 24, self.d, self.d, start)
                self.__addPoint(setTime, (riseTime2 - (1.0 / 3600)) % 24, self.d, self.d2, end)
            else:
                riseTime, setTime = f(self.d.year, self.d.month, self.d.day, lon, lat) # lat/long reversed.
                self.__addPoint(riseTime, riseTime, self.d, self.d, start)
                self.__addPoint(setTime, setTime, self.d, self.d, end)
            self.d += timedelta(days=1)
            self.d2 += timedelta(days=1)

    def __addPoint(self, time, time2, date, date2, summary):
        ev = self.v.add('vevent')
        ev.add('summary').value = summary
        ev.add('geo').value = "%f;%f" % (self.lat, self.lon)
        ev.add('dtstamp').value = datetime.utcnow()
        start = ev.add('dtstart')
        end = ev.add('dtend')
        minute = 60 * (time - int(time))
        second = 60 * (minute - int(minute))
        minute2 = 60 * (time2 - int(time2))
        second2 = 60 * (minute2 - int(minute2))
        start.value = datetime(date.year, date.month,
                date.day, int(time), int(minute), int(second),
                tzinfo=self.utc)
        end.value = datetime(date2.year, date2.month,
                date2.day, int(time2), int(minute2), int(second2),
                tzinfo=self.utc)
        ev.add('uid').value = str(calendar.timegm(start.value.timetuple())) \
                + "-1@suncalendar"

    def ical(self):
        return self.v.serialize().replace("\r\n", "\n").strip()

def compressBuf(buf):
    zbuf = cStringIO.StringIO()
    zfile = gzip.GzipFile(mode='wb', fileobj=zbuf)
    zfile.write(buf)
    zfile.close()
    return zbuf.getvalue()

def testAcceptsGzip(req):
    if req.headers_in.has_key('accept-encoding'):
        return (req.headers_in['accept-encoding'].find("gzip") != -1)
    else:
        return False

def index(req):
    """Serve the static index page."""
    req.content_type = "application/xhtml+xml"
    s = """\
<?xml version="1.0" encoding="iso-8859-1"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
  "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
<head>
<meta http-equiv="Content-Style-Type" content="text/css" />
<meta http-equiv="Content-Script-Type" content="text/javascript" />
<title>iCal sunrise and sunset</title>
<script type="text/javascript">
/* <![CDATA[ */
function showLink() {
    document.getElementById('link').href = 'cal?lat=' +
        document.getElementById('lat').value + '&lon=' +
        document.getElementById('lon').value + '&cal=' +
        document.getElementById('cal').value;
    document.getElementById('link').innerHTML = 'iCalendar for &quot;' +
        document.getElementById('cal').options[
            document.getElementById('cal').selectedIndex].innerHTML +
        '&quot; for ' +
        document.getElementById('lat').value + 'N, ' +
        document.getElementById('lon').value + 'W';
    document.getElementById('linkContainer').style.display = 'block';
    return false
}
/* ]]> */
</script>
</head>
<body style="text-align: justify">
<div style="float: right; width: 500px; text-align: right; margin: 1em;
    font-size: small">
<img src="/~bduncan/sunset.jpeg"
    alt="Sunset at Oca&ntilde;a, Spain" style="width: 495px; height: 367px" />
<br />
<p>Sunset taken at Oca&ntilde;a, Spain by Amy Barsby, 2006.
<a rel="license" href="http://creativecommons.org/licenses/by/2.0/uk/">
<img alt="Creative Commons License"
    style="border-width: 0; width: 80px; height: 15px"
    src="http://i.creativecommons.org/l/by/2.0/uk/80x15.png" /></a><br />
</p>
</div>
<h1>Sunset/Sunrise iCalendar</h1>
<p>Enter your lat/long to get an iCal file for one year, from last month, of
sunrise and sunset times. You may change the parameters to show the times for
civil/nautical/astonomical twilight. You should also be able to import the
calendar dynamically into something like
<a href="http://www.google.com/calendar">Google Calendar</a>. No account is
made of altitude. The default location is pretty close to my flat in
Edinburgh.</p>
<form action="cal" method="get">
<p style="margin-left: 2em">
<label for="lat">Latitude (decimal degrees, negative is South):</label>
<input type="text" name="lat" id="lat" value="55.932756" /><br />
<label for="lon">Longitutde (decimal degrees, negative is West):</label>
<input type="text" name="lon" id="lon" value="-3.177664" /><br />
<label for="cal">Type</label>
<select name="cal" id="cal">
<option value="sunRiseSet">Sunrise/sunset</option>
<option value="aviationTime">First launch/last landing</option>
<option value="civilTwilight">Civil dawn/dusk</option>
<option value="nauticalTwilight">Nautical dawn/dusk</option>
<option value="astronomicalTwilight">Astronomical dawn/dusk</option>
<option value="dayNightTime">Daytime/Nighttime</option>
</select><br />
<input type="submit" value="Download .ics" />
<input type="submit" name="URL" value="Show Link"
    onclick="return showLink()" />
</p>
</form>
<p style="display:none; border: dashed 2px red; padding: 5px; margin-left: 2em"
    id="linkContainer">
<a href="cal" id="link">This iCalendar link does not work without javascript
yet...</a></p>
<p>This application was written in <a href="http://www.python.org/">python</a>
by Bruce Duncan in 2008.
It uses the public domain <a href="Sunsource">Sun.py</a> and the
<a href="http://www.apache.org/licenses/LICENSE-1.1">Apache licensed</a>
<a href="http://vobject.skyhouseconsulting.com/">vobject</a> python class (I
used the <a href="http://packages.debian.org/vobject">Debian package</a> for
development).
The <a href="source">source</a> is available under the GPL version 2.
When I wrote this, I was (and still am) working for the
<a href="http://www.see.ed.ac.uk/">University of Edinburgh School of
Engineering<span style="text-decoration: line-through"> and
Electronics</span></a>, but I wrote it in my own time.
I used <a href="http://www.vim.org/">Vim</a>.</p>
<h2>Changes</h2>
<p><b>2010-05-06</b></p>
<p>Fix a couple of bugs introduced by refactoring (changing an argument name
and hiding a required variable in a class).</p>
<p><b>2010-06-23</b></p>
<p>Tidy up the python following pep8 and pylint recommendations (mostly
renaming variables which clash with keywords or builtins like &quot;type&quot;
and &quot;long&quot;). Send data gzip-compressed if possible. Get browsers to
honour filenames when downloading.</p>
<p><b>2009-03-31</b></p>
<p>Times are now output in UTC. This should allow clients to adjust to the
local timezone, especially for DST!</p>
<p><b>2009-12-08</b></p>
<p>Big code cleanup. Fix a presentation bug (&quot;E&quot; instead of
&quot;N&quot;).</p>
<p><b>2009-12-08</b></p>
<p>Add twilight options. Remove promise to store locations. Calendars start
from one month ago.</p>
<p style="text-align: right"><i>Bruce Duncan, &copy; 2008</i>
<a href="http://validator.w3.org/check?uri=referer">
<img src="http://www.w3.org/Icons/valid-xhtml10-blue"
    alt="Valid XHTML 1.0 Strict"
    style="border: none; width: 88px; height: 31px" /></a>
</p>
</body>
</html>
"""
    if testAcceptsGzip(req):
        zbuf = compressBuf(s)
        req.headers_out['Content-Encoding'] = 'gzip'
        req.headers_out['Content-Length'] = str(len(zbuf))
        req.send_http_header()
        req.write(zbuf)
    else:
        req.headers_out['Content-Length'] = str(len(s))
        req.send_http_header()
        req.write(s)
    return apache.OK


def cal(req, lat=None, lon=None, cal=None, long=None, type=None):
    """Use the Suncal class to output a calendar for one year from the current
    date."""
    if lon is None:
        lon = long
    if cal is None:
        cal = type
    if lat is None or lon is None:
        req.status = 302
        req.content_type = 'text/plain'
        req.headers_out['Location'] = '.'
        req.write('Found')
    if cal is None:
        cal = "sunRiseSet"
    req.content_type = "text/calendar"
    d = datetime.today()
    req.headers_out['Content-Disposition'] = \
        'attachment; filename="%s_%s-%s-%s_%02f_%02f.ics"' % (
        cal, d.year, d.month, d.day, float(lat), float(lon))
    k = Suncal(float(lat), float(lon), d - timedelta(days=30), 365, cal)
    s = k.ical()
    if testAcceptsGzip(req):
        zbuf = compressBuf(s)
        req.headers_out['Content-Encoding'] = 'gzip'
        req.headers_out['Content-Length'] = str(len(zbuf))
        req.send_http_header()
        req.write(zbuf)
    else:
        req.headers_out['Content-Length'] = str(len(s))
        req.send_http_header()
        req.write(s)
    return apache.OK


def Sunsource(req):
    """Distribute the Sun module."""
    req.content_type = "application/x-python"
    req.headers_out['Content-Disposition'] = 'attachment; filename="Sun.py"'
    f = open("/var/www/markc/markc.dev.obanmultilingual.com/web/suncal/Sun.py")
    try:
        s = f.read()
    finally:
        f.close()
    if testAcceptsGzip(req):
        zbuf = compressBuf(s)
        req.headers_out['Content-Encoding'] = 'gzip'
        req.headers_out['Content-Length'] = str(len(zbuf))
        req.send_http_header()
        req.write(zbuf)
    else:
        req.headers_out['Content-Length'] = str(len(s))
        req.send_http_header()
        req.write(s)
    return apache.OK


def source(req):
    """Deliver the source. Self-replicating code!"""
    req.content_type = "application/x-python"
    req.headers_out['Content-Disposition'] = 'attachment; filename="Suncalendar.py"'
    f = open("/var/www/markc/markc.dev.obanmultilingual.com/web/suncal/index.py")
    try:
        s = f.read()
    finally:
        f.close()
    if testAcceptsGzip(req):
        zbuf = compressBuf(s)
        req.headers_out['Content-Encoding'] = 'gzip'
        req.headers_out['Content-Length'] = str(len(zbuf))
        req.send_http_header()
        req.write(zbuf)
    else:
        req.headers_out['Content-Length'] = str(len(s))
        req.send_http_header()
        req.write(s)
    return apache.OK


def Suncalendar(req):
    """A hack to redirect calendars installed under a previous version."""
    req.status = 301
    req.content_type = 'text/plain'
    req.headers_out['Location'] = '../Suncalendar'
    req.write("Moved permanently")


if __name__ == "__main__":
    k = Suncal(55.932756, -3.177664,
        datetime.today() - timedelta(days=30), 365)
    print k.ical()
