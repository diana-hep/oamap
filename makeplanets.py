import os

import csv

def boolean(x):
    if x == "":
        return None
    elif x == "0":
        return False
    else:
        return True

def integer(x):
    if x == "":
        return None
    else:
        return int(x)

def real(x):
    if x == "":
        return None
    else:
        return float(x)

def string(x):
    if x == "":
        return None
    else:
        return x

def rec(x):
    assert isinstance(x, dict)
    if all(xi is None for xi in x.values()):
        return None
    else:
        return x

# https://exoplanetarchive.ipac.caltech.edu/cgi-bin/TblView/nph-tblView?app=ExoTbls&config=planets

fields = None
stars = {}
for line in csv.reader(open("planets.csv")):
    if line[0][0] != "#":
        if fields is None:
            fields = line
        else:
            x = dict(zip(fields, line))
            if x["pl_hostname"] not in stars:
                stars[x["pl_hostname"]] = {
                    "name": string(x["pl_hostname"]),
                    "update": string(x["rowupdate"]),
                    "ra": real(x["ra"]),
                    "dec": real(x["dec"]),
                    "opticalband": string(x["st_optband"]),
                    "temperature": rec({"val": real(x["st_teff"]), "hierr": real(x["st_tefferr1"]), "loerr": real(x["st_tefferr2"]), "lim": boolean(x["st_tefflim"]), "blend": boolean(x["st_teffblend"])}),
                    "mass": rec({"val": real(x["st_mass"]), "hierr": real(x["st_masserr1"]), "loerr": real(x["st_masserr2"]), "lim": boolean(x["st_masslim"]), "blend": boolean(x["st_massblend"])}),
                    "radius": rec({"val": real(x["st_rad"]), "hierr": real(x["st_raderr1"]), "loerr": real(x["st_raderr2"]), "lim": boolean(x["st_radlim"]), "blend": boolean(x["st_radblend"])}),
                    "galactic": rec({"longitude": real(x["st_glon"]), "latitude": real(x["st_glat"])}),
                    "ecliptic": rec({"longitude": real(x["st_elon"]), "latitude": real(x["st_elat"])}),
                    "parallax": rec({"val": real(x["st_plx"]), "hierr": real(x["st_plxerr1"]), "loerr": real(x["st_plxerr2"]), "lim": boolean(x["st_plxlim"]), "blend": boolean(x["st_plxblend"])}),
                    "distance": rec({"val": real(x["st_dist"]), "hierr": real(x["st_disterr1"]), "loerr": real(x["st_disterr2"]), "lim": boolean(x["st_distlim"]), "blend": boolean(x["st_optmagblend"])}),
                    "propermotion": rec({"ra": rec({"val": real(x["st_pmra"]), "err": real(x["st_pmraerr"]), "lim": boolean(x["st_pmralim"])}), "dec": rec({"val": real(x["st_pmdec"]), "err": real(x["st_pmdecerr"]), "lim": boolean(x["st_pmdeclim"])}), "total": rec({"val": real(x["st_pm"]), "err": real(x["st_pmerr"]), "lim": boolean(x["st_pmlim"]), "blend": boolean(x["st_pmblend"])})}),
                    "gaia": rec({"gband": rec({"val": real(x["gaia_gmag"]), "err": real(x["gaia_gmagerr"]), "lim": boolean(x["gaia_gmaglim"])}), "parallax": rec({"val": real(x["gaia_plx"]), "hierr": real(x["gaia_plxerr1"]), "loerr": real(x["gaia_plxerr2"]), "lim": boolean(x["gaia_plxlim"])}), "distance": rec({"val": real(x["gaia_dist"]), "hierr": real(x["gaia_disterr1"]), "loerr": real(x["gaia_disterr2"]), "lim": boolean(x["gaia_distlim"])}), "propermotion": rec({"ra": rec({"val": real(x["gaia_pmra"]), "err": real(x["gaia_pmraerr"]), "lim": boolean(x["gaia_pmralim"])}), "dec": rec({"val": real(x["gaia_pmdec"]), "err": real(x["gaia_pmdecerr"]), "lim": boolean(x["gaia_pmdeclim"])}), "total": rec({"val": real(x["gaia_pm"]), "err": real(x["gaia_pmerr"]), "lim": boolean(x["gaia_pmlim"])})})}),
                    "radialvelocity": rec({"val": real(x["st_radv"]), "hierr": real(x["st_radverr1"]), "loerr": real(x["st_radverr2"]), "lim": boolean(x["st_radvlim"]), "blend": boolean(x["st_radvblend"])}),
                    "spectraltype": rec({"val": real(x["st_sp"]), "str": string(x["st_spstr"]), "err": real(x["st_sperr"]), "lim": boolean(x["st_splim"]), "blend": boolean(x["st_spblend"])}),
                    "surfacegravity": rec({"val": real(x["st_logg"]), "hierr": real(x["st_loggerr1"]), "loerr": real(x["st_loggerr2"]), "lim": boolean(x["st_logglim"]), "blend": boolean(x["st_loggblend"])}),
                    "luminosity": rec({"val": real(x["st_lum"]), "hierr": real(x["st_lumerr1"]), "loerr": real(x["st_lumerr2"]), "lim": boolean(x["st_lumlim"]), "blend": boolean(x["st_lumblend"])}),
                    "density": rec({"val": real(x["st_dens"]), "hierr": real(x["st_denserr1"]), "loerr": real(x["st_denserr2"]), "lim": boolean(x["st_denslim"])}),
                    "metallicity": rec({"val": real(x["st_metfe"]), "loerr": real(x["st_metfeerr1"]), "hierr": real(x["st_metfeerr2"]), "lim": boolean(x["st_metfelim"]), "blend": boolean(x["st_metfeblend"]), "ratio": string(x["st_metratio"])}),
                    "age": rec({"val": real(x["st_age"]), "hierr": real(x["st_ageerr1"]), "loerr": real(x["st_ageerr2"]), "lim": boolean(x["st_agelim"])}),
                    "rotational_velocity": rec({"val": real(x["st_vsini"]), "hierr": real(x["st_vsinierr1"]), "loerr": real(x["st_vsinierr2"]), "lim": boolean(x["st_vsinilim"]), "blend": boolean(x["st_vsiniblend"])}),
                    "activity": rec({"sindex": rec({"val": real(x["st_acts"]), "err": real(x["st_actserr"]), "lim": boolean(x["st_actslim"]), "blend": boolean(x["st_actsblend"])}), "rindex": rec({"val": real(x["st_actr"]), "err": real(x["st_actrerr"]), "lim": boolean(x["st_actrlim"]), "blend": boolean(x["st_actrblend"])}), "xindex": rec({"val": real(x["st_actlx"]), "err": real(x["st_actlxerr"]), "lim": boolean(x["st_actlxlim"]), "blend": boolean(x["st_actlxblend"])})}),
                    "num_timeseries": integer(x["st_nts"]),
                    "num_transit_lightcurves": integer(x["st_nplc"]),
                    "num_general_lightcurves": integer(x["st_nglc"]),
                    "num_radial_timeseries": integer(x["st_nrvc"]),
                    "num_amateur_lightcurves": integer(x["st_naxa"]),
                    "num_images": integer(x["st_nimg"]),
                    "num_spectra": integer(x["st_nspec"]),
                    "photometry": rec({"uband": rec({"val": real(x["st_uj"]), "err": real(x["st_ujerr"]), "lim": boolean(x["st_ujlim"]), "blend": boolean(x["st_ujblend"])}), "vband": rec({"val": real(x["st_vj"]), "err": real(x["st_vjerr"]), "lim": boolean(x["st_vjlim"]), "blend": boolean(x["st_vjblend"])}), "bband": rec({"val": real(x["st_bj"]), "err": real(x["st_bjerr"]), "lim": boolean(x["st_bjlim"]), "blend": boolean(x["st_bjblend"])}), "rband": rec({"val": real(x["st_rc"]), "err": real(x["st_rcerr"]), "lim": boolean(x["st_rclim"]), "blend": boolean(x["st_rcblend"])}), "iband": rec({"val": real(x["st_ic"]), "err": real(x["st_icerr"]), "lim": boolean(x["st_iclim"]), "blend": boolean(x["st_icblend"])}), "jband": rec({"val": real(x["st_j"]), "err": real(x["st_jerr"]), "lim": boolean(x["st_jlim"]), "blend": boolean(x["st_jblend"])}), "hband": rec({"val": real(x["st_h"]), "err": real(x["st_herr"]), "lim": boolean(x["st_hlim"]), "blend": boolean(x["st_hblend"])}), "kband": rec({"val": real(x["st_k"]), "err": real(x["st_kerr"]), "lim": boolean(x["st_klim"]), "blend": boolean(x["st_kblend"])}), "wise1": rec({"val": real(x["st_wise1"]), "err": real(x["st_wise1err"]), "lim": boolean(x["st_wise1lim"]), "blend": boolean(x["st_wise1blend"])}), "wise2": rec({"val": real(x["st_wise2"]), "err": real(x["st_wise2err"]), "lim": boolean(x["st_wise2lim"]), "blend": boolean(x["st_wise2blend"])}), "wise3": rec({"val": real(x["st_wise3"]), "err": real(x["st_wise3err"]), "lim": boolean(x["st_wise3lim"]), "blend": boolean(x["st_wise3blend"])}), "wise4": rec({"val": real(x["st_wise4"]), "err": real(x["st_wise4err"]), "lim": boolean(x["st_wise4lim"]), "blend": boolean(x["st_wise4blend"])}), "irac1": rec({"val": real(x["st_irac1"]), "err": real(x["st_irac1err"]), "lim": boolean(x["st_irac1lim"]), "blend": boolean(x["st_irac1blend"])}), "irac2": rec({"val": real(x["st_irac2"]), "err": real(x["st_irac2err"]), "lim": boolean(x["st_irac2lim"]), "blend": boolean(x["st_irac2blend"])}), "irac3": rec({"val": real(x["st_irac3"]), "err": real(x["st_irac3err"]), "lim": boolean(x["st_irac3lim"]), "blend": boolean(x["st_irac3blend"])}), "irac4": rec({"val": real(x["st_irac4"]), "err": real(x["st_irac4err"]), "lim": boolean(x["st_irac4lim"]), "blend": boolean(x["st_irac4blend"])}), "mips1": rec({"val": real(x["st_mips1"]), "err": real(x["st_mips1err"]), "lim": boolean(x["st_mips1lim"]), "blend": boolean(x["st_mips1blend"])}), "mips2": rec({"val": real(x["st_mips2"]), "err": real(x["st_mips2err"]), "lim": boolean(x["st_mips2lim"]), "blend": boolean(x["st_mips2blend"])}), "mips3": rec({"val": real(x["st_mips3"]), "err": real(x["st_mips3err"]), "lim": boolean(x["st_mips3lim"]), "blend": boolean(x["st_mips3blend"])}), "iras1": rec({"val": real(x["st_iras1"]), "err": real(x["st_iras1err"]), "lim": boolean(x["st_iras1lim"]), "blend": boolean(x["st_iras1blend"])}), "iras2": rec({"val": real(x["st_iras2"]), "err": real(x["st_iras2err"]), "lim": boolean(x["st_iras2lim"]), "blend": boolean(x["st_iras2blend"])}), "iras3": rec({"val": real(x["st_iras3"]), "err": real(x["st_iras3err"]), "lim": boolean(x["st_iras3lim"]), "blend": boolean(x["st_iras3blend"])}), "iras4": rec({"val": real(x["st_iras4"]), "err": real(x["st_iras4err"]), "lim": boolean(x["st_iras4lim"]), "blend": boolean(x["st_iras4blend"])}), "num_measurements": integer(x["st_photn"])}),
                    "color": rec({"ub_diff": rec({"val": real(x["st_umbj"]), "err": real(x["st_umbjerr"]), "lim": boolean(x["st_umbjlim"]), "blend": boolean(x["st_umbjblend"])}), "bv_diff": rec({"val": real(x["st_bmvj"]), "err": real(x["st_bmvjerr"]), "lim": boolean(x["st_bmvjlim"]), "blend": boolean(x["st_bmvjblend"])}), "vi_diff": rec({"val": real(x["st_vjmic"]), "err": real(x["st_vjmicerr"]), "lim": boolean(x["st_vjmiclim"]), "blend": boolean(x["st_vjmicblend"])}), "vr_diff": rec({"val": real(x["st_vjmrc"]), "err": real(x["st_vjmrcerr"]), "lim": boolean(x["st_vjmrclim"]), "blend": boolean(x["st_vjmrcblend"])}), "jh_diff": rec({"val": real(x["st_jmh2"]), "err": real(x["st_jmh2err"]), "lim": boolean(x["st_jmh2lim"]), "blend": boolean(x["st_jmh2blend"])}), "hk_diff": rec({"val": real(x["st_hmk2"]), "err": real(x["st_hmk2err"]), "lim": boolean(x["st_hmk2lim"]), "blend": boolean(x["st_hmk2blend"])}), "jk_diff": rec({"val": real(x["st_jmk2"]), "err": real(x["st_jmk2err"]), "lim": boolean(x["st_jmk2lim"]), "blend": boolean(x["st_jmk2blend"])}), "by_diff": rec({"val": real(x["st_bmy"]), "err": real(x["st_bmyerr"]), "lim": boolean(x["st_bmylim"]), "blend": boolean(x["st_bmyblend"])}), "m1_diff": rec({"val": real(x["st_m1"]), "err": real(x["st_m1err"]), "lim": boolean(x["st_m1lim"]), "blend": boolean(x["st_m1blend"])}), "c1_diff": rec({"val": real(x["st_c1"]), "err": real(x["st_c1err"]), "lim": boolean(x["st_c1lim"]), "blend": boolean(x["st_c1blend"])}), "num_measurements": integer(x["st_colorn"])}),
                    "num_planets": integer(x["pl_pnum"]),
                    "planets": []
                    }

            stars[x["pl_hostname"]]["planets"].append({
                "name": string(x["pl_name"]),
                "hd_name": string(x["hd_name"]),
                "hip_name": string(x["hip_name"]),
                "letter": string(x["pl_letter"]),
                "discovery_method": string(x["pl_discmethod"]),
                "orbital_period": rec({"val": real(x["pl_orbper"]), "hierr": real(x["pl_orbpererr1"]), "loerr": real(x["pl_orbpererr2"]), "lim": boolean(x["pl_orbperlim"])}),
                "semimajor_axis": rec({"val": real(x["pl_orbsmax"]), "hierr": real(x["pl_orbsmaxerr1"]), "loerr": real(x["pl_orbsmaxerr2"]), "lim": boolean(x["pl_orbsmaxlim"])}),
                "eccentricity": rec({"val": real(x["pl_orbeccen"]), "hierr": real(x["pl_orbeccenerr1"]), "loerr": real(x["pl_orbeccenerr2"]), "lim": boolean(x["pl_orbeccenlim"])}),
                "inclination": rec({"val": real(x["pl_orbincl"]), "hierr": real(x["pl_orbinclerr1"]), "loerr": real(x["pl_orbinclerr2"]), "lim": boolean(x["pl_orbincllim"])}),
                "mass": rec({"val": real(x["pl_massj"]), "hierr": real(x["pl_massjerr1"]), "loerr": real(x["pl_massjerr2"]), "lim": boolean(x["pl_massjlim"])}),
                "mass_sini": rec({"val": real(x["pl_msinij"]), "hierr": real(x["pl_msinijerr1"]), "loerr": real(x["pl_msinijerr2"]), "lim": boolean(x["pl_msinijlim"])}),
                "mass_best": rec({"val": real(x["pl_bmassj"]), "hierr": real(x["pl_bmassjerr1"]), "loerr": real(x["pl_bmassjerr2"]), "lim": boolean(x["pl_bmassjlim"]), "provenance": string(x["pl_bmassprov"])}),
                "radius": rec({"val": real(x["pl_radj"]), "hierr": real(x["pl_radjerr1"]), "loerr": real(x["pl_radjerr2"]), "lim": boolean(x["pl_radjlim"])}),
                "density": rec({"val": real(x["pl_dens"]), "hierr": real(x["pl_denserr1"]), "loerr": real(x["pl_denserr2"]), "lim": boolean(x["pl_denslim"])}),
                "has_timing_variations": boolean(x["pl_ttvflag"]),
                "in_kepler_data": boolean(x["pl_kepflag"]),
                "in_k2_data": boolean(x["pl_k2flag"]),
                "num_notes": integer(x["pl_nnotes"]),
                "has_transits": boolean(x["pl_tranflag"]),
                "has_radial_velocity": boolean(x["pl_tranflag"]),
                "has_image": boolean(x["pl_imgflag"]),
                "has_astrometrical_variations": boolean(x["pl_astflag"]),
                "has_orbital_modulations": boolean(x["pl_omflag"]),
                "has_binary": boolean(x["pl_cbflag"]),
                "angular_separation": rec({"val": real(x["pl_angsep"]), "hierr": real(x["pl_angseperr1"]), "loerr": real(x["pl_angseperr2"])}),
                "periastron": rec({"val": real(x["pl_orbtper"]), "hierr": real(x["pl_orbtpererr1"]), "loerr": real(x["pl_orbtpererr2"]), "lim": boolean(x["pl_orbtperlim"])}),
                "longitude_periastron": rec({"val": real(x["pl_orblper"]), "hierr": real(x["pl_orblpererr1"]), "loerr": real(x["pl_orblpererr2"]), "lim": boolean(x["pl_orblperlim"])}),
                "radial_velocity": rec({"val": real(x["pl_rvamp"]), "hierr": real(x["pl_rvamperr1"]), "loerr": real(x["pl_rvamperr2"]), "lim": boolean(x["pl_rvamplim"])}),
                "equilibrium_temperature": rec({"val": real(x["pl_eqt"]), "hierr": real(x["pl_eqterr1"]), "loerr": real(x["pl_eqterr2"]), "lim": boolean(x["pl_eqtlim"])}),
                "isolation_flux": rec({"val": real(x["pl_insol"]), "hierr": real(x["pl_insolerr1"]), "loerr": real(x["pl_insolerr2"]), "lim": boolean(x["pl_insollim"])}),
                "transit_depth": rec({"val": real(x["pl_trandep"]), "hierr": real(x["pl_trandeperr1"]), "loerr": real(x["pl_trandeperr2"]), "lim": boolean(x["pl_trandeplim"])}),
                "transit_duration": rec({"val": real(x["pl_trandur"]), "hierr": real(x["pl_trandurerr1"]), "loerr": real(x["pl_trandurerr2"]), "lim": boolean(x["pl_trandurlim"])}),
                "transit_midpoint": rec({"val": real(x["pl_tranmid"]), "hierr": real(x["pl_tranmiderr1"]), "loerr": real(x["pl_tranmiderr2"]), "lim": boolean(x["pl_tranmidlim"])}),
                "timesystem_reference": string(x["pl_tsystemref"]),
                "impact_parameter": rec({"val": real(x["pl_imppar"]), "hierr": real(x["pl_impparerr1"]), "loerr": real(x["pl_impparerr2"]), "lim": boolean(x["pl_impparlim"])}),
                "occultation_depth": rec({"val": real(x["pl_occdep"]), "hierr": real(x["pl_occdeperr1"]), "loerr": real(x["pl_occdeperr2"]), "lim": boolean(x["pl_occdeplim"])}),
                "ratio_planetdistance_starradius": rec({"val": real(x["pl_ratdor"]), "hierr": real(x["pl_ratdorerr1"]), "loerr": real(x["pl_ratdorerr2"]), "lim": boolean(x["pl_ratdorlim"])}),
                "ratio_planetradius_starradius": rec({"val": real(x["pl_ratror"]), "hierr": real(x["pl_ratrorerr1"]), "loerr": real(x["pl_ratrorerr2"]), "lim": boolean(x["pl_ratrorlim"])}),
                "reference_link": string(x["pl_def_reflink"]),
                "discovery": rec({"year": integer(x["pl_disc"]), "link": string(x["pl_disc_reflink"]), "locale": string(x["pl_locale"]), "facility": string(x["pl_facility"]), "telescope": string(x["pl_telescope"]), "instrument": string(x["pl_instrument"])}),
                "num_parameters": integer(x["pl_st_npar"]),
                "encyclopedia_link": string(x["pl_pelink"]),
                "explorer_link": string(x["pl_edelink"]),
                "publication_date": string(x["pl_publ_date"])
                })

