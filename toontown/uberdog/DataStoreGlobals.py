from toontown.uberdog.DataStore import *
from toontown.uberdog.ScavengerHuntDataStore import *

SH = 1
GEN = 2
TYPES = {SH: (ScavengerHuntDataStore,),
 GEN: (DataStore,)}

def getStoreClass(type):
    storeClass = TYPES.get(type, None)
    if storeClass:
        return storeClass[0]
    return
