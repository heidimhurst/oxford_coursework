###########
#    Heidi Hurst 2019 DS4Dev Coursework
#
#    package cost_model.py
###########


# imports
import networkx as nx
from shapely.ops import nearest_points
from shapely.geometry import MultiPoint, Point, Polygon

import pandas as pd
import geopandas as gpd

import geoplot as gplt

import numpy as np


# estimated speed in minutes per meter
# transit_speed = {"Metro": 1, "Cable": 1, "Tramway":1, "Bus rapid transit": 1, "Walk":1/75} 
# # esimtated wait time in minutes
# transit_wait = {"Metro": 1, "Cable": 5, "Tramway":5, "Bus rapid transit": 10}

def non_unique(lst):
    """
    Returns non-unique items in a list
    """
    
    uniq = list(set(lst))
    # remove them all, leaving only transfer stops
    for i in range(len(uniq)):
        lst.remove(uniq[i])
        
    return lst

def projected(df, crs=32218):
    """
    Projects a dataframe df into epsg:21818 (UTM18N). 
    If no intial CRS specified, assume WGS 84
    """
    if df.crs is None:
        # if no coordinate reference selected, assume WGS84
        df.crs = {'init' :'epsg:4326'}
    df = df.to_crs(epsg=crs)
    
    return df

def projected_centroid(df, crs=32218):
    """
    Takes a dataframe with a polygon "geometry" field, finds the centroid of each 
    polygon, and then converts that into a projected coordinate for given CRS
    """
    
    new_geom = [df.loc[x,"geometry"].centroid for x in range(len(df))]
    df["geometry"] = new_geom

    return projected(df,crs)

def sort_df_by_list(df, lst, column_name="admin2RefN"):
    """
    Sorts a data frame to be in the same order as lst by column name
    Returns sorted data frame
    """
    
    df["sort_ind"] = [lst.index(df.loc[i,column_name]) for i in range(len(df))]
    
    return df.sort_values("sort_ind")

def muni_center(ind, comunas, **kwargs):
    """
    Finds the "center" of a municipality of index "ind" as 
    the centroid of all its composite comunas
    """
    return MultiPoint(comunas[comunas["muni_index"]==ind].geometry.tolist()).centroid


def metro_dist(from_pt, to_pts, **kwargs):
    """
    Finds distance from from_pt to nearest metro station or to_pts.
    
    from_pt : row of e.g. municipality with PROJECTED .geometry field
    to_pts (eg metro) : data frame of target points with PROJECTED .geometry field

    if additional key COMUNAS is included, distance will be taken from the centroid
    of comunas matching the correct municipality index.
    
    returns: distance (METERS, if both dataframes projected projected)
    and INDEX (second) of to_pt
    """
    
    # throw error if incorrect type, for whatever reason
    assert(type(from_pt.geometry) in [Point, Polygon]), "from_pt must contain point or polygon geometry"

    to_pts_geom = to_pts.geometry.tolist()
    # find nearest point to a given point
    if "comunas" in kwargs.keys(): # weighted center of comunas
        center = muni_center(from_pt["sort_ind"] + 1,  kwargs["comunas"])
        r = nearest_points(center, MultiPoint(to_pts_geom))
    elif type(from_pt.geometry) == Polygon:
        r = nearest_points(from_pt.geometry.centroid, MultiPoint(to_pts_geom))
    elif type(from_pt.geometry) == Point:
        r = nearest_points(from_pt.geometry, MultiPoint(to_pts_geom))

    return r[0].distance(r[1]), to_pts_geom.index(r[1])


def metro_time(i, j, metro, **kwargs):
    """
    Computes the time needed to travel between metro stop i and stop j
    i,j indices based on transit_speed specified by transit type
    """
    # change speed based on type of transit
    dist =  metro.loc[i,'geometry'].distance(metro.loc[j,'geometry'])

    if "speed" in kwargs.keys():
        speed = kwargs["speed"]
        return dist * speed[metro.loc[i,"Type"]]
    else:
        return dist

