from direct.directnotify.DirectNotifyGlobal import directNotify
from toontown.uberdog import DataStoreGlobals
from direct.showbase.DirectObject import DirectObject
import pickle

class DataStoreAIClient(DirectObject):
    """
    This class should be instantiated by any class that needs to
    access an Uberdog data store.

    The client, as it is now, has the ability to create and destroy
    DataStores on the Uberdog.  This is mainly provided for backwards
    compatibility with the Toontown architecture where the logic has
    already been written for the AI side of things.

    For example, the HolidayManagerAI is something that could feasably
    be run on the Uberdog, however it's already well established on
    the AI.  For this reason, we'll allow the HolidayManagerAI to
    create and destroy data stores as it needs to.

    All it takes is one request to the Uberdog to carry out one of
    these operations.  Any further requests for data to an already
    destroyed store will go unanswered.

    In the future, we should make attempts to keep the create/destroy
    control on the Uberdog.  That way, we have only one point of control
    rather than several various AIs who may not be entirely in sync.
    """
    
    notify = directNotify.newCategory('DataStoreAIClient')
    wantDsm = simbase.config.GetBool('want-ddsm', 1)
        
    def __init__(self,air,storeId,resultsCallback):
        """
        storeId is a unique identifier to the type of store
        the client wishes to connect to.  There will only be
        one store of this type on the Uberdog at any given time.

        resultsCallback is a function that accepts one argument,
        the results returned from a query.  The format of this
        result argument is defined in the store's class definition.
        """

        if self.wantDsm:
            self.__storeMgr = air.dataStoreManager
        self.__storeId = storeId
        self.__resultsCallback = resultsCallback
        self.__storeClass = DataStoreGlobals.getStoreClass(storeId)
        self.__queryTypesDict = self.__storeClass.QueryTypes
        self.__queryStringDict = dict(list(zip(list(self.__queryTypesDict.values()),
                                          list(self.__queryTypesDict.keys()))))
        self.__enabled = False

    def openStore(self):
        """
        Attempt to connect to the store defined by the storeId in the
        __init__() function.  If no store of this type is present on
        the Uberdog, the store is created at this time.  Queries can now
        be sent to the store and replies from the store will be processed
        by the client.
        """
        if self.wantDsm:
            self.__storeMgr.startStore(self.__storeId)
            self.__startClient()

    def closeStore(self):
        """
        This client will no longer receive results from the store.  Also,
        the store, if present on the Uberdog, will now be shutdown and all
        data destroyed.  Do not use this method unless you are sure that
        the data is no longer needed by this, or any other, client.
        """
        if self.wantDsm:
            self.__stopClient()
            self.__storeMgr.stopStore(self.__storeId)

    def isOpen(self):
        return self.__enabled
    
    def getQueryTypes(self):
        return list(self.__queryTypesDict.keys())

    def getQueryTypeString(self,qId):
        return self.__queryStringDict.get(qId,None)
    
    def sendQuery(self,queryTypeString,queryData):
        """
        Sends a query to the data store.  The format of the query is
        defined in the store's class definition.
        """
        if self.__enabled:
            qId = self.__queryTypesDict.get(queryTypeString,None)
            if qId is not None:
                query = (qId,queryData)
                # pack the data to be sent to the Uberdog store.
                pQuery = pickle.dumps(query)
                self.__storeMgr.queryStore(self.__storeId,pQuery)
            else:
                self.notify.debug('Tried to send invalid query type: \'%s\'' % (queryTypeString,))
        else:
            self.notify.warning('Client currently stopped.  \'%s\' query will fail.' % (queryTypeString,))
        
    def receiveResults(self,data):
        """
        Upon receiving a query, the store will respond with a result.
        This function will call the resultsCallback function with the
        result data as its sole argument.  Try to treat the
        resultsCallback function as an event that is fired whenever
        the client receives data from the store.
        """
        # unpack the results from the Uberdog store.

        if data == 'Store not found':
            self.notify.debug('%s not present on uberdog. Query dropped.' %(self.__storeClass.__name__,))
        else:
            results = pickle.loads(data)
            self.__resultsCallback(results)

    def __startClient(self):
        """
        Allow the client to send queries and receive results from its
        associated data store.
        """
        self.accept('TDS-results-%d'%self.__storeId,self.receiveResults)
        self.__enabled = True
        
    def __stopClient(self):
        """
        Disallow the client from sending queries and receiving results
        from its associated data store.
        """
        self.ignoreAll()
        self.__enabled = False

    def deleteBackupStores(self):
        """
        Delete any backed up stores from previous year's
        """
        if self.wantDsm:
            self.__storeMgr.deleteBackupStores()
