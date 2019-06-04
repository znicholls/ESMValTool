"""
*********************************************************************
APPLICATE/TRR Ocean Diagnostics
*********************************************************************
"""
import logging
import os
from collections import OrderedDict
from netCDF4 import Dataset, num2date
import numpy as np
import os
import matplotlib as mpl
import matplotlib.pylab as plt
import math
from matplotlib import cm
#import seawater as sw
from collections import OrderedDict
from cdo import Cdo
import cmocean.cm as cmo
from mpl_toolkits.basemap import Basemap
from mpl_toolkits.basemap import addcyclic
import pandas as pd
import pyresample
from scipy.interpolate import interp1d
import ESMF
import pyproj
from esmvaltool.diag_scripts.ocean3d.utils import genfilename
from esmvaltool.diag_scripts.ocean3d.regions import hofm_regions, transect_points

logger = logging.getLogger(os.path.basename(__file__))
mpl.use('agg')  #noqa

def load_meta(datapath, fxpath=None):
    datafile = Dataset(datapath)

    if fxpath:
        datafile_area = Dataset(fxpath)
        areacello = datafile_area.variables['areacello'][:]
    else:
        areacello = None

    lon = datafile.variables['lon'][:]
    lat = datafile.variables['lat'][:]
    lev = datafile.variables['lev'][:]
    time = num2date(datafile.variables['time'][:],
                    datafile.variables['time'].units)
    if lon.ndim == 2:
        lon2d, lat2d = lon, lat
    elif lon.ndim == 1:
        lon2d, lat2d = np.meshgrid(lon, lat)

    return [datafile, lon2d, lat2d, lev, time, areacello]

def hofm_data(model_filenames, mmodel, cmor_var, areacello_fx, max_level,
              region, diagworkdir):
    ''' Extract data for Hovmoeller diagrams from monthly values.
    Saves the data to files in `diagworkdir`.

    Parameters
    ----------
    model_filenames: OrderedDict
        OrderedDict with model names as keys and input files as values.
    mmodel: str
        model name that will be processed.
    cmor_var: str
        name of the CMOR variable
    areacello_fx: OrderedDict.
        dictionary with model names as keys and paths to fx files as values.
    max_level: float
        maximum depth level the Hovmoeller diagrams should go to.
    region: str
        name of the region predefined in `hofm_regions` function.
    diagworkdir: str
        path to work directory.

    Returns
    -------
    None
    '''
    logger.info("Extract  %s data for %s, region %s", cmor_var, mmodel, region)
    metadata = load_meta(datapath=model_filenames[mmodel],
                         fxpath=areacello_fx[mmodel])
    datafile, lon2d, lat2d, lev, time, areacello = metadata

    lev_limit = lev[lev <= max_level].shape[0] + 1

    indexesi, indexesj = hofm_regions(region, lon2d, lat2d)

    # Fix for climatology
    # ESMValTool reduces the dimentions if one of the
    # dimentions is "empty"
    if datafile.variables[cmor_var].ndim < 4:
        series_lenght = 1
    else:
        series_lenght = datafile.variables[cmor_var].shape[0]

    oce_hofm = np.zeros((lev[0:lev_limit].shape[0], series_lenght))
    for mon in range(series_lenght):
        for ind, depth in enumerate(lev[0:lev_limit]):
            # fix for climatology
            if datafile.variables[cmor_var].ndim < 4:
                level_pp = datafile.variables[cmor_var][ind, :, :]
            else:
                level_pp = datafile.variables[cmor_var][mon, ind, :, :]

            ## This is fix fo make models with 0 as missing values work,
            ## should be fixed in fixes.
            if not isinstance(level_pp, np.ma.MaskedArray):
                level_pp = np.ma.masked_equal(level_pp, 0)
            data_mask = level_pp[indexesi, indexesj].mask
            area_masked = np.ma.masked_where(data_mask,
                                             areacello[indexesi, indexesj])
            result = (area_masked *
                      level_pp[indexesi, indexesj]).sum() / area_masked.sum()
            oce_hofm[ind, mon] = result

    ofilename = genfilename(diagworkdir, cmor_var, mmodel, region, 'hofm')
    ofilename_levels = genfilename(diagworkdir, cmor_var, mmodel, region,
                                   'levels')
    ofilename_time = genfilename(diagworkdir, cmor_var, mmodel, region, 'time')
    # print(ofilename)
    np.save(ofilename, oce_hofm)
    if isinstance(lev, np.ma.core.MaskedArray):
        np.save(ofilename_levels, lev[0:lev_limit].filled())
    else:
        np.save(ofilename_levels, lev[0:lev_limit])

    np.save(ofilename_time, time)
    datafile.close()


