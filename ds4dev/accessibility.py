###########
#    Heidi Hurst 2019 DS4Dev Coursework
#
#    package accessibility.py
###########

import numpy as np

# TODO: what to do about zero entries in our cost matrix 
# (IE what about the diagonal? EXCLUDE or SET CIJ TO ONE)
def exclude(lst, i):
    if i == 0:
        return lst[i+1:]

    return np.concatenate((lst[:i],lst[i+1:]))

def access1(T,c):
    """
    Creates an access index of type 1 based on inputs:
        T (flow from i to j, square matrix)
        c (cost of travel from i to j, square matrix)
        
    See Piovani et al (2018) eqn 3.10
    """
    outsize = c.shape[0]
    # initialize output to nans
    A = [np.nan] * outsize
    # iterate
    for i in range(outsize):
        A[i] = sum(exclude(T[i,:],i)*(1/exclude(c[i,:],i)))/sum(exclude(T[i,:],i))
    
    return A
    
    
def access2(E,c):
    """
    Creates an accessibility index of type 2 based on inputs:
        E (opportunities/employment at each location, vector)
        c (cost of travel from i to j, square matrix)
        
    See Piovani et al (2018) eqn 3.11
    """
    outsize = c.shape[0]
    # initialize output to nans
    A = [np.nan] * outsize
    # iterate
    for i in range(outsize):
        A[i] = sum(exclude(E,i)/exclude(c[i,:],i))/outsize
        
    return A