before = stars.values()

import json
json.dump(before, open("planets.json", "wb"))
os.system("gzip -k planets.json")

from oamap.schema import *

def boolean(doc=None, nullable=False):
    return Primitive("bool_", doc=doc, nullable=nullable)

def integer(doc=None, nullable=False):
    return Primitive("i4", doc=doc, nullable=nullable)

def real(doc=None, nullable=False):
    return Primitive("f4", doc=doc, nullable=nullable)

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
        opticalband = Pointer(string(), doc="Optical Magnitude Band", nullable=True),   # st_optband
        temperature = Record(
          name = "ValueAsymErrBlend",
          doc = "Temperature of the star as modeled by a black body emitting the same total amount of electromagnetic radiation",
          nullable = True,
          fields = dict(
            val = real("Effective Temperature [K]", nullable=True),                 # st_teff
            hierr = real("Effective Temperature Upper Unc. [K]", nullable=True),    # st_tefferr1
            loerr = real("Effective Temperature Lower Unc. [K]", nullable=True),    # st_tefferr2
            lim = boolean("Effective Temperature Limit Flag", nullable=True),       # st_tefflim
            blend = boolean("Effective Temperature Blend Flag", nullable=True)      # st_teffblend
          )
        ),
        mass = Record(
          name = "ValueAsymErrBlend",
          doc = "Amount of matter contained in the star, measured in units of masses of the Sun",
          nullable = True,
          fields = dict(
            val = real("Stellar Mass [Solar mass]", nullable=True),                 # st_mass
            hierr = real("Stellar Mass Upper Unc. [Solar mass]", nullable=True),    # st_masserr1
            loerr = real("Stellar Mass Lower Unc. [Solar mass]", nullable=True),    # st_masserr2
            lim = boolean("Stellar Mass Limit Flag", nullable=True),                # st_masslim
            blend = boolean("Stellar Mass Blend Flag", nullable=True)               # st_massblend
          )
        ),
        radius = Record(
          name = "ValueAsymErrBlend",
          doc = "Length of a line segment from the center of the star to its surface, measured in units of radius of the Sun",
          nullable = True,
          fields = dict(
            val = real("Stellar Radius [Solar radii]", nullable=True),              # st_rad
            hierr = real("Stellar Radius Upper Unc. [Solar radii]", nullable=True), # st_raderr1
            loerr = real("Stellar Radius Lower Unc. [Solar radii]", nullable=True), # st_raderr2
            lim = boolean("Stellar Radius Limit Flag", nullable=True),              # st_radlim
            blend = boolean("Stellar Radius Blend Flag", nullable=True)              # st_radblend
          )
        ),
        galactic = Record(
          name = "Coordinate",
          doc = "Coordinates with respect to the plane of the galaxy in degrees",
          fields = dict(
            longitude = real("Galactic Longitude [deg]"),                           # st_glon
            latitude = real("Galactic Latitude [deg]")                              # st_glat
          )
        ),
        ecliptic = Record(
          name = "Coordinate",
          doc = "Coordinates with respect to the plane of the ecliptic in degrees",
          fields = dict(
            longitude = real("Ecliptic Longitude [deg]"),                           # st_elon
            latitude = real("Ecliptic Latitude [deg]")                              # st_elat
          )
        ),
        parallax = Record(
          name = "ValueAsymErrBlend",
          doc = "Difference in the angular position of a star as measured at two opposite positions within the Earth's orbit",
          nullable = True,
          fields = dict(
            val = real("Parallax [mas]", nullable=True),                            # st_plx
            hierr = real("Parallax Upper Unc. [mas]", nullable=True),               # st_plxerr1
            loerr = real("Parallax Lower Unc. [mas]", nullable=True),               # st_plxerr2
            lim = boolean("Parallax Limit Flag", nullable=True),                    # st_plxlim
            blend = boolean("Parallax Blend Flag", nullable=True)                   # st_plxblend
          )
        ),
        distance = Record(
          name = "ValueAsymErrBlend",
          doc = "Distance to the planetary system in units of parsecs",
          nullable = True,
          fields = dict(
            val = real("Distance [pc]", nullable=True),                             # st_dist
            hierr = real("Distance Upper Unc. [pc]", nullable=True),                # st_disterr1
            loerr = real("Distance Lower Unc. [pc]", nullable=True),                # st_disterr2
            lim = boolean("Distance Limit Flag", nullable=True),                    # st_distlim
            blend = boolean("Optical Magnitude Blend Flag", nullable=True),         # st_optmagblend
          )
        ),
        propermotion = Record(
          name = "ProperMotion",
          doc = "Angular change over time as seen from the center of mass of the Solar System",
          nullable = True,
          fields = dict(
            ra = Record(
              name = "ValueErr",
              doc = "Proper motion in right ascension",
              fields = dict(
                val = real("Proper Motion (RA) [mas/yr]", nullable=True),           # st_pmra
                err = real("Proper Motion (RA) Unc. [mas/yr]", nullable=True),      # st_pmraerr
                lim = boolean("Proper Motion (RA) Limit Flag", nullable=True)       # st_pmralim
              )
            ),
            dec = Record(
              name = "ValueErr",
              doc = "Proper motion in declination",
              fields = dict(
                val = real("Proper Motion (Dec) [mas/yr]", nullable=True),          # st_pmdec
                err = real("Proper Motion (Dec) Unc. [mas/yr]", nullable=True),     # st_pmdecerr
                lim = boolean("Proper Motion (Dec) Limit Flag", nullable=True)      # st_pmdeclim
              )
            ),
            total = Record(
              name = "ValueErrBlend",
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
          name = "GAIAMeasurements",
          nullable = True,
          fields = dict(
            gband = Record(
              name = "ValueErr",
              fields = dict(
                val = real(doc="G-band (Gaia) [mag]", nullable=True),               # gaia_gmag
                err = real(doc="G-band (Gaia) Unc. [mag]", nullable=True),          # gaia_gmagerr
                lim = boolean(doc="G-band (Gaia) Limit Flag", nullable=True)      # gaia_gmaglim
              )
            ),
            parallax = Record(
              name = "ValueAsymErr",
              doc = "Difference in the angular position of a star as measured at two opposite positions within the Earth's orbit",
              nullable = True,
              fields = dict(
                val = real(doc="Gaia Parallax [mas]", nullable=True),               # gaia_plx
                hierr = real(doc="Gaia Parallax Upper Unc. [mas]", nullable=True),  # gaia_plxerr1
                loerr = real(doc="Gaia Parallax Lower Unc. [mas]", nullable=True),  # gaia_plxerr2
                lim = boolean(doc="Gaia Parallax Limit Flag", nullable=True)      # gaia_plxlim
              )
            ),
            distance = Record(
              name = "ValueAsymErr",
              doc = "Distance to the planetary system in units of parsecs",
              nullable = True,
              fields = dict(
                val = real(doc="Gaia Distance [pc]", nullable=True),                # gaia_dist
                hierr = real(doc="Gaia Distance Upper Unc. [pc]", nullable=True),   # gaia_disterr1
                loerr = real(doc="Gaia Distance Lower Unc. [pc]", nullable=True),   # gaia_disterr2
                lim = boolean(doc="Gaia Distance Limit Flag", nullable=True)      # gaia_distlim
              )
            ),
            propermotion = Record(
              name = "GAIAProperMotion",
              doc = "Angular change over time as seen from the center of mass of the Solar System",
              nullable = True,
              fields = dict(
                ra = Record(
                  name = "ValueErr",
                  doc = "Proper motion in right ascension",
                  fields = dict(
                    val = real(doc="Gaia Proper Motion (RA) [mas/yr]", nullable=True),       # gaia_pmra
                    err  = real(doc="Gaia Proper Motion (RA) Unc. [mas/yr]", nullable=True), # gaia_pmraerr
                    lim = boolean(doc="Gaia Proper Motion (RA) Limit Flag", nullable=True)   # gaia_pmralim
                  ),
                ),
                dec = Record(
                  name = "ValueErr",
                  doc = "Proper motion in declination",
                  fields = dict(
                    val = real(doc="Gaia Proper Motion (Dec) [mas/yr]", nullable=True),      # gaia_pmdec
                    err = real(doc="Gaia Proper Motion (Dec) Unc. [mas/yr]", nullable=True), # gaia_pmdecerr
                    lim = boolean(doc="Gaia Proper Motion (Dec) Limit Flag", nullable=True)  # gaia_pmdeclim
                  )
                ),
                total = Record(
                  name = "ValueErr",
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
          name = "ValueAsymErrBlend",
          doc = "Velocity of the star in the direction of the line of sight",
          nullable = True,
          fields = dict(
            val = real("Radial Velocity [km/s]", nullable=True),                    # st_radv
            hierr = real("Radial Velocity Upper Unc. [km/s]", nullable=True),       # st_radverr1
            loerr = real("Radial Velocity Lower Unc. [km/s]", nullable=True),       # st_radverr2
            lim = boolean("Radial Velocity Limit Flag", nullable=True),             # st_radvlim
            blend = boolean("Radial Velocity Blend Flag", nullable=True)            # st_radvblend
          )
        ),
        spectraltype = Record(
          name = "ValueStrErrBlend",
          doc = "Classification of the star based on their spectral characteristics following the Morgan-Keenan system",
          nullable = True,
          fields = dict(
            val = real("Spectral Type", nullable=True),                             # st_sp
            str = Pointer(string(), doc="Spectral Type", nullable=True),            # st_spstr
            err = real("Spectral Type Unc.", nullable=True),                        # st_sperr
            lim = boolean("Spectral Type Limit Flag", nullable=True),               # st_splim
            blend = boolean("Spectral Type Blend Flag", nullable=True)              # st_spblend
          )
        ),
        surfacegravity = Record(
          name = "ValueAsymErrBlend",
          doc = "Gravitational acceleration experienced at the stellar surface",
          nullable = True,
          fields = dict(
            val = real("Stellar Surface Gravity [log10(cm/s**2)]", nullable=True),                # st_logg
            hierr = real("Stellar Surface Gravity Upper Unc. [log10(cm/s**2)]", nullable=True),   # st_loggerr1
            loerr = real("Stellar Surface Gravity Lower Unc. [log10(cm/s**2)]", nullable=True),   # st_loggerr2
            lim = boolean("Stellar Surface Gravity Limit Flag", nullable=True),                   # st_logglim
            blend = boolean("Stellar Surface Gravity Blend Flag", nullable=True)                  # st_loggblend
          )
        ),
        luminosity = Record(
          name = "ValueAsymErrBlend",
          doc = "Amount of energy emitted by a star per unit time, measured in units of solar luminosities",
          nullable = True,
          fields = dict(
            val = real("Stellar Luminosity [log(Solar)]", nullable=True),                         # st_lum
            hierr = real("Stellar Luminosity Upper Unc. [log(Solar)]", nullable=True),            # st_lumerr1
            loerr = real("Stellar Luminosity Lower Unc. [log(Solar)]", nullable=True),            # st_lumerr2
            lim = boolean("Stellar Luminosity Limit Flag", nullable=True),                        # st_lumlim
            blend = boolean("Stellar Luminosity Blend Flag", nullable=True)                       # st_lumblend
          )
        ),
        density = Record(
          name = "ValueAsymErr",
          doc = "Amount of mass per unit of volume of the star",
          nullable = True,
          fields = dict(
            val = real("Stellar Density [g/cm**3]", nullable=True),                 # st_dens
            hierr = real("Stellar Density Upper Unc. [g/cm**3]", nullable=True),    # st_denserr1
            loerr = real("Stellar Density Lower Unc. [g/cm**3]", nullable=True),    # st_denserr2
            lim = boolean("Stellar Density Limit Flag", nullable=True)              # st_denslim
          )
        ),
        metallicity = Record(
          name = "ValueAsymErrBlendRatio",
          doc = "Measurement of the metal content of the photosphere of the star as compared to the hydrogen content",
          nullable = True,
          fields = dict(
            val = real("Stellar Metallicity [dex]", nullable=True),                 # st_metfe
            loerr = real("Stellar Metallicity Upper Unc. [dex]", nullable=True),    # st_metfeerr1
            hierr = real("Stellar Metallicity Lower Unc. [dex]", nullable=True),    # st_metfeerr2
            lim = boolean("Stellar Metallicity Limit Flag", nullable=True),         # st_metfelim
            blend = boolean("Stellar Metallicity Blend Flag", nullable=True),       # st_metfeblend
            ratio = Pointer(string(), doc="Metallicity Ratio: ([Fe/H] denotes iron abundance, [M/H] refers to a general metal content)", nullable=True)   # st_metratio
          )
        ),
        age = Record(
          name = "ValueAsymErr",
          doc = "The age of the host star",
          nullable = True,
          fields = dict(
            val = real("Stellar Age [Gyr]", nullable=True),                         # st_age
            hierr = real("Stellar Age Upper Unc. [Gyr]", nullable=True),            # st_ageerr1
            loerr = real("Stellar Age Lower Unc. [Gyr]", nullable=True),            # st_ageerr2
            lim = boolean("Stellar Age Limit Flag", nullable=True)                  # st_agelim
          )
        ),
        rotational_velocity = Record(
          name = "ValueAsymErrBlend",
          doc = "Rotational velocity at the equator of the star multiplied by the sine of the inclination",
          nullable = True,
          fields = dict(
            val = real("Rot. Velocity V*sin(i) [km/s]", nullable=True),                          # st_vsini
            hierr = real("Rot. Velocity V*sin(i) Upper Unc. [km/s]", nullable=True),             # st_vsinierr1
            loerr = real("Rot. Velocity V*sin(i) Lower Unc. [km/s]", nullable=True),             # st_vsinierr2
            lim = boolean("Rot. Velocity V*sin(i) Limit Flag", nullable=True),                   # st_vsinilim
            blend = boolean("Rot. Velocity V*sin(i) Blend Flag", nullable=True)                  # st_vsiniblend
          )
        ),
        activity = Record(
          name = "StellarActivity",
          doc = "Stellar activity in various metrics",
          nullable = True,
          fields = dict(
            sindex = Record(
              name = "ValueErrBlend",
              doc = "Chromospheric activity as measured by the S-index (ratio of the emission of the H and K Ca lines to that in nearby continuum)",
              nullable = True,
              fields = dict(
                val = real("Stellar Activity S-index", nullable=True),                           # st_acts
                err = real("Stellar Activity S-index Unc.", nullable=True),                      # st_actserr
                lim = boolean("Stellar Activity S-index Limit Flag", nullable=True),             # st_actslim
                blend = boolean("Stellar Activity S-index Blend Flag", nullable=True)            # st_actsblend
              )
            ),
            rindex = Record(
              name = "ValueErrBlend",
              doc = "Chromospheric activity as measured by the log(R' HK) index, with is based on the S-index, but excludes the photospheric component in the Ca lines",
              nullable = True,
              fields = dict(
                val = real("Stellar Activity log(R'HK)", nullable=True),                         # st_actr
                err = real("Stellar Activity log(R'HK) Unc.", nullable=True),                    # st_actrerr
                lim = boolean("Stellar Activity log(R'HK) Limit Flag", nullable=True),           # st_actrlim
                blend = boolean("Stellar Activity log(R'HK) Blend Flag", nullable=True)          # st_actrblend
              )
            ),
            xindex = Record(
              name = "ValueErrBlend",
              doc = "Stellar activity as measured by the total luminosity in X-rays",
              nullable = True,
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
          name = "Photometry",
          fields = dict(
            uband = Record(
              name = "ValueErrBlend",
              doc = "Brightness of the host star as measured using the U (Johnson) band in units of magnitudes",
              nullable = True,
              fields = dict(
                val = real("U-band (Johnson) [mag]", nullable=True),   # st_uj
                err = real("U-band (Johnson) Unc. [mag]", nullable=True),   # st_ujerr
                lim = boolean("U-band (Johnson) Limit Flag", nullable=True),   # st_ujlim
                blend = boolean("U-band (Johnson) Blend Flag", nullable=True)   # st_ujblend
              )
            ),
            vband = Record(
              name = "ValueErrBlend",
              doc = "Brightness of the host star as measured using the V (Johnson) band in units of magnitudes",
              nullable = True,
              fields = dict(
                val = real("V-band (Johnson) [mag]", nullable=True),   # st_vj
                err = real("V-band (Johnson) Unc. [mag]", nullable=True),   # st_vjerr
                lim = boolean("V-band (Johnson) Limit Flag", nullable=True),   # st_vjlim
                blend = boolean("V-band (Johnson) Blend Flag", nullable=True)   # st_vjblend
              )
            ),
            bband = Record(
              name = "ValueErrBlend",
              doc = "Brightness of the host star as measured using the B (Johnson) band in units of magnitudes",
              nullable = True,
              fields = dict(
                val = real("B-band (Johnson) [mag]", nullable=True),   # st_bj
                err = real("B-band (Johnson) Unc. [mag]", nullable=True),   # st_bjerr
                lim = boolean("B-band (Johnson) Limit Flag", nullable=True),        # st_bjlim
                blend = boolean("B-band (Johnson) Blend Flag", nullable=True)   # st_bjblend
              )
            ),
            rband = Record(
              name = "ValueErrBlend",
              doc = "Brightness of the host star as measured using the R (Cousins) band in units of magnitudes",
              nullable = True,
              fields = dict(
                val = real("R-band (Cousins) [mag]", nullable=True),   # st_rc
                err = real("R-band (Cousins) Unc. [mag]", nullable=True),        # st_rcerr
                lim = boolean("R-band (Cousins) Limit Flag", nullable=True),        # st_rclim
                blend = boolean("R-band (Cousins) Blend Flag", nullable=True)   # st_rcblend
              )
            ),
            iband = Record(
              name = "ValueErrBlend",
              doc = "Brightness of the host star as measured using the I (Cousins) band in units of magnitudes",
              nullable = True,
              fields = dict(
                val = real("I-band (Cousins) [mag]", nullable=True),   # st_ic
                err = real("I-band (Cousins) Unc. [mag]", nullable=True),   # st_icerr
                lim = boolean("I-band (Cousins) Limit Flag", nullable=True),   # st_iclim
                blend = boolean("I-band (Cousins) Blend Flag", nullable=True)   # st_icblend
              )
            ),
            jband = Record(
              name = "ValueErrBlend",
              doc = "Brightness of the host star as measured using the J (2MASS) band in units of magnitudes",
              nullable = True,
              fields = dict(
                val = real("J-band (2MASS) [mag]", nullable=True),   # st_j
                err = real("J-band (2MASS) Unc. [mag]", nullable=True),   # st_jerr
                lim = boolean("J-band (2MASS) Limit Flag", nullable=True),   # st_jlim
                blend = boolean("J-band (2MASS) Blend Flag", nullable=True)   # st_jblend
              )
            ),
            hband = Record(
              name = "ValueErrBlend",
              doc = "Brightness of the host star as measured using the H (2MASS) band in units of magnitudes",
              nullable = True,
              fields = dict(
                val = real("H-band (2MASS) [mag]", nullable=True),   # st_h
                err = real("H-band (2MASS) Unc. [mag]", nullable=True),   # st_herr
                lim = boolean("H-band (2MASS) Limit Flag", nullable=True),   # st_hlim
                blend = boolean("H-band (2MASS) Blend Flag", nullable=True)   # st_hblend
              )
            ),
            kband = Record(
              name = "ValueErrBlend",
              doc = "Brightness of the host star as measured using the K (2MASS) band in units of magnitudes",
              nullable = True,
              fields = dict(
                val = real("Ks-band (2MASS) [mag]", nullable=True),   # st_k
                err = real("Ks-band (2MASS) Unc. [mag]", nullable=True),        # st_kerr
                lim = boolean("Ks-band (2MASS) Limit Flag", nullable=True),        # st_klim
                blend = boolean("Ks-band (2MASS) Blend Flag", nullable=True)        # st_kblend
              )
            ),
            wise1 = Record(
              name = "ValueErrBlend",
              doc = "Brightness of the host star as measured using the 3.4um (WISE) band in units of magnitudes",
              nullable = True,
              fields = dict(
                val = real("WISE 3.4um [mag]", nullable=True),   # st_wise1
                err = real("WISE 3.4um Unc. [mag]", nullable=True),        # st_wise1err
                lim = boolean("WISE 3.4um Limit Flag", nullable=True),        # st_wise1lim
                blend = boolean("WISE 3.4um Blend Flag", nullable=True)   # st_wise1blend
              )
            ),
            wise2 = Record(
              name = "ValueErrBlend",
              doc = "Brightness of the host star as measured using the 4.6um (WISE) band in units of magnitudes",
              nullable = True,
              fields = dict(
                val = real("WISE 4.6um [mag]", nullable=True),   # st_wise2
                err = real("WISE 4.6um Unc. [mag]", nullable=True),        # st_wise2err
                lim = boolean("WISE 4.6um Limit Flag", nullable=True),        # st_wise2lim
                blend = boolean("WISE 4.6um Blend Flag", nullable=True)   # st_wise2blend
              )
            ),
            wise3 = Record(
              name = "ValueErrBlend",
              doc = "Brightness of the host star as measured using the 12.um (WISE) band in units of magnitudes",
              nullable = True,
              fields = dict(
                val = real("WISE 12.um [mag]", nullable=True),   # st_wise3
                err = real("WISE 12.um Unc. [mag]", nullable=True),   # st_wise3err
                lim = boolean("WISE 12.um Limit Flag", nullable=True),   # st_wise3lim
                blend = boolean("WISE 12.um Blend Flag", nullable=True)   # st_wise3blend
              )
            ),
            wise4 = Record(
              name = "ValueErrBlend",
              doc = "Brightness of the host star as measured using the 22.um (WISE) band in units of magnitudes",
              nullable = True,
              fields = dict(
                val = real("WISE 22.um [mag]", nullable=True),   # st_wise4
                err = real("WISE 22.um Unc. [mag]", nullable=True),   # st_wise4err
                lim = boolean("WISE 22.um Limit Flag", nullable=True),   # st_wise4lim
                blend = boolean("WISE 22.um Blend Flag", nullable=True)   # st_wise4blend
              )
            ),
            irac1 = Record(
              name = "ValueErrBlend",
              doc = "Brightness of the host star as measured using the 3.6um (IRAC) band in units of magnitudes",
              nullable = True,
              fields = dict(
                val = real("IRAC 3.6um [mag]", nullable=True),   # st_irac1
                err = real("IRAC 3.6um Unc. [mag]", nullable=True),   # st_irac1err
                lim = boolean("IRAC 3.6um Limit Flag", nullable=True),   # st_irac1lim
                blend = boolean("IRAC 3.6um Blend Flag", nullable=True)   # st_irac1blend
              )
            ),
            irac2 = Record(
              name = "ValueErrBlend",
              doc = "Brightness of the host star as measured using the 4.5um (IRAC) band in units of magnitudes",
              nullable = True,
              fields = dict(
                val = real("IRAC 4.5um [mag]", nullable=True),   # st_irac2
                err = real("IRAC 4.5um Unc. [mag]", nullable=True),        # st_irac2err
                lim = boolean("IRAC 4.5um Limit Flag", nullable=True),        # st_irac2lim
                blend = boolean("IRAC 4.5um Blend Flag", nullable=True)   # st_irac2blend
              )
            ),
            irac3 = Record(
              name = "ValueErrBlend",
              doc = "Brightness of the host star as measured using the 5.8um (IRAC) band in units of magnitudes",
              nullable = True,
              fields = dict(
                val = real("IRAC 5.8um [mag]", nullable=True),   # st_irac3
                err = real("IRAC 5.8um Unc. [mag]", nullable=True),        # st_irac3err
                lim = boolean("IRAC 5.8um Limit Flag", nullable=True),        # st_irac3lim
                blend = boolean("IRAC 5.8um Blend Flag", nullable=True)   # st_irac3blend
              )
            ),
            irac4 = Record(
              name = "ValueErrBlend",
              doc = "Brightness of the host star as measured using the 8.0um (IRAC) band in units of magnitudes",
              nullable = True,
              fields = dict(
                val = real("IRAC 8.0um [mag]", nullable=True),   # st_irac4
                err = real("IRAC 8.0um Unc. [mag]", nullable=True),   # st_irac4err
                lim = boolean("IRAC 8.0um Limit Flag", nullable=True),   # st_irac4lim
                blend = boolean("IRAC 8.0um Blend Flag", nullable=True)   # st_irac4blend
              )
            ),
            mips1 = Record(
              name = "ValueErrBlend",
              doc = "Brightness of the host star as measured using the 24um (MIPS) band in units of magnitudes",
              nullable = True,
              fields = dict(
                val = real("MIPS 24um [mag]", nullable=True),   # st_mips1
                err = real("MIPS 24um Unc. [mag]", nullable=True),   # st_mips1err
                lim = boolean("MIPS 24um Limit Flag", nullable=True),   # st_mips1lim
                blend = boolean("MIPS 24um Blend Flag", nullable=True)   # st_mips1blend
              )
            ),
            mips2 = Record(
              name = "ValueErrBlend",
              doc = "Brightness of the host star as measured using the 70um (MIPS) band in units of magnitudes",
              nullable = True,
              fields = dict(
                val = real("MIPS 70um [mag]", nullable=True),   # st_mips2
                err = real("MIPS 70um Unc. [mag]", nullable=True),   # st_mips2err
                lim = boolean("MIPS 70um Limit Flag", nullable=True),   # st_mips2lim
                blend = boolean("MIPS 70um Blend Flag", nullable=True)   # st_mips2blend
              )
            ),
            mips3 = Record(
              name = "ValueErrBlend",
              doc = "Brightness of the host star as measured using the 160um (MIPS) band in units of magnitudes",
              nullable = True,
              fields = dict(
                val = real("MIPS 160um [mag]", nullable=True),   # st_mips3
                err = real("MIPS 160um Unc. [mag]", nullable=True),        # st_mips3err
                lim = boolean("MIPS 160um Limit Flag", nullable=True),        # st_mips3lim
                blend = boolean("MIPS 160um Blend Flag", nullable=True)   # st_mips3blend
              )
            ),
            iras1 = Record(
              name = "ValueErrBlend",
              doc = "Brightness of the host star as measured using the 12um (IRAS) band in units of Jy",
              nullable = True,
              fields = dict(
                val = real("IRAS 12um Flux [Jy]", nullable=True),   # st_iras1
                err = real("IRAS 12um Flux Unc. [Jy]", nullable=True),        # st_iras1err
                lim = boolean("IRAS 12um Flux Limit Flag", nullable=True),        # st_iras1lim
                blend = boolean("IRAS 12um Flux Blend Flag", nullable=True)   # st_iras1blend
              )
            ),
            iras2 = Record(
              name = "ValueErrBlend",
              doc = "Brightness of the host star as measured using the 25um (IRAS) band in units of Jy",
              nullable = True,
              fields = dict(
                val = real("IRAS 25um Flux [Jy]", nullable=True),   # st_iras2
                err = real("IRAS 25um Flux Unc. [Jy]", nullable=True),        # st_iras2err
                lim = boolean("IRAS 25um Flux Limit Flag", nullable=True),        # st_iras2lim
                blend = boolean("IRAS 25um Flux Blend Flag", nullable=True)        # st_iras2blend
              )
            ),
            iras3 = Record(
              name = "ValueErrBlend",
              doc = "Brightness of the host star as measured using the 60um (IRAS) band in units of Jy",
              nullable = True,
              fields = dict(
                val = real("IRAS 60um Flux [Jy]", nullable=True),        # st_iras3
                err = real("IRAS 60um Flux Unc. [Jy]", nullable=True),        # st_iras3err
                lim = boolean("IRAS 60um Flux Limit Flag", nullable=True),        # st_iras3lim
                blend = boolean("IRAS 60um Flux Blend Flag", nullable=True)        # st_iras3blend
              )
            ),
            iras4 = Record(
              name = "ValueErrBlend",
              doc = "Brightness of the host star as measured using the 100um (IRAS) band in units of Jy",
              nullable = True,
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
          name = "Color",
          fields = dict(
            ub_diff = Record(
              name = "ValueErrBlend",
              doc = "Color of the star as measured by the difference between U and B (Johnson) bands",
              nullable = True,
              fields = dict(
                val = real("U-B (Johnson) [mag]", nullable=True),        # st_umbj
                err = real("U-B (Johnson) Unc. [mag]", nullable=True),        # st_umbjerr
                lim = boolean("U-B (Johnson) Limit Flag", nullable=True),        # st_umbjlim
                blend = boolean("U-B (Johnson) Blend Flag", nullable=True)   # st_umbjblend
              )
            ),
            bv_diff = Record(
              name = "ValueErrBlend",
              doc = "Color of the star as measured by the difference between B and V (Johnson) bands",
              nullable = True,
              fields = dict(
                val = real("B-V (Johnson) [mag]", nullable=True),  # st_bmvj
                err = real("B-V (Johnson) Unc. [mag]", nullable=True),       # st_bmvjerr
                lim = boolean("B-V (Johnson) Limit Flag", nullable=True),       # st_bmvjlim
                blend = boolean("B-V (Johnson) Blend Flag", nullable=True)   # st_bmvjblend
              )
            ),
            vi_diff = Record(
              name = "ValueErrBlend",
              doc = "Color of the star as measured by the difference between V (Johnson) and I (Cousins) bands",
              nullable = True,
              fields = dict(
                val = real("V-I (Johnson-Cousins) [mag]", nullable=True),  # st_vjmic
                err = real("V-I (Johnson-Cousins) Unc. [mag]", nullable=True),       # st_vjmicerr
                lim = boolean("V-I (Johnson-Cousins) Limit Flag", nullable=True),       # st_vjmiclim
                blend = boolean("V-I (Johnson-Cousins) Blend Flag", nullable=True)        # st_vjmicblend
              )
            ),
            vr_diff = Record(
              name = "ValueErrBlend",
              doc = "Color of the star as measured by the difference between V (Johnson) and R (Cousins) bands",
              nullable = True,
              fields = dict(
                val = real("V-R (Johnson-Cousins) [mag]", nullable=True),       # st_vjmrc
                err = real("V-R (Johnson-Cousins) Unc. [mag]", nullable=True),       # st_vjmrcerr
                lim = boolean("V-R (Johnson-Cousins) Limit Flag", nullable=True),       # st_vjmrclim
                blend = boolean("V-R (Johnson-Cousins) Blend Flag", nullable=True)        # st_vjmrcblend
              )
            ),
            jh_diff = Record(
              name = "ValueErrBlend",
              doc = "Color of the star as measured by the difference between J and H (2MASS) bands",
              nullable = True,
              fields = dict(
                val = real("J-H (2MASS) [mag]", nullable=True),       # st_jmh2
                err = real("J-H (2MASS) Unc. [mag]", nullable=True),       # st_jmh2err
                lim = boolean("J-H (2MASS) Limit Flag", nullable=True),       # st_jmh2lim
                blend = boolean("J-H (2MASS) Blend Flag", nullable=True)        # st_jmh2blend
              )
            ),
            hk_diff = Record(
              name = "ValueErrBlend",
              doc = "Color of the star as measured by the difference between H and K (2MASS) bands",
              nullable = True,
              fields = dict(
                val = real("H-Ks (2MASS) [mag]", nullable=True),  # st_hmk2
                err = real("H-Ks (2MASS) Unc. [mag]", nullable=True),       # st_hmk2err
                lim = boolean("H-Ks (2MASS) Limit Flag", nullable=True),       # st_hmk2lim
                blend = boolean("H-Ks (2MASS) Blend Flag", nullable=True)        # st_hmk2blend
              )
            ),
            jk_diff = Record(
              name = "ValueErrBlend",
              doc = "Color of the star as measured by the difference between K and K (2MASS) bands",
              nullable = True,
              fields = dict(
                val = real("J-Ks (2MASS) [mag]", nullable=True),  # st_jmk2
                err = real("J-Ks (2MASS) Unc. [mag]", nullable=True),       # st_jmk2err
                lim = boolean("J-Ks (2MASS) Limit Flag", nullable=True),       # st_jmk2lim
                blend = boolean("J-Ks (2MASS) Blend Flag", nullable=True)        # st_jmk2blend
              )
            ),
            by_diff = Record(
              name = "ValueErrBlend",
              doc = "Color of the star as measured by the difference between b and y (Stromgren) bands",
              nullable = True,
              fields = dict(
                val = real("b-y (Stromgren) [mag]", nullable=True),  # st_bmy
                err = real("b-y (Stromgren) Unc. [mag]", nullable=True),       # st_bmyerr
                lim = boolean("b-y (Stromgren) Limit Flag", nullable=True),       # st_bmylim
                blend = boolean("b-y (Stromgren) Blend Flag", nullable=True)   # st_bmyblend
              )
            ),
            m1_diff = Record(
              name = "ValueErrBlend",
              doc = "Color of the star as measured by the m1 (Stromgren) system",
              nullable = True,
              fields = dict(
                val = real("m1 (Stromgren) [mag]", nullable=True),  # st_m1
                err = real("m1 (Stromgren) Unc. [mag]", nullable=True),       # st_m1err
                lim = boolean("m1 (Stromgren) Limit Flag", nullable=True),       # st_m1lim
                blend = boolean("m1 (Stromgren) Blend Flag", nullable=True)   # st_m1blend
              )
            ),
            c1_diff = Record(
              name = "ValueErrBlend",
              doc = "Color of the star as measured by the c1 (Stromgren) system",
              nullable = True,
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
              letter = Pointer(string(), doc="Planet Letter"),              # pl_letter
              discovery_method = Pointer(string(), doc="Discovery Method"), # pl_discmethod
              orbital_period = Record(
                name = "ValueAsymErr",
                doc = "Time the planet takes to make a complete orbit around the host star or system",
                nullable = True,
                fields = dict(
                  val = real("Orbital Period [days]", nullable=True),                 # pl_orbper
                  hierr = real("Orbital Period Upper Unc. [days]", nullable=True),    # pl_orbpererr1
                  loerr = real("Orbital Period Lower Unc. [days]", nullable=True),    # pl_orbpererr2
                  lim = boolean("Orbital Period Limit Flag", nullable=True)           # pl_orbperlim
                )
              ),
              semimajor_axis = Record(
                name = "ValueAsymErr",
                doc = "The longest diameter of an elliptic orbit, or for directly imaged planets, the projected separation in the plane of the sky",
                nullable = True,
                fields = dict(
                  val = real("Orbit Semi-Major Axis [AU]", nullable=True),               # pl_orbsmax
                  hierr = real("Orbit Semi-Major Axis Upper Unc. [AU]", nullable=True),  # pl_orbsmaxerr1
                  loerr = real("Orbit Semi-Major Axis Lower Unc. [AU]", nullable=True),  # pl_orbsmaxerr2
                  lim = boolean("Orbit Semi-Major Axis Limit Flag", nullable=True)       # pl_orbsmaxlim
                )
              ),
              eccentricity = Record(
                name = "ValueAsymErr",
                doc = "Amount by which the orbit of the planet deviates from a perfect circle",
                nullable = True,
                fields = dict(
                  val = real("Eccentricity", nullable=True),                     # pl_orbeccen
                  hierr = real("Eccentricity Upper Unc.", nullable=True),        # pl_orbeccenerr1
                  loerr = real("Eccentricity Lower Unc.", nullable=True),        # pl_orbeccenerr2
                  lim = boolean("Eccentricity Limit Flag", nullable=True)        # pl_orbeccenlim
                )
              ),
              inclination = Record(
                name = "ValueAsymErr",
                doc = "Angular distance of the orbital plane from the line of sight",
                nullable = True,
                fields = dict(
                  val = real("Inclination [deg]", nullable=True),                # pl_orbincl
                  hierr = real("Inclination Upper Unc. [deg]", nullable=True),   # pl_orbinclerr1
                  loerr = real("Inclination Lower Unc. [deg]", nullable=True),   # pl_orbinclerr2
                  lim = boolean("Inclination Limit Flag", nullable=True)         # pl_orbincllim
                )
              ),
              mass = Record(
                name = "ValueAsymErr",
                doc = "Amount of matter contained in the planet, measured in units of masses of Jupiter",
                nullable = True,
                fields = dict(
                  val = real("Planet Mass [Jupiter mass]", nullable=True),   # pl_massj
                  hierr = real("Planet Mass Upper Unc. [Jupiter mass]", nullable=True),        # pl_massjerr1
                  loerr = real("Planet Mass Lower Unc. [Jupiter mass]", nullable=True),        # pl_massjerr2
                  lim = boolean("Planet Mass Limit Flag", nullable=True)        # pl_massjlim
                )
              ),
              mass_sini = Record(
                name = "ValueAsymErr",
                doc = "Minimum mass of a planet as measured by radial velocity, measured in units of masses of Jupiter",
                nullable = True,
                fields = dict(
                  val = real("Planet M*sin(i) [Jupiter mass]", nullable=True),        # pl_msinij
                  hierr = real("Planet M*sin(i) Upper Unc. [Jupiter mass]", nullable=True),        # pl_msinijerr1
                  loerr = real("Planet M*sin(i) Lower Unc. [Jupiter mass]", nullable=True),        # pl_msinijerr2
                  lim = boolean("Planet M*sin(i) Limit Flag", nullable=True)        # pl_msinijlim
                )
              ),
              mass_best = Record(
                name = "ValueAsymErrProvenance",
                doc = "Best planet mass measurement in units of masses of Jupiter. Either Mass, M*sin(i)/sin(i), or M*sin(i). See provenance for source of the measurement.",
                nullable = True,
                fields = dict(
                  val = real("Planet Mass or M*sin(i)[Jupiter mass]", nullable=True),                  # pl_bmassj
                  hierr = real("Planet Mass or M*sin(i)Upper Unc. [Jupiter mass]", nullable=True),     # pl_bmassjerr1
                  loerr = real("Planet Mass or M*sin(i)Lower Unc. [Jupiter mass]", nullable=True),     # pl_bmassjerr2
                  lim = boolean("Planet Mass or M*sin(i)Limit Flag", nullable=True),                   # pl_bmassjlim
                  provenance = Pointer(string(), doc="Planet Mass or M*sin(i) Provenance", nullable=True)    # pl_bmassprov
                )
              ),
              radius = Record(
                name = "ValueAsymErr",
                doc = "Length of a line segment from the center of the planet to its surface, measured in units of radius of Jupiter",
                nullable = True,
                fields = dict(
                  val = real("Planet Radius [Jupiter radii]", nullable=True),   # pl_radj
                  hierr = real("Planet Radius Upper Unc. [Jupiter radii]", nullable=True),        # pl_radjerr1
                  loerr = real("Planet Radius Lower Unc. [Jupiter radii]", nullable=True),        # pl_radjerr2
                  lim = boolean("Planet Radius Limit Flag", nullable=True)        # pl_radjlim
                )
              ),
              density = Record(
                name = "ValueAsymErr",
                doc = "Amount of mass per unit of volume of the planet",
                nullable = True,
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
              angular_separation = Record(
                name = "ValueAsymErrNoLim",
                doc = "The calculated angular separation (semi-major axis/distance) between the star and the planet. This value is only calculated for systems with both a semi-major axis and a distance value.",
                nullable = True,
                fields = dict(
                  val = real("Calculated Angular Separation [mas]", nullable=True),   # pl_angsep
                  hierr = real("Calculated Angular Separation Upper Unc. [mas]", nullable=True),        # pl_angseperr1
                  loerr = real("Calculated Angular Separation Lower Unc. [mas]", nullable=True)        # pl_angseperr2
                )
              ),
              periastron = Record(
                name = "ValueAsymErr",
                doc = "The time at which the orbiting body is at its closest approach to the star it orbits (i.e. is at periastron)",
                nullable = True,
                fields = dict(
                  val = real("Time of Periastron [days]", nullable=True),        # pl_orbtper
                  hierr = real("Time of Periastron Upper Unc. [days]", nullable=True),        # pl_orbtpererr1
                  loerr = real("Time of Periastron Lower Unc. [days]", nullable=True),        # pl_orbtpererr2
                  lim = boolean("Time of Periastron Limit Flag", nullable=True)        # pl_orbtperlim
                )
              ),
              longitude_periastron = Record(
                name = "ValueAsymErr",
                doc = "The angular separation between the ascending node of the orbit and the location in the orbit of periastron",
                nullable = True,
                fields = dict(
                  val = real("Long. of Periastron [deg]", nullable=True),   # pl_orblper
                  hierr = real("Long. of Periastron Upper Unc. [deg]", nullable=True),        # pl_orblpererr1
                  loerr = real("Long. of Periastron Lower Unc. [deg]", nullable=True),        # pl_orblpererr2
                  lim = boolean("Long. of Periastron Limit Flag", nullable=True)        # pl_orblperlim
                )
              ),
              radial_velocity = Record(
                name = "ValueAsymErr",
                doc = "Half the peak-to-peak amplitude of variability in the stellar radial velocity",
                nullable = True,
                fields = dict(
                  val = real("Radial Velocity Amplitude [m/s]", nullable=True),   # pl_rvamp
                  hierr = real("Radial Velocity Amplitude Upper Unc. [m/s]", nullable=True),        # pl_rvamperr1
                  loerr = real("Radial Velocity Amplitude Lower Unc. [m/s]", nullable=True),        # pl_rvamperr2
                  lim = boolean("Radial Velocity Amplitude Limit Flag", nullable=True)        # pl_rvamplim
                )
              ),
              equilibrium_temperature = Record(
                name = "ValueAsymErr",
                doc = "The equilibrium temperature of the planet as modeled by a black body heated only by its host star, or for directly imaged planets, the effective temperature of the planet required to match the measured luminosity if the planet were a black body",
                nullable = True,
                fields = dict(
                  val = real("Equilibrium Temperature [K]", nullable=True),        # pl_eqt
                  hierr = real("Equilibrium Temperature Upper Unc. [K]", nullable=True),        # pl_eqterr1
                  loerr = real("Equilibrium Temperature Lower Unc. [K]", nullable=True),        # pl_eqterr2
                  lim = boolean("Equilibrium Temperature Limit Flag", nullable=True)        # pl_eqtlim
                )
              ),
              isolation_flux = Record(
                name = "ValueAsymErr",
                doc = "Insolation flux is another way to give the equilibrium temperature. It's given in units relative to those measured for the Earth from the Sun",
                nullable = True,
                fields = dict(
                  val = real("Insolation Flux [Earth flux]", nullable=True),   # pl_insol
                  hierr = real("Insolation Flux Upper Unc. [Earth flux]", nullable=True),        # pl_insolerr1
                  loerr = real("Insolation Flux Lower Unc. [Earth flux]", nullable=True),        # pl_insolerr2
                  lim = boolean("Insolation Flux Limit Flag", nullable=True)        # pl_insollim
                )
              ),
              transit_depth = Record(
                name = "ValueAsymErr",
                doc = "The size of the relative flux decrement caused by the orbiting body transiting in front of the star",
                nullable = True,
                fields = dict(
                  val = real("Transit Depth [percent]", nullable=True),        # pl_trandep
                  hierr = real("Transit Depth Upper Unc. [percent]", nullable=True),        # pl_trandeperr1
                  loerr = real("Transit Depth Lower Unc. [percent]", nullable=True),        # pl_trandeperr2
                  lim = boolean("Transit Depth Limit Flag", nullable=True)        # pl_trandeplim
                )
              ),
              transit_duration = Record(
                name = "ValueAsymErr",
                doc = "The length of time from the moment the planet begins to cross the stellar limb to the moment the planet finishes crossing the stellar limb",
                nullable = True,
                fields = dict(
                  val = real("Transit Duration [days]", nullable=True),        # pl_trandur
                  hierr = real("Transit Duration Upper Unc. [days]", nullable=True),        # pl_trandurerr1
                  loerr = real("Transit Duration Lower Unc. [days]", nullable=True),        # pl_trandurerr2
                  lim = boolean("Transit Duration Limit Flag", nullable=True)        # pl_trandurlim
                )
              ),
              transit_midpoint = Record(
                name = "ValueAsymErr",
                doc = "The time given by the average of the time the planet begins to cross the stellar limb and the time the planet finishes crossing the stellar limb",
                nullable = True,
                fields = dict(
                  val = real("Transit Midpoint [days]", nullable=True),   # pl_tranmid
                  hierr = real("Transit Midpoint Upper Unc. [days]", nullable=True),        # pl_tranmiderr1
                  loerr = real("Transit Midpoint Lower Unc. [days]", nullable=True),        # pl_tranmiderr2
                  lim = boolean("Transit Midpoint Limit Flag", nullable=True)        # pl_tranmidlim
                )
              ),
              timesystem_reference = Pointer(string(), doc="Time System Reference", nullable=True),  # pl_tsystemref
              impact_parameter = Record(
                name = "ValueAsymErr",
                doc = "The sky-projected distance between the center of the stellar disc and the center of the planet disc at conjunction, normalized by the stellar radius",
                nullable = True,
                fields = dict(
                  val = real("Impact Parameter", nullable=True),   # pl_imppar
                  hierr = real("Impact Parameter Upper Unc.", nullable=True),        # pl_impparerr1
                  loerr = real("Impact Parameter Lower Unc.", nullable=True),        # pl_impparerr2
                  lim = boolean("Impact Parameter Limit Flag", nullable=True)        # pl_impparlim
                )
              ),
              occultation_depth = Record(
                name = "ValueAsymErr",
                doc = "Depth of occultation of secondary eclipse",
                nullable = True,
                fields = dict(
                  val = real("Occultation Depth [percentage]", nullable=True),   # pl_occdep
                  hierr = real("Occultation Depth Upper Unc. [percentage]", nullable=True),        # pl_occdeperr1
                  loerr = real("Occultation Depth Lower Unc. [percentage]", nullable=True),        # pl_occdeperr2
                  lim = boolean("Occultation Depth Limit Flag", nullable=True)        # pl_occdeplim
                )
              ),
              ratio_planetdistance_starradius = Record(
                name = "ValueAsymErr",
                doc = "The distance between the planet and the star at mid-transit divided by the stellar radius. For the case of zero orbital eccentricity, the distance at mid-transit is the semi-major axis of the planetary orbit.",
                nullable = True,
                fields = dict(
                  val = real("Ratio of Distance to Stellar Radius", nullable=True),   # pl_ratdor
                  hierr = real("Ratio of Distance to Stellar Radius Upper Unc.", nullable=True),        # pl_ratdorerr1
                  loerr = real("Ratio of Distance to Stellar Radius Lower Unc.", nullable=True),        # pl_ratdorerr2
                  lim = boolean("Ratio of Distance to Stellar Radius Limit Flag", nullable=True)        # pl_ratdorlim
                )
              ),
              ratio_planetradius_starradius = Record(
                name = "ValueAsymErr",
                doc = "The planet radius divided by the stellar radius",
                nullable = True,
                fields = dict(
                  val = real("Ratio of Planet to Stellar Radius", nullable=True),   # pl_ratror
                  hierr = real("Ratio of Planet to Stellar Radius Upper Unc.", nullable=True),        # pl_ratrorerr1
                  loerr = real("Ratio of Planet to Stellar Radius Lower Unc.", nullable=True),        # pl_ratrorerr2
                  lim = boolean("Ratio of Planet to Stellar Radius Limit Flag", nullable=True)        # pl_ratrorlim
                )
              ),
              reference_link = string("Reference for publication used for default parameter"), # pl_def_reflink
              discovery = Record(
                name = "Discovery",
                fields = dict(
                  year = integer("Year the planet was discovered"), # pl_disc
                  link = string("Reference name for discovery publication"), # pl_disc_reflink
                  locale = Pointer(string(), doc="Location of observation of planet discovery (Ground or Space)"), # pl_locale
                  facility = Pointer(string(), doc="Name of facility of planet discovery observations"), # pl_facility
                  telescope = string("Name of telescope of planet discovery observations"), # pl_telescope
                  instrument = string("Name of instrument of planet discovery observations"), # pl_instrument
                )
              ),
              num_parameters = integer("Number of Stellar and Planet Parameters", nullable=True),   # pl_st_npar
              encyclopedia_link = string("Link to the planet page in the Exoplanet Encyclopaedia", nullable=True),  # pl_pelink
              explorer_link = string("Link to the planet page in Exoplanet Data Explorer", nullable=True),  # pl_edelink
              publication_date = Pointer(string(), doc="Publication Date of the planet discovery referee publication", nullable=True) # pl_publ_date
            )
          ) # planet Record
        ) # planets List
      )
    )
  )
)

import avro.schema

def convert2avro(schema, names):
    if isinstance(schema, Pointer):
        out = convert2avro(schema.target, names)

    elif isinstance(schema, Primitive):
        if issubclass(schema.dtype.type, (numpy.bool_, numpy.bool)):
            out = {"type": "boolean"}
        elif issubclass(schema.dtype.type, numpy.integer):
            out = {"type": "int"}
        elif issubclass(schema.dtype.type, numpy.floating):
            out = {"type": "float"}
        else:
            raise AssertionError

    elif isinstance(schema, List) and schema.name == "UTF8String":
        out = {"type": "string"}

    elif isinstance(schema, List):
        out = {"type": "array", "items": convert2avro(schema.content, names)}

    elif isinstance(schema, Record):
        out = {"type": "record", "name": schema.name, "fields": [{"name": n, "type": convert2avro(x, names)} for n, x in schema.fields.items()]}

        if schema.name not in names:
            names[schema.name] = out
        else:
            assert names[schema.name] == out, "{}:\n{}\n{}".format(schema.name, names[schema.name], out)
            out = schema.name

    else:
        raise AssertionError

    if schema.nullable:
        return ["null", out]
    else:
        return out

avroschema = avro.schema.make_avsc_object(convert2avro(schema.content, {}))

import avro.datafile
import avro.io

writer = avro.datafile.DataFileWriter(open("planets_uncompressed.avro", "wb"), avro.io.DatumWriter(), avroschema)
for star in before:
    writer.append(star)
writer.close()

writer = avro.datafile.DataFileWriter(open("planets.avro", "wb"), avro.io.DatumWriter(), avroschema, codec="deflate")
for star in before:
    writer.append(star)
writer.close()

import bson

writer = open("planets.bson", "wb")
for star in before:
    writer.write(bson.BSON.encode(star))
writer.close()
os.system("gzip -k planets.bson")

schema.tojsonfile(open("planets/schema.json", "wb"))

import oamap.fill

generator = schema.generator()
fillables = oamap.fill.fromdata(before, generator=generator, pointer_fromequal=True)
after = schema(fillables)

packedarrays = generator.save(fillables)
after2 = schema(packedarrays)

import numpy

for n, x in packedarrays.items():
    numpy.save("planets/{0}.npy".format(n), x)

os.system("cp -a planets planets_gz")
for n in packedarrays:
    os.system("gzip planets_gz/{}.npy".format(n))

numpy.savez("planets_uncompressed.npz", packedarrays)
numpy.savez_compressed("planets.npz", packedarrays)

############################################################################################################

import time

import json
before = json.load(open("planets.json"))

import ROOT

file = ROOT.TFile("planets.root", "RECREATE")
file.SetCompressionAlgorithm(1)
file.SetCompressionLevel(4)

def makebranches(schema, name, nested):
    if isinstance(schema, Primitive):
        if issubclass(schema.dtype.type, (numpy.bool, numpy.bool_)):
            ROOT.gInterpreter.Declare("""
Char_t {0}[{1}];
void assign_{0}(Char_t value, int index) {{
    {0}[index] = value;
}}
""".format(name, "8" if nested else "1"))
            ROOT.gInterpreter.ProcessLine("""
planets->Branch("{0}", {0}, "{0}/B{2}");
""".format(name, "8" if nested else "1", "[num_planets]" if nested else ""))

        elif schema.dtype == numpy.dtype(numpy.int32):
            ROOT.gInterpreter.Declare("""
int32_t {0}[{1}];
void assign_{0}(int32_t value, int index) {{
    {0}[index] = value;
}}
""".format(name, "8" if nested else "1"))
            ROOT.gInterpreter.ProcessLine("""
planets->Branch("{0}", {0}, "{0}/I{2}");
""".format(name, "8" if nested else "1", "[num_planets]" if nested else ""))

        elif schema.dtype == numpy.dtype(numpy.float32):
            ROOT.gInterpreter.Declare("""
float {0}[{1}];
void assign_{0}(float value, int index) {{
    {0}[index] = value;
}}
""".format(name, "8" if nested else "1"))
            ROOT.gInterpreter.ProcessLine("""
planets->Branch("{0}", {0}, "{0}/F{2}");
""".format(name, "8" if nested else "1", "[num_planets]" if nested else ""))

        else:
            raise AssertionError

    elif isinstance(schema, List) and schema.name == "UTF8String":
        ROOT.gInterpreter.Declare("""
char {0}[150 * {1}];
int {0}_position;
void assign_{0}(const char* value, int index) {{
    if (index == 0)
        {0}_position = 0;
    strcpy(&{0}[{0}_position], value);
    {0}_position += strlen(value);
}}
""".format(name, "8" if nested else "1"))
        ROOT.gInterpreter.ProcessLine("""
planets->Branch("{0}", {0}, "{0}/C");
""".format(name, "8" if nested else "1"))

    elif isinstance(schema, List):
        makebranches(schema.content, name, True)

    elif isinstance(schema, Record):
        for n, x in schema.fields.items():
            makebranches(x, n if name is None else name + "_" + n, nested)

    elif isinstance(schema, Pointer):
        makebranches(schema.target, name, nested)

    else:
        raise AssertionError

def fillbranches(schema, name, value, index):
    if isinstance(schema, Primitive):
        exec("ROOT.assign_{0}({1}, {2})".format(name, repr(0 if value is None else value), repr(index)))

    elif isinstance(schema, List) and schema.name == "UTF8String":
        exec("ROOT.assign_{0}({1}, {2})".format(name, repr("" if value is None else value), repr(index)))

    elif isinstance(schema, List):
        for i, x in enumerate(value):
            fillbranches(schema.content, name, x, i)

    elif isinstance(schema, Record):
        for n, x in schema.fields.items():
            fillbranches(x, n if name is None else name + "_" + n, None if value is None else value[n], index)

    elif isinstance(schema, Pointer):
        fillbranches(schema.target, name, value, index)

tree = ROOT.TTree("planets", "")
makebranches(schema.content, "branch", False)

startTime = time.time()
for i, x in enumerate(before):
    fillbranches(schema.content, "branch", x, 0)
    tree.Fill()
    print i, len(before), time.time() - startTime, "seconds", "len(planets)", len(x["planets"])

tree.Write()
file.Close()
