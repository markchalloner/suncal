#!/usr/bin/env python
# -*- coding: utf8 -*-
"""
SUNRISET.C - computes Sun rise/set times, start/end of twilight, and
             the length of the day at any date and latitude

Written as DAYLEN.C, 1989-08-16

Modified to SUNRISET.C, 1992-12-01

(c) Paul Schlyter, 1989, 1992

Released to the public domain by Paul Schlyter, December 1992

Direct conversion to Java
Sean Russell <ser@germane-software.com>

Conversion to Python Class, 2002-03-21
Henrik Härkönen <radix@kortis.to>

Solar Altitude added by Miguel Tremblay 2005-01-16
Solar flux, equation of time and import of python library
  added by Miguel Tremblay 2007-11-22


2007-12-12 - v1.5 by Miguel Tremblay: bug fix to solar flux calculation
"""

__all__ = ['SUN_PY_VERSION', 'Sun']

SUN_PY_VERSION = 1.5

import math
import calendar


class Sun:

    # Following are some macros around the "workhorse" function __daylen
    # They mainly fill in the desired values for the reference altitude
    # below the horizon, and also selects whether this altitude should
    # refer to the Sun's center or its upper limb.

    @classmethod
    def dayLength(cls, year, month, day, lon, lat):
        """
        This macro computes the length of the day, from sunrise to sunset.
        Sunrise/set is considered to occur when the Sun's upper limb is
        35 arc minutes below the horizon (this accounts for the refraction
        of the Earth's atmosphere).
        """
        return cls.__daylen(year, month, day, lon, lat, -35.0 / 60.0, 1)

    @classmethod
    def dayCivilTwilightLength(cls, year, month, day, lon, lat):
        """
        This macro computes the length of the day, including civil twilight.
        Civil twilight starts/ends when the Sun's center is 6 degrees below
        the horizon.
        """
        return cls.__daylen(year, month, day, lon, lat, -6.0, 0)

    @classmethod
    def dayNauticalTwilightLength(cls, year, month, day, lon, lat):
        """
        This macro computes the length of the day, incl. nautical twilight.
        Nautical twilight starts/ends when the Sun's center is 12 degrees
        below the horizon.
        """
        return cls.__daylen(year, month, day, lon, lat, -12.0, 0)

    @classmethod
    def dayAstronomicalTwilightLength(cls, year, month, day, lon, lat):
        """
        This macro computes the length of the day, incl. astronomical twilight.
        Astronomical twilight starts/ends when the Sun's center is 18 degrees
        below the horizon.
        """
        return cls.__daylen(year, month, day, lon, lat, -18.0, 0)

    @classmethod
    def sunRiseSet(cls, year, month, day, lon, lat):
        """
        This macro computes times for sunrise/sunset.
        Sunrise/set is considered to occur when the Sun's upper limb is
        35 arc minutes below the horizon (this accounts for the refraction
        of the Earth's atmosphere).
        """
        return cls.__sunriset(year, month, day, lon, lat, -35.0 / 60.0, 1)

    @classmethod
    def aviationTime(cls, year, month, day, lon, lat):
        """
        This macro computes the start and end times as considered by UK law.
        First launch is 30 minutes before sunrise and last landing is 30
        minutes after sunset.
        """
        r, s = cls.__sunriset(year, month, day, lon, lat, -35.0 / 60.0, 1)
        return r - 0.5, s + 0.5

    @classmethod
    def civilTwilight(cls, year, month, day, lon, lat):
        """
        This macro computes the start and end times of civil twilight.
        Civil twilight starts/ends when the Sun's center is 6 degrees below
        the horizon.
        """
        return cls.__sunriset(year, month, day, lon, lat, -6.0, 0)

    @classmethod
    def nauticalTwilight(cls, year, month, day, lon, lat):
        """
        This macro computes the start and end times of nautical twilight.
        Nautical twilight starts/ends when the Sun's center is 12 degrees
        below the horizon.
        """
        return cls.__sunriset(year, month, day, lon, lat, -12.0, 0)

    @classmethod
    def astronomicalTwilight(cls, year, month, day, lon, lat):
        """
        This macro computes the start and end times of astronomical twilight.
        Astronomical twilight starts/ends when the Sun's center is 18 degrees
        below the horizon.
        """
        return cls.__sunriset(year, month, day, lon, lat, -18.0, 0)

    # The "workhorse" function for sun rise/set times
    @classmethod
    def __sunriset(cls, year, month, day, lon, lat, altit, upper_limb):
        """
        Note: year,month,date = calendar date, 1801-2099 only.
              Eastern longitude positive, Western longitude negative
              Northern latitude positive, Southern latitude negative
              The longitude value IS critical in this function!
              altit = the altitude which the Sun should cross
                      Set to -35/60 degrees for rise/set, -6 degrees
                      for civil, -12 degrees for nautical and -18
                      degrees for astronomical twilight.
                upper_limb: non-zero -> upper limb, zero -> center
                      Set to non-zero (e.g. 1) when computing rise/set
                      times, and to zero when computing start/end of
                      twilight.
              *rise = where to store the rise time
              *set  = where to store the set  time
                      Both times are relative to the specified altitude,
                      and thus this function can be used to compute
                      various twilight times, as well as rise/set times
        Return value:  0 = sun rises/sets this day, times stored at
                           *trise and *tset.
                      +1 = sun above the specified 'horizon' 24 hours.
                           *trise set to time when the sun is at south,
                           minus 12 hours while *tset is set to the south
                           time plus 12 hours. 'Day' length = 24 hours
                      -1 = sun is below the specified 'horizon' 24 hours
                           'Day' length = 0 hours, *trise and *tset are
                            both set to the time when the sun is at south.
        """
        # Compute d of 12h local mean solar time
        d = cls.__daysSince2000Jan0(year, month, day) + 0.5 - (lon / 360.0)

        # Compute local sidereal time of this moment
        sidtime = cls.__revolution(cls.__GMST0(d) + 180.0 + lon)

        # Compute Sun's RA + Decl at this moment
        sRA, sdec, sr = cls.__sunRADec(d)

        # Compute time when Sun is at south - in hours UT
        tsouth = 12.0 - cls.__rev180(sidtime - sRA) / 15.0

        # Compute the Sun's apparent radius, degrees
        sradius = 0.2666 / sr

        # Do correction to upper limb, if necessary
        if upper_limb:
            altit = altit - sradius

        # Compute the diurnal arc that the Sun traverses to reach
        # the specified altitude altit:

        cost = (cls.__sind(altit) - cls.__sind(lat) * cls.__sind(sdec)) / \
               (cls.__cosd(lat) * cls.__cosd(sdec))

        if cost >= 1.0:
            t = 0.0           # Sun always below altit
        elif cost <= -1.0:
            t = 12.0         # Sun always above altit
        else:
            t = cls.__acosd(cost) / 15.0   # The diurnal arc, hours

        # Store rise and set times - in hours UT
        return (tsouth - t, tsouth + t)

    @classmethod
    def __daylen(cls, year, month, day, lon, lat, altit, upper_limb):
        """
        Note: year,month,date = calendar date, 1801-2099 only.
              Eastern longitude positive, Western longitude negative
              Northern latitude positive, Southern latitude negative
              The longitude value is not critical. Set it to the correct
              longitude if you're picky, otherwise set to, say, 0.0
              The latitude however IS critical - be sure to get it correct
              altit = the altitude which the Sun should cross
                      Set to -35/60 degrees for rise/set, -6 degrees
                      for civil, -12 degrees for nautical and -18
                      degrees for astronomical twilight.
                upper_limb: non-zero -> upper limb, zero -> center
                      Set to non-zero (e.g. 1) when computing day length
                      and to zero when computing day+twilight length.

        """

        # Compute d of 12h local mean solar time
        d = cls.__daysSince2000Jan0(year, month, day) + 0.5 - lon / 360.0

        # Compute obliquity of ecliptic (inclination of Earth's axis)
        obl_ecl = 23.4393 - 3.563E-7 * d

        # Compute Sun's position
        slon, sr = cls.__sunpos(d)

        # Compute sine and cosine of Sun's declination
        sin_sdecl = cls.__sind(obl_ecl) * cls.__sind(slon)
        cos_sdecl = math.sqrt(1.0 - sin_sdecl * sin_sdecl)

        # Compute the Sun's apparent radius, degrees
        sradius = 0.2666 / sr

        # Do correction to upper limb, if necessary
        if upper_limb:
            altit = altit - sradius

        cost = (cls.__sind(altit) - cls.__sind(lat) * sin_sdecl) / \
               (cls.__cosd(lat) * cos_sdecl)
        if cost >= 1.0:
            return 0.0             # Sun always below altit

        elif cost <= -1.0:
            return 24.0      # Sun always above altit

        else:
            return 2.0 / 15.0 * cls.__acosd(cost)     # The diurnal arc, hours

    @classmethod
    def __sunpos(cls, d):
        """
        Computes the Sun's ecliptic longitude and distance
        at an instant given in d, number of days since
        2000 Jan 0.0.  The Sun's ecliptic latitude is not
        computed, since it's always very near 0.
        """

        # Compute mean elements
        M = cls.__revolution(356.0470 + 0.9856002585 * d)
        w = 282.9404 + 4.70935e-5 * d
        e = 0.016709 - 1.151e-9 * d

        # Compute true longitude and radius vector
        E = M + math.degrees(e) * cls.__sind(M) * (1.0 + e * cls.__cosd(M))
        x = cls.__cosd(E) - e
        y = math.sqrt(1.0 - e * e) * cls.__sind(E)
        r = math.hypot(x, y)               # Solar distance
        v = cls.__atan2d(y, x)              # True anomaly
        lon = v + w                        # True solar longitude
        if lon >= 360.0:
            lon -= 360.0   # Make it 0..360 degrees

        return lon, r

    @classmethod
    def __sunRADec(cls, d):
        """
        Returns the angle of the Sun (RA)
        the declination (dec) and the distance of the Sun (r)
        for a given day d.
        """

        # Compute Sun's ecliptical coordinates
        lon, r = cls.__sunpos(d)

        # Compute ecliptic rectangular coordinates (z=0)
        x = r * cls.__cosd(lon)
        y = r * cls.__sind(lon)

        # Compute obliquity of ecliptic (inclination of Earth's axis)
        obl_ecl = 23.4393 - 3.563e-7 * d

        # Convert to equatorial rectangular coordinates - x is unchanged
        z = y * cls.__sind(obl_ecl)
        y = y * cls.__cosd(obl_ecl)

        # Convert to spherical coordinates
        return cls.__atan2d(y, x), cls.__atan2d(z, math.hypot(x, y)), r

    @staticmethod
    def __revolution(x):
        """
        This function reduces any angle to within the first revolution
        by subtracting or adding even multiples of 360.0 until the
        result is >= 0.0 and < 360.0

        Reduce angle to within 0..360 degrees
        """
        return x - 360.0 * math.floor(x / 360.0)

    @staticmethod
    def __rev180(x):
        """Reduce angle to within +180..+180 degrees."""
        return x - 360.0 * math.floor(x / 360.0 + 0.5)

    @classmethod
    def __GMST0(cls, d):
        """
        This function computes GMST0, the Greenwich Mean Sidereal Time
        at 0h UT (i.e. the sidereal time at the Greenwich meridian at
        0h UT).  GMST is then the sidereal time at Greenwich at any
        time of the day.  I've generalized GMST0 as well, and define it
        as:  GMST0 = GMST - UT  --  this allows GMST0 to be computed at
        other times than 0h UT as well.  While this sounds somewhat
        contradictory, it is very practical:  instead of computing
        GMST like:

         GMST = (GMST0) + UT * (366.2422/365.2422)

        where (GMST0) is the GMST last time UT was 0 hours, one simply
        computes:

         GMST = GMST0 + UT

        where GMST0 is the GMST "at 0h UT" but at the current moment!
        Defined in this way, GMST0 will increase with about 4 min a
        day.  It also happens that GMST0 (in degrees, 1 hr = 15 degr)
        is equal to the Sun's mean longitude plus/minus 180 degrees!
        (if we neglect aberration, which amounts to 20 seconds of arc
        or 1.33 seconds of time)
        """
        # Sidtime at 0h UT = L (Sun's mean longitude) + 180.0 degr
        # L = M + w, as defined in sunpos().  Since I'm too lazy to
        # add these numbers, I'll let the C compiler do it for me.
        # Any decent C compiler will add the constants at compile
        # time, imposing no runtime or code overhead.

        return cls.__revolution(180.0 + 356.0470 + 282.9404 +
                              (0.9856002585 + 4.70935E-5) * d)

    @classmethod
    def __solar_altitude(cls, latitude, year, month, day):
        """
        Compute the altitude of the sun. No atmospherical refraction taken
        in account.
        Altitude of the southern hemisphere are given relative to
        true north.
        Altitude of the northern hemisphere are given relative to
        true south.
        Declination is between 23.5° North and 23.5° South depending
        on the period of the year.
        Source of formula for altitude is PhysicalGeography.net
        http://www.physicalgeography.net/fundamentals/6h.html
        """
        # Compute declination
        N = cls.__daysSince2000Jan0(year, month, day)
        sRA, dec, sr = cls.__sunRADec(N)

        # Compute the altitude
        altitude = 90.0 - latitude + dec

        # In the tropical and in extreme latitude, values over 90 may occur.
        if altitude > 90:
            return 180 - altitude
        if altitude < 0:
            return 0
        return altitude

    @classmethod
    def __get_max_solar_flux(cls, latitude, year, month, day):
        """
        Compute the maximal solar flux to reach the ground for this date and
        latitude.
        Originally comes from Environment Canada weather forecast model.
        Information was of the public domain on release by Environment Canada
        Output is in W/M^2.
        """

        fEot, fR0r, tDeclsc = cls.__equation_of_time(year, month, day, latitude)
        fSF = (tDeclsc[0] + tDeclsc[1]) * fR0r

        # In the case of a negative declination, solar flux is null
        if fSF < 0:
            fCoeff = 0
        else:
            fCoeff = -1.56e-12 * fSF ** 4 + 5.972e-9 * fSF ** 3 - \
                      8.364e-6 * fSF ** 2 + 5.183e-3 * fSF - 0.435

        fSFT = fSF * fCoeff

        if fSFT < 0:
            fSFT = 0

        return fSFT

    @classmethod
    def __equation_of_time(cls, year, month, day, latitude):
        """
        Description: Subroutine computing the part of the equation of time
                     needed in the computing of the theoretical solar flux
                     Correction originating from the CMC GEM model.

        Parameters:  int nTime : cTime for the correction of the time.

        Returns: tuple (double fEot, double fR0r, tuple tDeclsc)
                 dEot: Correction for the equation of time
                 dR0r: Corrected solar constant for the equation of time
                 tDeclsc: Declination
        """
        # Julian date
        nJulianDate = cls.__julian(year, month, day)
        # Check if it is a leap year
        fDivide = 2.0 * math.pi / (calendar.isleap(year) and 366.0 or 365.0)
        # Correction for "equation of time"
        fA = nJulianDate * fDivide
        fR0r = cls.__solcons(fA) * 0.1367e4
        fRdecl = 0.412 * math.cos((nJulianDate + 10.0) * fDivide - math.pi)
        fDeclsc1 = cls.__sind(latitude) * math.sin(fRdecl)
        fDeclsc2 = cls.__cosd(latitude) * math.cos(fRdecl)
        tDeclsc = (fDeclsc1, fDeclsc2)
        # in minutes
        fEot = (0.002733
               - 7.3430 * math.sin(fA)       + 0.55190 * math.cos(fA)
               - 9.4700 * math.sin(2.0 * fA) - 3.02000 * math.cos(2.0 * fA)
               - 0.3289 * math.sin(3.0 * fA) - 0.07581 * math.cos(3.0 * fA)
               - 0.1935 * math.sin(4.0 * fA) - 0.12450 * math.cos(4.0 * fA))
        # Express in fraction of hour, in radians
        fEot = math.radians(fEot * 15.0 / 60.0)

        return fEot, fR0r, tDeclsc

    @staticmethod
    def __solcons(dAlf):
        """
        Name: __solcons

        Parameters: [I] double dAlf: Solar constant to correct the eccentricity

        Returns: double dVar : Variation of the solar constant

        Functions Called: cos, sin

        Description:  Statement function that calculates the variation of the
          solar constant as a function of the julian day. (dAlf, in radians)

        Revision History:
        Author                Date                Reason
        Miguel Tremblay      June 30th 2004
        """

        return 1.0 / (1.0 -
                    9.464e-4 * math.sin(dAlf) - 0.01671 * math.cos(dAlf) -
                    1.489e-4 * math.cos(2.0 * dAlf) -
                    2.917e-5 * math.sin(3.0 * dAlf) -
                    3.438e-4 * math.cos(4.0 * dAlf)) ** 2

    @staticmethod
    def __julian(year, month, day):
        """Return julian day."""
        if calendar.isleap(year): # Bissextil year, 366 days
            lMonth = [0, 31, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335,
                     366]
        else: # Normal year, 365 days
            lMonth = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334,
                     365]

        return lMonth[month - 1] + day

    @staticmethod
    def __daysSince2000Jan0(y, m, d):
        """A macro to compute the number of days elapsed since 2000 Jan 0.0
           (which is equal to 1999 Dec 31, 0h UT)"""
        return 367 * y - 7 * (y + (m + 9) / 12) / 4 + \
               275 * m / 9 + d - 730530

    # The trigonometric functions in degrees
    @staticmethod
    def __sind(x):
        """Returns the sin in degrees"""
        return math.sin(math.radians(x))

    @staticmethod
    def __cosd(x):
        """Returns the cos in degrees"""
        return math.cos(math.radians(x))

    @staticmethod
    def __acosd(x):
        """Returns the arc cos in degrees"""
        return math.degrees(math.acos(x))

    @staticmethod
    def __atan2d(y, x):
        """Returns the atan2 in degrees"""
        return math.degrees(math.atan2(y, x))


if __name__ == "__main__":
#    print Sun.get_max_solar_flux(46.2, 2004, 01, 30)
    print Sun.sunRiseSet(2008, 10, 31, -3.191528, 55.946124)