def transect_data(mmodel,
                  cmor_var,
                  region,
                  diagworkdir,
                  mult=2,
                  observations='PHC'):
    ''' Extract data for transects (defined in regions.transect_points)
    and save data to files.

    Parameters
    ----------
    mmodel: str
        model name that will be processed.
    cmor_var: str
        name of the CMOR variable
    region: str
        name of the region predefined in `transect_points` function.
    diagworkdir: str
        path to work directory.
    mult: integer
        multiplicator for the number of points in the transect.
        Can be used to increase transect resolution.
    observations: str
        name of the observation dataset.
    '''
    logger.info("Extract  {} data for {}, region {}".format(
        cmor_var, mmodel, region))
    # get the path to preprocessed file
    ifilename = genfilename(diagworkdir,
                            cmor_var,
                            mmodel,
                            data_type='timmean',
                            extension='.nc')
    # open with netCDF4
    datafile = Dataset(ifilename)
    # open with ESMF
    grid = ESMF.Grid(filename=ifilename, filetype=ESMF.FileFormat.GRIDSPEC)

    # get depth of the levels
    lev = datafile.variables['lev'][:]

    # indexesi, indexesj = hofm_regions(region, lon2d, lat2d)
    lon_s4new, lat_s4new = transect_points(region, mult=mult)

    # get instance of the coordinate system
    coord_sys = ESMF.CoordSys.SPH_DEG

    # masking true
    domask = True

    # create instans of the location stream (set of points)
    locstream = ESMF.LocStream(lon_s4new.shape[0],
                               name="Atlantic Inflow Section",
                               coord_sys=coord_sys)

    # appoint the section locations
    locstream["ESMF:Lon"] = lon_s4new
    locstream["ESMF:Lat"] = lat_s4new
    if domask:
        locstream["ESMF:Mask"] = np.array(np.ones(lon_s4new.shape[0]),
                                          dtype=np.int32)
    # initialise array for the section
    secfield = np.zeros(
        (lon_s4new.shape[0], datafile.variables[cmor_var].shape[1]))
    # get number of depth levels for the model
    ndepths = datafile.variables[cmor_var].shape[1]
    print("MODEL {}, ndepths {}".format(mmodel, ndepths))

    # loop over depth levels
    for kind in range(0, ndepths):
        # define field we interpolate FROM
        sourcefield = ESMF.Field(
            grid,
            staggerloc=ESMF.StaggerLoc.CENTER,
            name='MPI',
        )
        # load model data
        model_data = datafile.variables[cmor_var][0, kind, :, :]

        # ESMF do not understand masked arrays, so fill them
        if isinstance(model_data, np.ma.core.MaskedArray):
            sourcefield.data[...] = model_data.filled(0).T
        else:
            sourcefield.data[...] = model_data.T

        # create a field we giong to intorpolate TO
        dstfield = ESMF.Field(locstream, name='dstfield')
        dstfield.data[:] = 0.0

        # create an object to regrid data
        # from the source to the destination field
        dst_mask_values = None
        if domask:
            dst_mask_values = np.array([0])

        regrid = ESMF.Regrid(
            sourcefield,
            dstfield,
            regrid_method=ESMF.RegridMethod.NEAREST_STOD,
            #regrid_method=ESMF.RegridMethod.BILINEAR,
            unmapped_action=ESMF.UnmappedAction.IGNORE,
            dst_mask_values=dst_mask_values)

        # do the regridding from source to destination field
        dstfield = regrid(sourcefield, dstfield)
        secfield[:, kind] = dstfield.data

    # Calculate distance between points in km
    g = pyproj.Geod(ellps='WGS84')
    (az12, az21, dist) = g.inv(lon_s4new[0:-1], lat_s4new[0:-1], lon_s4new[1:],
                               lat_s4new[1:])
    dist = dist.cumsum() / 1000
    dist = np.insert(dist, 0, 0)

    # save the data
    ofilename = genfilename(diagworkdir, cmor_var, mmodel, region, 'transect')
    ofilename_depth = genfilename(diagworkdir, 'depth', mmodel, region,
                                  'transect')
    ofilename_dist = genfilename(diagworkdir, 'distance', mmodel, region,
                                 'transect')

    np.save(ofilename, secfield)
    # we have to fill masked arrays before saving
    if isinstance(lev, np.ma.core.MaskedArray):
        np.save(ofilename_depth, lev.filled())
    else:
        np.save(ofilename_depth, lev)
    np.save(ofilename_dist, dist)

    datafile.close()