def create_transfer_nodes(G, metro, add=True, **kwargs):
    """
    For a metro system "metro" (dataframe), creates dummy nodes for transfer stations
    and adds them to graph of metro system G.
    
    Returns list of transfer node names
    """
    # get list of transfer stops
    t_names = non_unique(list(metro["Stop"].values))
    # create node dictionary
    t_nodes = dict.fromkeys(list(range(len(metro),len(metro)+len(t_names))))
    # populate node dict with content
    for i in range(len(t_names)):
        t_nodes[i+len(metro)] = t_names[i]
        
    if add:
        G.add_nodes_from(t_nodes)
        return G

    return t_nodes

def create_transfer_edges(G, metro, wait, add=True, **kwargs):
    """
    Creates tuples of (station, transfer, wait_time) and adds them to graph
    G of the metro station as edges.
    """
    edges = []
    # get list of transfer stops
    transfer_names = non_unique(list(metro["Stop"].values))
    # loop through dummy transfer stations
    for i in range(len(transfer_names)):
        to_indices = [k for k in range(len(metro)) if (metro.loc[k,"Stop"] == transfer_names[i]) ]
        # loop through things to that tation
        for j in to_indices:
            edges.append((j,i+len(metro),wait[metro.loc[j,"Type"]]))
            
    if add:
        G.add_weighted_edges_from(edges)
        return G
        
    return edges

def create_metro_edges(G, metro, add=True, **kwargs):
    """
    Generates weighted edges
    """
    edges = [(i,i+1,metro_time(i,i+1, metro, **kwargs)) for i in range(len(metro)-1) if metro.loc[i,"Line"] == metro.loc[i+1,"Line"]]
    
    if add:
        # add edges to graph
        G.add_weighted_edges_from(edges)
        return G
        
    return edges

def metro_to_graph(metro,**kwargs):
    """
    Creates a connected graph from metro dataframe, where metro contains (at least) columns
    "Line", "Stop", "Type"
    """
    # create empty graph
    G = nx.Graph()
    
    # add metro nodes
    mdict = metro.to_dict(orient="index")
    G.add_nodes_from(list(mdict.keys()))
    nx.set_node_attributes(G, mdict)
    # add metro edges
    G = create_metro_edges(G, metro,**kwargs)
    # add transit dummy stations
    G = create_transfer_nodes(G, metro, **kwargs)
    # add transit edges
    G = create_transfer_edges(G, metro, **kwargs)
    return G

def add_centroids(G, metro, municip, namecol="admin2RefN", add=True, walk_speed=1/84, **kwargs):
    """
    Adds centroids of municipality to graph as well as edges 
    between centroids and closest metro stops
    
    walk_speed: meters per minute
    """
    
    # distance from each centroid to a metro station
    mout = [metro_dist(municip.iloc[x], metro, **kwargs) for x in range(10)]
    
    # create new nodes,edges for each municipality
    offset = 1000
    # muni index list
    muni_index = list(range(offset, offset+len(municip)))
    muni_nodes = dict.fromkeys(muni_index)
    edges = []

    # set walk speed from speed, if an option
    if "speed" in kwargs.keys():
    	walk_speed = kwargs["speed"]["Walk"]
    
    # assign name attribute, index attribute, create edges
    for i in range(len(municip)):
        muni_nodes[offset + i] = {"muni_index":i, "muni_name" : municip.loc[i,namecol]}
        edges.append((offset+i, mout[i][1], mout[i][0]*walk_speed))    
        
    # add to graph
    if add:
        # add nodes
        G.add_nodes_from(list(muni_nodes.keys()))
        nx.set_node_attributes(G, muni_nodes)
        # add edges
        G.add_weighted_edges_from(edges)
        return G, muni_index
    
    return muni_nodes, edges


def cost_between_indices(G, lst, method="dijkstra"):
    """
    Creates a matrix of size len(lst)^2 where entry
    c_ij contains the cost of traveling from node i to
    node j through graph G
    """
    
    n = len(lst)
    cost = np.zeros((n,n))
    for i in range(n):
        for j in range(n):
            cost[i,j] = max(nx.dijkstra_path_length(G,lst[i],lst[j]),1)
    
    return cost

def cost_from_metro(metro, municip, **kwargs):
    """
    Creates a cost matrix for traveling between the centroids 
    of all municipalities
    """
    
    # create graph
    G = metro_to_graph(metro, **kwargs)
    # add centroids
    G, muni_index = add_centroids(G, metro, municip, **kwargs)
    
    return cost_between_indices(G, muni_index)
