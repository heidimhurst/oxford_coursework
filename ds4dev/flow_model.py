###########
#    Heidi Hurst 2019 DS4Dev Coursework
#
#    package flow_model.py
###########

import numpy as np
from scipy.optimize import minimize

def gravity_single(c, E, P, beta):
    """
    Computes an accessibility matrix based on 
    c: cost matrix (where cij is cost from i to j)
    E: employment
    P: population
    beta: parameter
    """
    
    # initialize z, which must be solved for
    Z = [np.nan] * 10 # initialize to nan
    # compute zi
    for i in range(len(Z)):
        Z[i] = 1/(sum(E*np.exp(-1*beta*c[i,:])))
        
    # initialize tij
    Tsing = np.full((10,10),np.nan)
    
    # calculate tij 
    # nb i know there's a better way but this way i don't get confused
    for i in range(10):
        for j in range(10):
            Tsing[i,j] = Z[i]*P[i]*E[j]*np.exp(-1*beta*c[i,j])
            
    return Tsing


def radiation(c, E, P, **kwargs):
    """
    Apply radiation model to cost matrix cij to get estimated flows
    
    c: cost matrix (where cij is cost from i to j)
    E: employment
    P: population
    """
    
    n = len(c)
    
    # initialize empty matrix
    E_mat = np.full((n,n),0)
    
    # compute available opportunities by looking at what is reachable 
    # from a given starting point
    for i in range(n):
        for j in range(n):
            c1 = c[i,j] # comparison travel time of interest
            in_range = (c[i,:] <= c1) # filter indices within travel time 
            E_mat[i,j] = sum(E[in_range]) # add up population
            
    # initialize tij
    Trad = np.full((n,n),np.nan)
    
    # compute!
    for i in range(10):
        for j in range(10):
            Trad[i,j] = ((P[i]/(1-P[i]/P.sum()))*((E[i]*E[j])/
                        ((E[i] + E_mat[i,j])*(E[i]+E[j]+E_mat[i,j]))))
            
    return Trad