def tsplot_data(mmodel, max_level, region, diagworkdir, observations='PHC'):
    '''Extract data for TS plots from one specific model

    Parameters
    ----------

    mmodel: str
        model name
    max_level: int
        maximum level (depth) of TS data to be used
    region: str
        region as defined in `hofm_regions`
    diagworkdir: str
        working directory
    observations: str
        name of the observations

    Returns
    -------
    None
    '''
    logger.info("Extract  TS data for {}, region {}".format(mmodel, region))

    # generate input names for T and S. The files are generated by the
    # `timmean` function.
    ifilename_t = genfilename(diagworkdir,
                              'thetao',
                              mmodel,
                              data_type='timmean',
                              extension='.nc')
    ifilename_s = genfilename(diagworkdir,
                              'so',
                              mmodel,
                              data_type='timmean',
                              extension='.nc')
    # get the metadata for T and S
    metadata_t = load_meta(datapath=ifilename_t, fxpath=None)
    datafile_t, lon2d, lat2d, lev, time, areacello = metadata_t

    metadata_s = load_meta(datapath=ifilename_s, fxpath=None)
    datafile_s, lon2d, lat2d, lev, time, areacello = metadata_s

    datafile_t = Dataset(ifilename_t)
    datafile_s = Dataset(ifilename_s)

    # find index of the max_level
    lev_limit = lev[lev <= max_level].shape[0] + 1
    # find indexes of data that are in the region
    indexesi, indexesj = hofm_regions(region, lon2d, lat2d)

    temp = np.array([])
    salt = np.array([])
    depth_model = np.array([])
    # loop over depths
    for ind, depth in enumerate(lev[0:lev_limit]):
        if mmodel != observations:
            level_pp = datafile_t.variables['thetao'][0, ind, :, :]
            level_pp_s = datafile_s.variables['so'][0, ind, :, :]
        else:
            level_pp = datafile_t.variables['thetao'][0, ind, :, :]
            level_pp_s = datafile_s.variables['so'][0, ind, :, :]
        ## This is fix fo make models with 0 as missing values work,
        ## should be fixed in fixes that do not work for now in the new backend
        if not isinstance(level_pp, np.ma.MaskedArray):
            level_pp = np.ma.masked_equal(level_pp, 0)
            level_pp_s = np.ma.masked_equal(level_pp_s, 0)
        # select individual points for T, S and depth
        temp = np.hstack((temp, level_pp[indexesi, indexesj].compressed()))
        salt = np.hstack((salt, level_pp_s[indexesi, indexesj].compressed()))
        depth_temp = np.zeros_like(level_pp[indexesi, indexesj].compressed())
        depth_temp[:] = depth
        depth_model = np.hstack((depth_model, depth_temp))

    # Saves the data to individual files
    ofilename_t = genfilename(diagworkdir, 'thetao', mmodel, region, 'tsplot')
    ofilename_s = genfilename(diagworkdir, 'so', mmodel, region, 'tsplot')
    ofilename_depth = genfilename(diagworkdir, 'depth', mmodel, region,
                                  'tsplot')
    np.save(ofilename_t, temp)
    np.save(ofilename_s, salt)
    np.save(ofilename_depth, depth_model)

    datafile_t.close()
    datafile_s.close()


def aw_core(model_filenames, diagworkdir, region, cmor_var):
    ''' Calculates Atlantic Water (AW) core depth the region.

    The AW core is defined as water temperature maximum
    between 200 and 1000 meters. Can be in future generalised
    to find the depth of specific water masses.

    The function relies on the data for the profiles, so
    this information should be available.

    Parameters
    ----------
    model_filenames: OrderedDict
        OrderedDict with model names as keys and input files as values.
    diagworkdir: str
        path to work directory.
    region: str
        one of the regions from `hofm_regions`,
        the data from the mean vertical profiles should be available.
    cmor_var: str
        name of the variable.

    Returns
    -------
    aw_core_parameters: dict
        For each model there is maximum temperature, depth level in the model,
        index of the depth level in the model.
    '''
    logger.info("Calculate AW core statistics")
    aw_core_parameters = {}

    for i, mmodel in enumerate(model_filenames):
        aw_core_parameters[mmodel] = {}
        logger.info("Plot profile {} data for {}, region {}".format(
            cmor_var, mmodel, region))
        ifilename = genfilename(diagworkdir, cmor_var, mmodel, region, 'hofm',
                                '.npy')
        ifilename_levels = genfilename(diagworkdir, cmor_var, mmodel, region,
                                       'levels', '.npy')

        hofdata = np.load(ifilename, allow_pickle=True)
        lev = np.load(ifilename_levels, allow_pickle=True)

        profile = (hofdata)[:, :].mean(axis=1)
        maxvalue = np.max(profile[(lev >= 200) & (lev <= 1000)])
        maxvalue_index = np.where(profile == maxvalue)[0][0]
        maxvalue_depth = lev[maxvalue_index]

        aw_core_parameters[mmodel]['maxvalue'] = maxvalue
        aw_core_parameters[mmodel]['maxvalue_index'] = maxvalue_index
        aw_core_parameters[mmodel]['maxvalue_depth'] = maxvalue_depth

    return aw_core_parameters