import json

data = json.load(open("/tmp/downloads/planets.json"))

def whattype(field):
    types = set()
    for x in data:
        types.add(type(x[field]))
    return types

def uniques(field):
    out = set()
    for x in data:
        out.add(x[field])
    return out

from oamap.schema import *

def boolean(doc=None, nullable=False):
    return Primitive("bool_", doc=doc, nullable=nullable)

def integer(doc=None, nullable=False):
    return Primitive("i4", doc=doc, nullable=nullable)

def real(doc=None, nullable=False):
    return Primitive("f8", doc=doc, nullable=nullable)

def string(doc=None, nullable=False):
    return List("u1", name="UTF8String", doc=doc, nullable=nullable)

schema = (
  List(
    Record(
      name = "Star",
      fields = dict(
        name = string("Stellar name most commonly used in the literature"),         # pl_hostname
        update = string("Date of last update of the planet parameters"),            # rowupdate
        ra = real("Right Ascension of the planetary system in decimal degrees"),    # ra
        dec = real("Declination of the planetary system in decimal degrees"),       # dec
        optband = Pointer(string(), doc="Optical Magnitude Band", nullable=True),   # st_optband
        efftemperature = Record(
          doc = "Temperature of the star as modeled by a black body emitting the same total amount of electromagnetic radiation",
          fields = dict(
            val = real("Effective Temperature [K]", nullable=True),                 # st_teff
            hierr = real("Effective Temperature Upper Unc. [K]", nullable=True),    # st_tefferr1
            loerr = real("Effective Temperature Lower Unc. [K]", nullable=True),    # st_tefferr2
            lim = boolean("Effective Temperature Limit Flag", nullable=True),       # st_tefflim (0: False, 1: True)
            blend = boolean("Effective Temperature Blend Flag", nullable=True)      # st_teffblend (0: False)
          )
        ),
        mass = Record(
          doc = "Amount of matter contained in the star, measured in units of masses of the Sun",
          fields = dict(
            val = real("Stellar Mass [Solar mass]", nullable=True),                 # st_mass
            hierr = real("Stellar Mass Upper Unc. [Solar mass]", nullable=True),    # st_masserr1
            loerr = real("Stellar Mass Lower Unc. [Solar mass]", nullable=True),    # st_masserr2
            lim = boolean("Stellar Mass Limit Flag", nullable=True),                # st_masslim (0: False, -1: True)
            blend = boolean("Stellar Mass Blend Flag", nullable=True)               # st_massblend (0: False)
          )
        ),
        radius = Record(
          doc = "Length of a line segment from the center of the star to its surface, measured in units of radius of the Sun",
          fields = dict(
            val = real("Stellar Radius [Solar radii]", nullable=True),              # st_rad
            hierr = real("Stellar Radius Upper Unc. [Solar radii]", nullable=True), # st_raderr1
            loerr = real("Stellar Radius Lower Unc. [Solar radii]", nullable=True), # st_raderr2
            lim = boolean("Stellar Radius Limit Flag", nullable=True),              # st_radlim (0: False)
            blend = boolean("Stellar Radius Blend Flag")                            # st_radblend (0: False)
          )
        ),
        galactic = Record(
          doc = "Coordinates with respect to the plane of the galaxy in degrees",
          fields = dict(
            longitude = real("Galactic Longitude [deg]"),                           # st_glon
            latitude = real("Galactic Latitude [deg]")                              # st_glat
          )
        ),
        ecliptic = Record(
          doc = "Coordinates with respect to the plane of the ecliptic in degrees",
          fields = dict(
            longitude = real("Ecliptic Longitude [deg]"),                           # st_elon
            latitude = real("Ecliptic Latitude [deg]")                              # st_elat
          )
        ),
        parallax = Record(
          doc = "Difference in the angular position of a star as measured at two opposite positions within the Earth's orbit",
          fields = dict(
            val = real("Parallax [mas]"),                                           # st_plx
            hierr = real("Parallax Upper Unc. [mas]", nullable=True),               # st_plxerr1
            loerr = real("Parallax Lower Unc. [mas]", nullable=True),               # st_plxerr2
            lim = boolean("Parallax Limit Flag", nullable=True),                    # st_plxlim
            blend = boolean("Parallax Blend Flag", nullable=True)                   # st_plxblend
          )
        ),
        distance = Record(
          doc = "Distance to the planetary system in units of parsecs",
          fields = dict(
            val = real("Distance [pc]", nullable=True),                             # st_dist
            hierr = real("Distance Upper Unc. [pc]", nullable=True),                # st_disterr1
            loerr = real("Distance Lower Unc. [pc]", nullable=True),                # st_disterr2
            lim = boolean("Distance Limit Flag", nullable=True),                    # st_distlim (0: False, -1: True)
            blend = boolean("Optical Magnitude Blend Flag", nullable=True),         # st_optmagblend (0: False)
          )
        ),
        propermotion = Record(
          doc = "Angular change over time as seen from the center of mass of the Solar System",
          fields = dict(
            ra = Record(
              doc = "Proper motion in right ascension",
              fields = dict(
                val = real("Proper Motion (RA) [mas/yr]", nullable=True),           # st_pmra
                err = real("Proper Motion (RA) Unc. [mas/yr]", nullable=True),      # st_pmraerr
                lim = boolean("Proper Motion (RA) Limit Flag", nullable=True)       # st_pmralim
              )
            ),
            dec = Record(
              doc = "Proper motion in declination",
              fields = dict(
                val = real("Proper Motion (Dec) [mas/yr]", nullable=True),          # st_pmdec
                err = real("Proper Motion (Dec) Unc. [mas/yr]", nullable=True),     # st_pmdecerr
                lim = boolean("Proper Motion (Dec) Limit Flag", nullable=True)      # st_pmdeclim
              )
            ),
            total = Record(
              doc = "Total proper motion",
              fields = dict(
                val = real("Total Proper Motion [mas/yr]", nullable=True),          # st_pm
                err = real("Total Proper Motion Unc. [mas/yr]", nullable=True),     # st_pmerr
                lim = boolean("Total Proper Motion Limit Flag", nullable=True),     # st_pmlim
                blend = boolean("Total Proper Motion Blend Flag", nullable=True)    # st_pmblend
              )
            )
          )
        ),
        gaia = Record(
          fields = dict(
            gband = Record(
              fields = dict(
                val = real(doc="G-band (Gaia) [mag]", nullable=True),               # gaia_gmag
                err = real(doc="G-band (Gaia) Unc. [mag]", nullable=True),          # gaia_gmagerr
                limit = boolean(doc="G-band (Gaia) Limit Flag", nullable=True)      # gaia_gmaglim
              )
            ),
            parallax = Record(
              doc = "Difference in the angular position of a star as measured at two opposite positions within the Earth's orbit",
              fields = dict(
                val = real(doc="Gaia Parallax [mas]", nullable=True),               # gaia_plx
                hierr = real(doc="Gaia Parallax Upper Unc. [mas]", nullable=True),  # gaia_plxerr1
                loerr = real(doc="Gaia Parallax Lower Unc. [mas]", nullable=True),  # gaia_plxerr2
                limit = boolean(doc="Gaia Parallax Limit Flag", nullable=True)      # gaia_plxlim
              )
            ),
            distance = Record(
              doc = "Distance to the planetary system in units of parsecs",
              fields = dict(
                val = real(doc="Gaia Distance [pc]", nullable=True),                # gaia_dist
                hierr = real(doc="Gaia Distance Upper Unc. [pc]", nullable=True),   # gaia_disterr1
                loerr = real(doc="Gaia Distance Lower Unc. [pc]", nullable=True),   # gaia_disterr2
                limit = boolean(doc="Gaia Distance Limit Flag", nullable=True)      # gaia_distlim
              )
            ),
            propermotion = Record(
              doc = "Angular change over time as seen from the center of mass of the Solar System",
              fields = dict(
                ra = Record(
                  doc = "Proper motion in right ascension",
                  fields = dict(
                    val = real(doc="Gaia Proper Motion (RA) [mas/yr]", nullable=True),       # gaia_pmra
                    err  = real(doc="Gaia Proper Motion (RA) Unc. [mas/yr]", nullable=True), # gaia_pmraerr
                    lim = boolean(doc="Gaia Proper Motion (RA) Limit Flag", nullable=True)   # gaia_pmralim
                  ),
                ),
                dec = Record(
                  doc = "Proper motion in declination",
                  fields = dict(
                    val = real(doc="Gaia Proper Motion (Dec) [mas/yr]", nullable=True),      # gaia_pmdec
                    err = real(doc="Gaia Proper Motion (Dec) Unc. [mas/yr]", nullable=True), # gaia_pmdecerr
                    lim = boolean(doc="Gaia Proper Motion (Dec) Limit Flag", nullable=True)  # gaia_pmdeclim
                  )
                ),
                total = Record(
                  doc = "Total proper motion",
                  fields = dict(
                    val = real(doc="Gaia Total Proper Motion [mas/yr]", nullable=True),      # gaia_pm
                    err = real(doc="Gaia Total Proper Motion Unc. [mas/yr]", nullable=True), # gaia_pmerr
                    lim = boolean(doc="Gaia Total Proper Motion Limit Flag", nullable=True)  # gaia_pmlim
                  )
                )
              )
            )
          )
        ),
        radialvelocity = Record(
          doc = "Velocity of the star in the direction of the line of sight",
          fields = dict(
            val = real("Radial Velocity [km/s]", nullable=True),                    # st_radv
            hierr = real("Radial Velocity Upper Unc. [km/s]", nullable=True),       # st_radverr1
            loerr = real("Radial Velocity Lower Unc. [km/s]", nullable=True),       # st_radverr2
            lim = boolean("Radial Velocity Limit Flag", nullable=True),             # st_radvlim
            blend = boolean("Radial Velocity Blend Flag", nullable=True)            # st_radvblend
          )
        ),
        spectraltype = Record(
          doc = "Classification of the star based on their spectral characteristics following the Morgan-Keenan system",
          fields = dict(
            val = real("Spectral Type", nullable=True),                             # st_sp
            str = real("Spectral Type", nullable=True),                             # st_spstr
            err = real("Spectral Type Unc.", nullable=True),                        # st_sperr
            lim = boolean("Spectral Type Limit Flag", nullable=True),               # st_splim
            blend = boolean("Spectral Type Blend Flag", nullable=True)              # st_spblend
          )
        ),
        surfacegravity = Record(
          doc = "Gravitational acceleration experienced at the stellar surface",
          fields = dict(
            val = real("Stellar Surface Gravity [log10(cm/s**2)]", nullable=True),                # st_logg
            hierr = real("Stellar Surface Gravity Upper Unc. [log10(cm/s**2)]", nullable=True),   # st_loggerr1
            loerr = real("Stellar Surface Gravity Lower Unc. [log10(cm/s**2)]", nullable=True),   # st_loggerr2
            lim = boolean("Stellar Surface Gravity Limit Flag", nullable=True),                   # st_logglim
            blend = boolean("Stellar Surface Gravity Blend Flag", nullable=True)                  # st_loggblend
          )
        ),
        luminosity = Record(
          doc = "Amount of energy emitted by a star per unit time, measured in units of solar luminosities",
          fields = dict(
            val = real("Stellar Luminosity [log(Solar)]", nullable=True),                         # st_lum
            hierr = real("Stellar Luminosity Upper Unc. [log(Solar)]", nullable=True),            # st_lumerr1
            loerr = real("Stellar Luminosity Lower Unc. [log(Solar)]", nullable=True),            # st_lumerr2
            lim = boolean("Stellar Luminosity Limit Flag", nullable=True),                        # st_lumlim
            blend = boolean("Stellar Luminosity Blend Flag", nullable=True)                       # st_lumblend
          )
        ),
        density = Record(
          doc = "Amount of mass per unit of volume of the star",
          fields = dict(
            val = real("Stellar Density [g/cm**3]", nullable=True),                 # st_dens
            hierr = real("Stellar Density Upper Unc. [g/cm**3]", nullable=True),    # st_denserr1
            loerr = real("Stellar Density Lower Unc. [g/cm**3]", nullable=True),    # st_denserr2
            lim = boolean("Stellar Density Limit Flag", nullable=True)              # st_denslim
          )
        ),
        metallicity = Record(
          doc = "Measurement of the metal content of the photosphere of the star as compared to the hydrogen content",
          fields = dict(
            val = real("Stellar Metallicity [dex]", nullable=True),                 # st_metfe
            loerr = real("Stellar Metallicity Upper Unc. [dex]", nullable=True),    # st_metfeerr1
            hierr = real("Stellar Metallicity Lower Unc. [dex]", nullable=True),    # st_metfeerr2
            lim = boolean("Stellar Metallicity Limit Flag", nullable=True),         # st_metfelim
            blend = boolean("Stellar Metallicity Blend Flag", nullable=True),       # st_metfeblend
            ratio = string("Metallicity Ratio: ([Fe/H] denotes iron abundance, [M/H] refers to a general metal content)", nullable=True)   # st_metratio
          )
        ),
        age = Record(
          doc = "The age of the host star",
          fields = dict(
            val = real("Stellar Age [Gyr]", nullable=True),                         # st_age
            hierr = real("Stellar Age Upper Unc. [Gyr]", nullable=True),            # st_ageerr1
            loerr = real("Stellar Age Lower Unc. [Gyr]", nullable=True),            # st_ageerr2
            lim = boolean("Stellar Age Limit Flag", nullable=True)                  # st_agelim
          )
        ),
        rotational_velocity = Record(
          doc = "Rotational velocity at the equator of the star multiplied by the sine of the inclination",
          fields = dict(
            val = real("Rot. Velocity V*sin(i) [km/s]", nullable=True),                          # st_vsini
            hierr = real("Rot. Velocity V*sin(i) Upper Unc. [km/s]", nullable=True),             # st_vsinierr1
            loerr = real("Rot. Velocity V*sin(i) Lower Unc. [km/s]", nullable=True),             # st_vsinierr2
            lim = boolean("Rot. Velocity V*sin(i) Limit Flag", nullable=True),                   # st_vsinilim
            blend = boolean("Rot. Velocity V*sin(i) Blend Flag", nullable=True)                  # st_vsiniblend
          )
        ),
        activity = Record(
          doc = "Stellar activity in various metrics",
          fields = dict(
            sindex = Record(
              doc = "Chromospheric activity as measured by the S-index (ratio of the emission of the H and K Ca lines to that in nearby continuum)",
              fields = dict(
                val = real("Stellar Activity S-index", nullable=True),                           # st_acts
                err = real("Stellar Activity S-index Unc.", nullable=True),                      # st_actserr
                lim = boolean("Stellar Activity S-index Limit Flag", nullable=True),             # st_actslim
                blend = boolean("Stellar Activity S-index Blend Flag", nullable=True)            # st_actsblend
              )
            ),
            rindex = Record(
              doc = "Chromospheric activity as measured by the log(R' HK) index, with is based on the S-index, but excludes the photospheric component in the Ca lines",
              fields = dict(
                val = real("Stellar Activity log(R'HK)", nullable=True),                         # st_actr
                err = real("Stellar Activity log(R'HK) Unc.", nullable=True),                    # st_actrerr
                lim = boolean("Stellar Activity log(R'HK) Limit Flag", nullable=True),           # st_actrlim
                blend = boolean("Stellar Activity log(R'HK) Blend Flag", nullable=True)          # st_actrblend
              )
            ),
            xindex = Record(
              doc = "Stellar activity as measured by the total luminosity in X-rays",
              fields = dict(
                val = real("X-ray Activity log(L<sub>x</sub>)", nullable=True),                  # st_actlx
                err = real("X-ray Activity log(L<sub>x</sub>) Unc.", nullable=True),             # st_actlxerr
                lim = boolean("X-ray Activity log(L<sub>x</sub>) Limit Flag", nullable=True),    # st_actlxlim
                blend = boolean("X-ray Activity log(L<sub>x</sub>) Blend Flag", nullable=True)   # st_actlxblend
              )
            )
          )
        ),
        num_timeseries = integer("Number of literature time series available for this star in the NASA Exoplanet Archive"), # st_nts
        num_transit_lightcurves = integer("Number of literature transit light curves available for this star in the NASA Exoplanet Archive"), # st_nplc
        num_general_lightcurves = integer("Number of Hipparcos light curves available for this star in the NASA Exoplanet Archive"), # st_nglc
        num_radial_timeseries = integer("Number of literature radial velocity curves available for this star in the NASA Exoplanet Archive"), # st_nrvc
        num_amateur_lightcurves = integer("Number of literature amateur light curves available for this star in the NASA Exoplanet Archive"), # st_naxa
        num_images = integer("Number of literature images available for this star in the NASA Exoplanet Archive"), # st_nimg
        num_spectra = integer("Number of literature of spectra available for this star in the NASA Exoplanet Archive"), # st_nspec
        photometry = Record(
          fields = dict(
            uband = Record(
              doc = "Brightness of the host star as measured using the U (Johnson) band in units of magnitudes",
              fields = dict(
                val = real("U-band (Johnson) [mag]", nullable=True),   # st_uj
                err = real("U-band (Johnson) Unc. [mag]", nullable=True),   # st_ujerr
                lim = boolean("U-band (Johnson) Limit Flag", nullable=True),   # st_ujlim
                blend = boolean("U-band (Johnson) Blend Flag", nullable=True)   # st_ujblend
              )
            ),
            vband = Record(
              doc = "Brightness of the host star as measured using the V (Johnson) band in units of magnitudes",
              fields = dict(
                val = real("V-band (Johnson) [mag]", nullable=True),   # st_vj
                err = real("V-band (Johnson) Unc. [mag]", nullable=True),   # st_vjerr
                lim = boolean("V-band (Johnson) Limit Flag", nullable=True),   # st_vjlim
                blend = boolean("V-band (Johnson) Blend Flag", nullable=True)   # st_vjblend
              )
            ),
            bband = Record(
              doc = "Brightness of the host star as measured using the B (Johnson) band in units of magnitudes",
              fields = dict(
                val = real("B-band (Johnson) [mag]", nullable=True),   # st_bj
                err = real("B-band (Johnson) Unc. [mag]", nullable=True),   # st_bjerr
                lim = boolean("B-band (Johnson) Limit Flag", nullable=True),        # st_bjlim
                blend = boolean("B-band (Johnson) Blend Flag", nullable=True)   # st_bjblend
              )
            ),
            rband = Record(
              doc = "Brightness of the host star as measured using the R (Cousins) band in units of magnitudes",
              fields = dict(
                val = real("R-band (Cousins) [mag]", nullable=True),   # st_rc
                err = real("R-band (Cousins) Unc. [mag]", nullable=True),        # st_rcerr
                lim = boolean("R-band (Cousins) Limit Flag", nullable=True),        # st_rclim
                blend = boolean("R-band (Cousins) Blend Flag", nullable=True)   # st_rcblend
              )
            ),
            iband = Record(
              doc = "Brightness of the host star as measured using the I (Cousins) band in units of magnitudes",
              fields = dict(
                val = real("I-band (Cousins) [mag]", nullable=True),   # st_ic
                err = real("I-band (Cousins) Unc. [mag]", nullable=True),   # st_icerr
                lim = boolean("I-band (Cousins) Limit Flag", nullable=True),   # st_iclim
                blend = boolean("I-band (Cousins) Blend Flag", nullable=True)   # st_icblend
              )
            ),
            jband = Record(
              doc = "Brightness of the host star as measured using the J (2MASS) band in units of magnitudes",
              fields = dict(
                val = real("J-band (2MASS) [mag]", nullable=True),   # st_j
                err = real("J-band (2MASS) Unc. [mag]", nullable=True),   # st_jerr
                lim = boolean("J-band (2MASS) Limit Flag", nullable=True),   # st_jlim
                blend = boolean("J-band (2MASS) Blend Flag", nullable=True)   # st_jblend
              )
            ),
            hband = Record(
              doc = "Brightness of the host star as measured using the H (2MASS) band in units of magnitudes",
              fields = dict(
                val = real("H-band (2MASS) [mag]", nullable=True),   # st_h
                err = real("H-band (2MASS) Unc. [mag]", nullable=True),   # st_herr
                lim = boolean("H-band (2MASS) Limit Flag", nullable=True),   # st_hlim
                blend = boolean("H-band (2MASS) Blend Flag", nullable=True)   # st_hblend
              )
            ),
            kband = Record(
              doc = "Brightness of the host star as measured using the K (2MASS) band in units of magnitudes",
              fields = dict(
                val = real("Ks-band (2MASS) [mag]", nullable=True),   # st_k
                err = real("Ks-band (2MASS) Unc. [mag]", nullable=True),        # st_kerr
                lim = boolean("Ks-band (2MASS) Limit Flag", nullable=True),        # st_klim
                blend = boolean("Ks-band (2MASS) Blend Flag", nullable=True)        # st_kblend
              )
            ),
            wise1 = Record(
              doc = "Brightness of the host star as measured using the 3.4um (WISE) band in units of magnitudes",
              fields = dict(
                val = real("WISE 3.4um [mag]", nullable=True),   # st_wise1
                err = real("WISE 3.4um Unc. [mag]", nullable=True),        # st_wise1err
                lim = boolean("WISE 3.4um Limit Flag", nullable=True),        # st_wise1lim
                blend = boolean("WISE 3.4um Blend Flag", nullable=True)   # st_wise1blend
              )
            ),
            wise2 = Record(
              doc = "Brightness of the host star as measured using the 4.6um (WISE) band in units of magnitudes",
              fields = dict(
                val = real("WISE 4.6um [mag]", nullable=True),   # st_wise2
                err = real("WISE 4.6um Unc. [mag]", nullable=True),        # st_wise2err
                lim = boolean("WISE 4.6um Limit Flag", nullable=True),        # st_wise2lim
                blend = boolean("WISE 4.6um Blend Flag", nullable=True)   # st_wise2blend
              )
            ),
            wise3 = Record(
              doc = "Brightness of the host star as measured using the 12.um (WISE) band in units of magnitudes",
              fields = dict(
                val = real("WISE 12.um [mag]", nullable=True),   # st_wise3
                err = real("WISE 12.um Unc. [mag]", nullable=True),   # st_wise3err
                lim = boolean("WISE 12.um Limit Flag", nullable=True),   # st_wise3lim
                blend = boolean("WISE 12.um Blend Flag", nullable=True)   # st_wise3blend
              )
            ),
            wise4 = Record(
              doc = "Brightness of the host star as measured using the 22.um (WISE) band in units of magnitudes",
              fields = dict(
                val = real("WISE 22.um [mag]", nullable=True),   # st_wise4
                err = real("WISE 22.um Unc. [mag]", nullable=True),   # st_wise4err
                lim = boolean("WISE 22.um Limit Flag", nullable=True),   # st_wise4lim
                blend = boolean("WISE 22.um Blend Flag", nullable=True)   # st_wise4blend
              )
            ),
            irac1 = Record(
              doc = "Brightness of the host star as measured using the 3.6um (IRAC) band in units of magnitudes",
              fields = dict(
                val = real("IRAC 3.6um [mag]", nullable=True),   # st_irac1
                err = real("IRAC 3.6um Unc. [mag]", nullable=True),   # st_irac1err
                lim = boolean("IRAC 3.6um Limit Flag", nullable=True),   # st_irac1lim
                blend = boolean("IRAC 3.6um Blend Flag", nullable=True)   # st_irac1blend
              )
            ),
            irac2 = Record(
              doc = "Brightness of the host star as measured using the 4.5um (IRAC) band in units of magnitudes",
              fields = dict(
                val = real("IRAC 4.5um [mag]", nullable=True),   # st_irac2
                err = real("IRAC 4.5um Unc. [mag]", nullable=True),        # st_irac2err
                lim = boolean("IRAC 4.5um Limit Flag", nullable=True),        # st_irac2lim
                blend = boolean("IRAC 4.5um Blend Flag", nullable=True)   # st_irac2blend
              )
            ),
            irac3 = Record(
              doc = "Brightness of the host star as measured using the 5.8um (IRAC) band in units of magnitudes",
              fields = dict(
                val = real("IRAC 5.8um [mag]", nullable=True),   # st_irac3
                err = real("IRAC 5.8um Unc. [mag]", nullable=True),        # st_irac3err
                lim = boolean("IRAC 5.8um Limit Flag", nullable=True),        # st_irac3lim
                blend = boolean("IRAC 5.8um Blend Flag", nullable=True)   # st_irac3blend
              )
            ),
            irac4 = Record(
              doc = "Brightness of the host star as measured using the 8.0um (IRAC) band in units of magnitudes",
              fields = dict(
                val = real("IRAC 8.0um [mag]", nullable=True),   # st_irac4
                err = real("IRAC 8.0um Unc. [mag]", nullable=True),   # st_irac4err
                lim = boolean("IRAC 8.0um Limit Flag", nullable=True),   # st_irac4lim
                blend = boolean("IRAC 8.0um Blend Flag", nullable=True)   # st_irac4blend
              )
            ),
            mips1 = Record(
              doc = "Brightness of the host star as measured using the 24um (MIPS) band in units of magnitudes",
              fields = dict(
                val = real("MIPS 24um [mag]", nullable=True),   # st_mips1
                err = real("MIPS 24um Unc. [mag]", nullable=True),   # st_mips1err
                lim = boolean("MIPS 24um Limit Flag", nullable=True),   # st_mips1lim
                blend = boolean("MIPS 24um Blend Flag", nullable=True)   # st_mips1blend
              )
            ),
            mips2 = Record(
              doc = "Brightness of the host star as measured using the 70um (MIPS) band in units of magnitudes",
              fields = dict(
                val = real("MIPS 70um [mag]", nullable=True),   # st_mips2
                err = real("MIPS 70um Unc. [mag]", nullable=True),   # st_mips2err
                lim = boolean("MIPS 70um Limit Flag", nullable=True),   # st_mips2lim
                blend = boolean("MIPS 70um Blend Flag", nullable=True)   # st_mips2blend
              )
            ),
            mips3 = Record(
              doc = "Brightness of the host star as measured using the 160um (MIPS) band in units of magnitudes",
              fields = dict(
                val = real("MIPS 160um [mag]", nullable=True),   # st_mips3
                err = real("MIPS 160um Unc. [mag]", nullable=True),        # st_mips3err
                lim = boolean("MIPS 160um Limit Flag", nullable=True),        # st_mips3lim
                blend = boolean("MIPS 160um Blend Flag", nullable=True)   # st_mips3blend
              )
            ),
            iras1 = Record(
              doc = "Brightness of the host star as measured using the 12um (IRAS) band in units of Jy",
              fields = dict(
                val = real("IRAS 12um Flux [Jy]", nullable=True),   # st_iras1
                err = real("IRAS 12um Flux Unc. [Jy]", nullable=True),        # st_iras1err
                lim = boolean("IRAS 12um Flux Limit Flag", nullable=True),        # st_iras1lim
                blend = boolean("IRAS 12um Flux Blend Flag", nullable=True)   # st_iras1blend
              )
            ),
            iras2 = Record(
              doc = "Brightness of the host star as measured using the 25um (IRAS) band in units of Jy",
              fields = dict(
                val = real("IRAS 25um Flux [Jy]", nullable=True),   # st_iras2
                err = real("IRAS 25um Flux Unc. [Jy]", nullable=True),        # st_iras2err
                lim = boolean("IRAS 25um Flux Limit Flag", nullable=True),        # st_iras2lim
                blend = boolean("IRAS 25um Flux Blend Flag", nullable=True)        # st_iras2blend
              )
            ),
            iras3 = Record(
              doc = "Brightness of the host star as measured using the 60um (IRAS) band in units of Jy",
              fields = dict(
                val = real("IRAS 60um Flux [Jy]", nullable=True),        # st_iras3
                err = real("IRAS 60um Flux Unc. [Jy]", nullable=True),        # st_iras3err
                lim = boolean("IRAS 60um Flux Limit Flag", nullable=True),        # st_iras3lim
                blend = boolean("IRAS 60um Flux Blend Flag", nullable=True)        # st_iras3blend
              )
            ),
            iras4 = Record(
              doc = "Brightness of the host star as measured using the 100um (IRAS) band in units of Jy",
              fields = dict(
                val = real("IRAS 100um Flux [Jy]", nullable=True),        # st_iras4
                err = real("IRAS 100um Flux Unc. [Jy]", nullable=True),        # st_iras4err
                lim = boolean("IRAS 100um Flux Limit Flag", nullable=True),        # st_iras4lim
                blend = boolean("IRAS 100um Flux Blend Flag", nullable=True),        # st_iras4blend
              )
            ),
            num_measurements = integer("Number of Photometry Measurements")        # st_photn
          )
        ),
        color = Record(
          fields = dict(
            ub_diff = Record(
              doc = "Color of the star as measured by the difference between U and B (Johnson) bands",
              fields = dict(
                val = real("U-B (Johnson) [mag]", nullable=True),        # st_umbj
                err = real("U-B (Johnson) Unc. [mag]", nullable=True),        # st_umbjerr
                lim = boolean("U-B (Johnson) Limit Flag", nullable=True),        # st_umbjlim
                blend = boolean("U-B (Johnson) Blend Flag", nullable=True)   # st_umbjblend
              )
            ),
            bv_diff = Record(
              doc = "Color of the star as measured by the difference between B and V (Johnson) bands",
              fields = dict(
                val = real("B-V (Johnson) [mag]", nullable=True),  # st_bmvj
                err = real("B-V (Johnson) Unc. [mag]", nullable=True),       # st_bmvjerr
                lim = boolean("B-V (Johnson) Limit Flag", nullable=True),       # st_bmvjlim
                blend = boolean("B-V (Johnson) Blend Flag", nullable=True)   # st_bmvjblend
              )
            ),
            vi_diff = Record(
              doc = "Color of the star as measured by the difference between V (Johnson) and I (Cousins) bands",
              fields = dict(
                val = real("V-I (Johnson-Cousins) [mag]", nullable=True),  # st_vjmic
                err = real("V-I (Johnson-Cousins) Unc. [mag]", nullable=True),       # st_vjmicerr
                lim = boolean("V-I (Johnson-Cousins) Limit Flag", nullable=True),       # st_vjmiclim
                blend = boolean("V-I (Johnson-Cousins) Blend Flag", nullable=True)        # st_vjmicblend
              )
            ),
            vr_diff = Record(
              doc = "Color of the star as measured by the difference between V (Johnson) and R (Cousins) bands",
              fields = dict(
                val = real("V-R (Johnson-Cousins) [mag]", nullable=True),       # st_vjmrc
                err = real("V-R (Johnson-Cousins) Unc. [mag]", nullable=True),       # st_vjmrcerr
                lim = boolean("V-R (Johnson-Cousins) Limit Flag", nullable=True),       # st_vjmrclim
                blend = boolean("V-R (Johnson-Cousins) Blend Flag", nullable=True)        # st_vjmrcblend
              )
            ),
            jh_diff = Record(
              doc = "Color of the star as measured by the difference between J and H (2MASS) bands",
              fields = dict(
                val = real("J-H (2MASS) [mag]", nullable=True),       # st_jmh2
                err = real("J-H (2MASS) Unc. [mag]", nullable=True),       # st_jmh2err
                lim = boolean("J-H (2MASS) Limit Flag", nullable=True),       # st_jmh2lim
                blend = boolean("J-H (2MASS) Blend Flag", nullable=True)        # st_jmh2blend
              )
            ),
            hk_diff = Record(
              doc = "Color of the star as measured by the difference between H and K (2MASS) bands",
              fields = dict(
                val = real("H-Ks (2MASS) [mag]", nullable=True),  # st_hmk2
                err = real("H-Ks (2MASS) Unc. [mag]", nullable=True),       # st_hmk2err
                lim = boolean("H-Ks (2MASS) Limit Flag", nullable=True),       # st_hmk2lim
                blend = boolean("H-Ks (2MASS) Blend Flag", nullable=True)        # st_hmk2blend
              )
            ),
            jk_diff = Record(
              doc = "Color of the star as measured by the difference between K and K (2MASS) bands",
              fields = dict(
                val = real("J-Ks (2MASS) [mag]", nullable=True),  # st_jmk2
                err = real("J-Ks (2MASS) Unc. [mag]", nullable=True),       # st_jmk2err
                lim = boolean("J-Ks (2MASS) Limit Flag", nullable=True),       # st_jmk2lim
                blend = boolean("J-Ks (2MASS) Blend Flag", nullable=True)        # st_jmk2blend
              )
            ),
            by_diff = Record(
              doc = "Color of the star as measured by the difference between b and y (Stromgren) bands",
              fields = dict(
                val = real("b-y (Stromgren) [mag]", nullable=True),  # st_bmy
                err = real("b-y (Stromgren) Unc. [mag]", nullable=True),       # st_bmyerr
                lim = boolean("b-y (Stromgren) Limit Flag", nullable=True),       # st_bmylim
                blend = boolean("b-y (Stromgren) Blend Flag", nullable=True)   # st_bmyblend
              )
            ),
            m1_diff = Record(
              doc = "Color of the star as measured by the m1 (Stromgren) system",
              fields = dict(
                val = real("m1 (Stromgren) [mag]", nullable=True),  # st_m1
                err = real("m1 (Stromgren) Unc. [mag]", nullable=True),       # st_m1err
                lim = boolean("m1 (Stromgren) Limit Flag", nullable=True),       # st_m1lim
                blend = boolean("m1 (Stromgren) Blend Flag", nullable=True)   # st_m1blend
              )
            ),
            c1_diff = Record(
              doc = "Color of the star as measured by the c1 (Stromgren) system",
              fields = dict(
                val = real("c1 (Stromgren) [mag]", nullable=True),  # st_c1
                err = real("c1 (Stromgren) Unc. [mag]", nullable=True),       # st_c1err
                lim = boolean("c1 (Stromgren) Limit Flag", nullable=True),       # st_c1lim
                blend = boolean("c1 (Stromgren) Blend Flag", nullable=True)   # st_c1blend
              )
            ),
            num_measurements = integer("Number of Color Measurements")   # st_colorn
          )
        ),
        num_planets = integer("Number of Planets in System"),            # pl_pnum
        planets = List(
          Record(
            name = "Planet",
            fields = dict(
              name = string("Name of planet"),                              # pl_name
              hd_name = string("HD identifier", nullable=True),             # hd_name
              hip_name = string("HIP identifier", nullable=True),           # hip_name
              letter = Pointer(integer("Planet Letter")),                   # pl_letter
              discovery_method = Pointer(string(), doc="Discovery Method"), # pl_discmethod
              orbital_period = Record(
                doc = "Time the planet takes to make a complete orbit around the host star or system",
                fields = dict(
                  val = real("Orbital Period [days]", nullable=True),                 # pl_orbper
                  hierr = real("Orbital Period Upper Unc. [days]", nullable=True),    # pl_orbpererr1
                  loerr = real("Orbital Period Lower Unc. [days]", nullable=True),    # pl_orbpererr2
                  lim = boolean("Orbital Period Limit Flag", nullable=True)           # pl_orbperlim
                )
              ),
              semimajor_axis = Record(
                doc = "The longest diameter of an elliptic orbit, or for directly imaged planets, the projected separation in the plane of the sky",
                fields = dict(
                  val = real("Orbit Semi-Major Axis [AU]", nullable=True),               # pl_orbsmax
                  hierr = real("Orbit Semi-Major Axis Upper Unc. [AU]", nullable=True),  # pl_orbsmaxerr1
                  loerr = real("Orbit Semi-Major Axis Lower Unc. [AU]", nullable=True),  # pl_orbsmaxerr2
                  lim = boolean("Orbit Semi-Major Axis Limit Flag", nullable=True)       # pl_orbsmaxlim
                )
              ),
              eccentricity = Record(
                doc = "Amount by which the orbit of the planet deviates from a perfect circle",
                fields = dict(
                  val = real("Eccentricity", nullable=True),                     # pl_orbeccen
                  hierr = real("Eccentricity Upper Unc.", nullable=True),        # pl_orbeccenerr1
                  loerr = real("Eccentricity Lower Unc.", nullable=True),        # pl_orbeccenerr2
                  lim = boolean("Eccentricity Limit Flag", nullable=True)        # pl_orbeccenlim
                )
              ),
              inclination = Record(
                doc = "Angular distance of the orbital plane from the line of sight",
                fields = dict(
                  val = real("Inclination [deg]", nullable=True),                # pl_orbincl
                  hierr = real("Inclination Upper Unc. [deg]", nullable=True),   # pl_orbinclerr1
                  loerr = real("Inclination Lower Unc. [deg]", nullable=True),   # pl_orbinclerr2
                  lim = boolean("Inclination Limit Flag", nullable=True)         # pl_orbincllim
                )
              ),
              mass = Record(
                doc = "Best planet mass measurement in units of masses of Jupiter. Either Mass, M*sin(i)/sin(i), or M*sin(i). See provenance for source of the measurement",
                fields = dict(
                  val = real("Planet Mass or M*sin(i)[Jupiter mass]", nullable=True),                  # pl_bmassj
                  hierr = real("Planet Mass or M*sin(i)Upper Unc. [Jupiter mass]", nullable=True),     # pl_bmassjerr1
                  loerr = real("Planet Mass or M*sin(i)Lower Unc. [Jupiter mass]", nullable=True),     # pl_bmassjerr2
                  lim = boolean("Planet Mass or M*sin(i)Limit Flag", nullable=True),                   # pl_bmassjlim
                  provenance = Pointer(string(), doc="Planet Mass or M*sin(i) Provenance", nullable=True)    # pl_bmassprov
                )
              ),
              radius = Record(
                doc = "Length of a line segment from the center of the planet to its surface, measured in units of radius of Jupiter",
                fields = dict(
                  val = real("Planet Radius [Jupiter radii]", nullable=True),   # pl_radj
                  hierr = real("Planet Radius Upper Unc. [Jupiter radii]", nullable=True),        # pl_radjerr1
                  loerr = real("Planet Radius Lower Unc. [Jupiter radii]", nullable=True),        # pl_radjerr2
                  lim = boolean("Planet Radius Limit Flag", nullable=True)        # pl_radjlim
                )
              ),
              density = Record(
                doc = "Amount of mass per unit of volume of the planet",
                fields = dict(
                  val = real("Planet Density [g/cm**3]", nullable=True),        # pl_dens
                  hierr = real("Planet Density Upper Unc. [g/cm**3]", nullable=True),        # pl_denserr1
                  loerr = real("Planet Density Lower Unc. [g/cm**3]", nullable=True),        # pl_denserr2
                  lim = boolean("Planet Density Limit Flag", nullable=True)        # pl_denslim
                )
              ),
              has_timing_variations = boolean("""Flag indicating if the planet orbit exhibits transit timing variations from another planet in the system.

Note: Non-transiting planets discovered via the transit timing variations of another planet in the system will not have their TTV flag set, since they do not themselves demonstrate TTVs."""),  # pl_ttvflag
              in_kepler_data = boolean("Flag indicating if the planetary system signature is present in data taken with the Kepler mission"), # pl_kepflag
              in_k2_data = boolean("Flag indicating if the planetary system signature is present in data taken with the K2 Mission"), # pl_k2flag
              num_notes = integer("Number of Notes associated with the planet. View all notes in the Confirmed Planet Overview page."), # pl_nnotes
              has_transits = boolean("Flag indicating if the planet transits its host star"), # pl_tranflag
              has_radial_velocity = boolean("Flag indicating if the planet host star exhibits radial velocity variations due to the planet"), # pl_tranflag
              has_image = boolean("Flag indicating if the planet has been observed via imaging techniques"), # pl_imgflag
              has_astrometrical_variations = boolean("Flag indicating if the planet host star exhibits astrometrical variations due to the planet", nullable=True), # pl_astflag
              has_orbital_modulations = boolean("Flag indicating whether the planet exhibits orbital modulations on the phase curve "), # pl_omflag
              has_binary = boolean("Flag indicating whether the planet orbits a binary system"), # pl_cbflag
              angsep = Record(
                doc = "The calculated angular separation (semi-major axis/distance) between the star and the planet. This value is only calculated for systems with both a semi-major axis and a distance value.",
                fields = dict(
                  val = real("Calculated Angular Separation [mas]", nullable=True),   # pl_angsep
                  hierr = real("Calculated Angular Separation Upper Unc. [mas]", nullable=True),        # pl_angseperr1
                  loerr = real("Calculated Angular Separation Lower Unc. [mas]", nullable=True)        # pl_angseperr2
                )
              ),





            )
          ) # planet Record
        ) # planets List
      )
    )
  )
)






              pl_orbtper     real("Time of Periastron [days]", nullable=True)        # pl_orbtper
              pl_orbtpererr1 real("Time of Periastron Upper Unc. [days]", nullable=True)        # pl_orbtpererr1
              pl_orbtpererr2 real("Time of Periastron Lower Unc. [days]", nullable=True)        # pl_orbtpererr2
              pl_orbtperlim  real("Time of Periastron Limit Flag", nullable=True)        # pl_orbtperlim
              pl_orblper     "Long. of Periastron [deg]"     set([None, bool])   # pl_orblper
              pl_orblpererr1 real("Long. of Periastron Upper Unc. [deg]", nullable=True)        # pl_orblpererr1
              pl_orblpererr2 real("Long. of Periastron Lower Unc. [deg]", nullable=True)        # pl_orblpererr2
              pl_orblperlim  real("Long. of Periastron Limit Flag", nullable=True)        # pl_orblperlim
              pl_rvamp       "Radial Velocity Amplitude [m/s]"     set([None, bool])   # pl_rvamp
              pl_rvamperr1   real("Radial Velocity Amplitude Upper Unc. [m/s]", nullable=True)        # pl_rvamperr1
              pl_rvamperr2   real("Radial Velocity Amplitude Lower Unc. [m/s]", nullable=True)        # pl_rvamperr2
              pl_rvamplim    real("Radial Velocity Amplitude Limit Flag", nullable=True)        # pl_rvamplim
              pl_eqt         integer("Equilibrium Temperature [K]", nullable=True)        # pl_eqt
              pl_eqterr1     integer("Equilibrium Temperature Upper Unc. [K]", nullable=True)        # pl_eqterr1
              pl_eqterr2     integer("Equilibrium Temperature Lower Unc. [K]", nullable=True)        # pl_eqterr2
              pl_eqtlim      integer("Equilibrium Temperature Limit Flag", nullable=True)        # pl_eqtlim
              pl_insol       "Insolation Flux [Earth flux]"     set([None, bool])   # pl_insol
              pl_insolerr1   real("Insolation Flux Upper Unc. [Earth flux]", nullable=True)        # pl_insolerr1
              pl_insolerr2   real("Insolation Flux Lower Unc. [Earth flux]", nullable=True)        # pl_insolerr2
              pl_insollim    real("Insolation Flux Limit Flag", nullable=True)        # pl_insollim
              pl_massj       "Planet Mass [Jupiter mass]"     set([None, bool])   # pl_massj
              pl_massjerr1   real("Planet Mass Upper Unc. [Jupiter mass]", nullable=True)        # pl_massjerr1
              pl_massjerr2   real("Planet Mass Lower Unc. [Jupiter mass]", nullable=True)        # pl_massjerr2
              pl_massjlim    real("Planet Mass Limit Flag", nullable=True)        # pl_massjlim
              pl_msinij      integer("Planet M*sin(i) [Jupiter mass]", nullable=True)        # pl_msinij
              pl_msinijerr1  real("Planet M*sin(i) Upper Unc. [Jupiter mass]", nullable=True)        # pl_msinijerr1
              pl_msinijerr2  real("Planet M*sin(i) Lower Unc. [Jupiter mass]", nullable=True)        # pl_msinijerr2
              pl_msinijlim   real("Planet M*sin(i) Limit Flag", nullable=True)        # pl_msinijlim
              pl_masse       integer("Planet Mass [Earth mass]", nullable=True)        # pl_masse
              pl_masseerr1   real("Planet Mass Upper Unc. [Earth mass]", nullable=True)        # pl_masseerr1
              pl_masseerr2   real("Planet Mass Lower Unc. [Earth mass]", nullable=True)        # pl_masseerr2
              pl_masselim    real("Planet Mass Limit Flag", nullable=True)        # pl_masselim
              pl_msinie      integer("Planet M*sin(i) [Earth mass]", nullable=True)        # pl_msinie
              pl_msinieerr1  real("Planet M*sin(i) Upper Unc. [Earth mass]", nullable=True)        # pl_msinieerr1
              pl_msinieerr2  real("Planet M*sin(i) Lower Unc. [Earth mass]", nullable=True)        # pl_msinieerr2
              pl_msinielim   real("Planet M*sin(i) Limit Flag", nullable=True)        # pl_msinielim
              pl_bmasse      integer("Planet Mass or M*sin(i) [Earth mass]", nullable=True)        # pl_bmasse
              pl_bmasseerr1  real("Planet Mass or M*sin(i) Upper Unc. [Earth mass]", nullable=True)        # pl_bmasseerr1
              pl_bmasseerr2  real("Planet Mass or M*sin(i) Lower Unc. [Earth mass]", nullable=True)        # pl_bmasseerr2
              pl_bmasselim   real("Planet Mass or M*sin(i) Limit Flag", nullable=True)        # pl_bmasselim
              pl_rade        integer("Planet Radius [Earth radii]", nullable=True)        # pl_rade
              pl_radeerr1    real("Planet Radius Upper Unc. [Earth radii]", nullable=True)        # pl_radeerr1
              pl_radeerr2    real("Planet Radius Lower Unc. [Earth radii]", nullable=True)        # pl_radeerr2
              pl_radelim     real("Planet Radius Limit Flag", nullable=True)        # pl_radelim
              pl_rads        real("Planet Radius [Solar radii]", nullable=True)        # pl_rads
              pl_radserr1    real("Planet Radius Upper Unc. [Solar radii]", nullable=True)        # pl_radserr1
              pl_radserr2    real("Planet Radius Lower Unc. [Solar radii]", nullable=True)        # pl_radserr2
              pl_radslim     real("Planet Radius Limit Flag", nullable=True)        # pl_radslim
              pl_trandep     real("Transit Depth [percent]", nullable=True)        # pl_trandep
              pl_trandeperr1 real("Transit Depth Upper Unc. [percent]", nullable=True)        # pl_trandeperr1
              pl_trandeperr2 real("Transit Depth Lower Unc. [percent]", nullable=True)        # pl_trandeperr2
              pl_trandeplim  real("Transit Depth Limit Flag", nullable=True)        # pl_trandeplim
              pl_trandur     real("Transit Duration [days]", nullable=True)        # pl_trandur
              pl_trandurerr1 real("Transit Duration Upper Unc. [days]", nullable=True)        # pl_trandurerr1
              pl_trandurerr2 real("Transit Duration Lower Unc. [days]", nullable=True)        # pl_trandurerr2
              pl_trandurlim  real("Transit Duration Limit Flag", nullable=True)        # pl_trandurlim
              pl_tranmid     "Transit Midpoint [days]"     set([None, bool])   # pl_tranmid
              pl_tranmiderr1 real("Transit Midpoint Upper Unc. [days]", nullable=True)        # pl_tranmiderr1
              pl_tranmiderr2 real("Transit Midpoint Lower Unc. [days]", nullable=True)        # pl_tranmiderr2
              pl_tranmidlim  real("Transit Midpoint Limit Flag", nullable=True)        # pl_tranmidlim
              pl_tsystemref  "Time System Reference"     set([None, bool])   # pl_tsystemref
              pl_imppar      "Impact Parameter"     set([str, None])   # pl_imppar
              pl_impparerr1  real("Impact Parameter Upper Unc.", nullable=True)        # pl_impparerr1
              pl_impparerr2  real("Impact Parameter Lower Unc.", nullable=True)        # pl_impparerr2
              pl_impparlim   real("Impact Parameter Limit Flag", nullable=True)        # pl_impparlim
              pl_occdep      "Occultation Depth [percentage]"     set([None, bool])   # pl_occdep
              pl_occdeperr1  real("Occultation Depth Upper Unc. [percentage]", nullable=True)        # pl_occdeperr1
              pl_occdeperr2  real("Occultation Depth Lower Unc. [percentage]", nullable=True)        # pl_occdeperr2
              pl_occdeplim   real("Occultation Depth Limit Flag", nullable=True)        # pl_occdeplim
              pl_ratdor      "Ratio of Distance to Stellar Radius"     set([None, bool])   # pl_ratdor
              pl_ratdorerr1  real("Ratio of Distance to Stellar Radius Upper Unc.", nullable=True)        # pl_ratdorerr1
              pl_ratdorerr2  real("Ratio of Distance to Stellar Radius Lower Unc.", nullable=True)        # pl_ratdorerr2
              pl_ratdorlim   real("Ratio of Distance to Stellar Radius Limit Flag", nullable=True)        # pl_ratdorlim
              pl_ratror      "Ratio of Planet to Stellar Radius"     set([None, bool])   # pl_ratror
              pl_ratrorerr1  real("Ratio of Planet to Stellar Radius Upper Unc.", nullable=True)        # pl_ratrorerr1
              pl_ratrorerr2  real("Ratio of Planet to Stellar Radius Lower Unc.", nullable=True)        # pl_ratrorerr2
              pl_ratrorlim   real("Ratio of Planet to Stellar Radius Limit Flag", nullable=True)        # pl_ratrorlim
              pl_def_reflink "Default Reference"     set([None, bool])   # pl_def_reflink
              pl_disc        string("Year of Discovery")        # pl_disc
              pl_disc_reflink integer("Discovery Reference")        # pl_disc_reflink
              pl_locale      string("Discovery Locale")        # pl_locale
              pl_facility    string("Discovery Facility")        # pl_facility
              pl_telescope   string("Discovery Telescope")        # pl_telescope
              pl_instrument  string("Discovery Instrument")        # pl_instrument
              pl_status      string("Status")        # pl_status
              pl_mnum        integer("Number of Moons in System")        # pl_mnum
              pl_st_npar     "Number of Stellar and Planet Parameters"     set([bool])   # pl_st_npar
              pl_st_nref     integer("Number of Stellar and Planet References")        # pl_st_nref
              pl_pelink      "Link to Exoplanet Encyclopaedia"     set([bool])   # pl_pelink
              pl_edelink     "Link to Exoplanet Data Explorer"     set([str, None])   # pl_edelink
              pl_publ_date   "Publication Date"     set([str, None])   # pl_publ_date




# types = {}
uniques = {}
fields = None
for line in csv.reader(open("/tmp/downloads/planets.csv")):
    if line[0][0] != "#":
        if fields is None:
            fields = line
        else:
            for n, x in zip(fields, line):
                if n not in uniques:
                    uniques[n] = set()
                uniques[n].add(x)


                # if n not in types:
                #     types[n] = set()
                
                # if x == "0" or x == "1":
                #     types[n].add(bool)
                # else:
                #     try:
                #         int(x)
                #     except ValueError:
                #         try:
                #             float(x)
                #         except ValueError:
                #             if x == "":
                #                 types[n].add(None)
                #             else:
                #                 types[n].add(str)
                #         else:
                #             types[n].add(float)
                #     else:
                #         types[n].add(int)
