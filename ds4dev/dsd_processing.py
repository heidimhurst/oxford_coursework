###########
#    Heidi Hurst 2019 DS4Dev Coursework
#
#    package dsd_processing.py
###########

import pandas as pd
import geopandas as gpd
import numpy as np

from shapely.ops import nearest_points
from shapely.geometry import MultiPoint, Point, Polygon

from cost_model import projected


def spatial_csv(name, path="", project = True, **kwargs):
    """
    Quick function to read in CSV containing columns "longitude" and 
    "latitude" and convert to geopandas dataframe.
    """
    stations = pd.read_csv(path+name, encoding="ISO-8859-1")
    if all(x in stations.columns for x in ["longitude", "latitude"]):
        stations['geometry'] = stations.apply(lambda z: Point(z.longitude, z.latitude), axis=1)
    stations = gpd.GeoDataFrame(stations)

    if project:
        return projected(stations, **kwargs)

    return stations


def plot_adj(axes, title=""):
    """
    Helper function to set axis, title, labels consistenly etc.
    """
    axes.set_title(title)
    axes.set_xticks(list(range(1,11)))
    axes.set_yticks(list(range(1,11)))
    axes.set_xlabel("Destination Municipio")
    axes.set_ylabel("Origin Municipio")


def scale_commute_to_employment(commutes_muni, employment):
    """
    Creates numpy array corresponding to flows scaled to meet employment constraints
    specified by "employment"
    """
    
    # get observed flows
    Tobs = observed_flow(commutes_muni)
    com_tot = Tobs.sum(axis=0) # total flow INTO each area (i.e. employment)
    
    # compute scale factors for each municipality
    com_sf = [0] * 10
    com_exp = np.array([list(employment[(employment["muni_index"]==i) & 
                                        (employment["year"]==2017)]['employment'])[0] 
                        for i in range(1,11)])
    com_sf = com_exp/com_tot

    # there has to be a matrix way of doing this
    for i in range(10):
        Tobs[:,i] = com_sf[i]*Tobs[:,i]
    
    return Tobs


def scale_commute_to_pop(commutes_muni, P, employment_rate=0.627):
    """
    Creates numpy array corresponding to flows scaled to meet employment constraints
    specified by "employment"
    """
    
    # get observed flows
    Tobs = observed_flow(commutes_muni)
    com_tot = Tobs.sum(axis=1) # total flow OUT OF each area
    
    # compute scale factors for each municipality
    com_sf = (employment_rate*P)/com_tot

    # there has to be a matrix way of doing this
    for i in range(10):
        Tobs[i,:] = com_sf[i]*Tobs[i,:]
    
    return Tobs


def plot_adj(axes, title=""):
    """
    Helper function to set axis, title, labels consistenly etc.
    """
    axes.set_title(title)
    axes.set_xticks(list(range(1,11)))
    axes.set_yticks(list(range(1,11)))
    axes.set_xlabel("Destination Municipio")
    axes.set_ylabel("Origin Municipio")