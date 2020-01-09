from . import CatalogItem
from pandac.PandaModules import *
from direct.distributed.PyDatagram import PyDatagram
from direct.distributed.PyDatagramIterator import PyDatagramIterator

class CatalogItemList:

    def __init__(self, source = None, store = 0):
        self.store = store
        self.__blob = None
        self.__list = None
        if isinstance(source, str):
            self.__blob = source
        elif isinstance(source, list):
            self.__list = source[:]
        elif isinstance(source, CatalogItemList):
            if source.store == store:
                if source.__list != None:
                    self.__list = source.__list[:]
                self.__blob = source.__blob
            else:
                self.__list = source[:]
        return

    def markDirty(self):
        if self.__list:
            self.__blob = None
        return

    def getBlob(self, store = None):
        if store == None or store == self.store:
            if self.__blob == None:
                self.__encodeList()
            return self.__blob
        return self.__makeBlob(store)

    def getNextDeliveryDate(self):
        if len(self) == 0:
            return
        nextDeliveryDate = None
        for item in self:
            if item:
                if nextDeliveryDate == None or item.deliveryDate < nextDeliveryDate:
                    nextDeliveryDate = item.deliveryDate

        return nextDeliveryDate

    def getNextDeliveryItem(self):
        if len(self) == 0:
            return
        nextDeliveryDate = None
        nextDeliveryItem = None
        for item in self:
            if item:
                if nextDeliveryDate == None or item.deliveryDate < nextDeliveryDate:
                    nextDeliveryDate = item.deliveryDate
                    nextDeliveryItem = item

        return nextDeliveryItem

    def extractDeliveryItems(self, cutoffTime):
        beforeTime = []
        afterTime = []
        for item in self:
            if item.deliveryDate <= cutoffTime:
                beforeTime.append(item)
            else:
                afterTime.append(item)

        return (CatalogItemList(beforeTime, store=self.store), CatalogItemList(afterTime, store=self.store))

    def extractOldestItems(self, count):
        return (self[0:count], self[count:])

    def __encodeList(self):
        self.__blob = self.__makeBlob(self.store)

    def __makeBlob(self, store):
        dg = PyDatagram()
        if self.__list:
            dg.addUint8(CatalogItem.CatalogItemVersion)
            for item in self.__list:
                CatalogItem.encodeCatalogItem(dg, item, store)

        return dg.getMessage()

    def __decodeList(self):
        self.__list = self.__makeList(self.store)

    def __makeList(self, store):
        list = []
        if self.__blob:
            dg = PyDatagram(self.__blob)
            di = PyDatagramIterator(dg)
            versionNumber = di.getUint8()
            while di.getRemainingSize() > 0:
                item = CatalogItem.decodeCatalogItem(di, versionNumber, store)
                list.append(item)

        return list

    def append(self, item):
        if self.__list == None:
            self.__decodeList()
        self.__list.append(item)
        self.__blob = None
        return

    def extend(self, items):
        self += items

    def count(self, item):
        if self.__list == None:
            self.__decodeList()
        return self.__list.count(item)

    def index(self, item):
        if self.__list == None:
            self.__decodeList()
        return self.__list.index(item)

    def insert(self, index, item):
        if self.__list == None:
            self.__decodeList()
        self.__list.insert(index, item)
        self.__blob = None
        return

    def pop(self, index = None):
        if self.__list == None:
            self.__decodeList()
        self.__blob = None
        if index == None:
            return self.__list.pop()
        else:
            return self.__list.pop(index)
        return

    def remove(self, item):
        if self.__list == None:
            self.__decodeList()
        self.__list.remove(item)
        self.__blob = None
        return

    def reverse(self):
        if self.__list == None:
            self.__decodeList()
        self.__list.reverse()
        self.__blob = None
        return

    def sort(self, cmpfunc = None):
        if self.__list == None:
            self.__decodeList()
        if cmpfunc == None:
            self.__list.sort()
        else:
            self.__list.sort(cmpfunc)
        self.__blob = None
        return

    def __len__(self):
        if self.__list == None:
            self.__decodeList()
        return len(self.__list)

    def __getitem__(self, index):
        if self.__list == None:
            self.__decodeList()
        return self.__list[index]

    def __setitem__(self, index, item):
        if self.__list == None:
            self.__decodeList()
        self.__list[index] = item
        self.__blob = None
        return

    def __delitem__(self, index):
        if self.__list == None:
            self.__decodeList()
        del self.__list[index]
        self.__blob = None
        return

    def __getslice__(self, i, j):
        if self.__list == None:
            self.__decodeList()
        return CatalogItemList(self.__list[i:j], store=self.store)

    def __setslice__(self, i, j, s):
        if self.__list == None:
            self.__decodeList()
        if isinstance(s, CatalogItemList):
            self.__list[i:j] = s.__list
        else:
            self.__list[i:j] = s
        self.__blob = None
        return

    def __delslice__(self, i, j):
        if self.__list == None:
            self.__decodeList()
        del self.__list[i:j]
        self.__blob = None
        return

    def __iadd__(self, other):
        if self.__list == None:
            self.__decodeList()
        self.__list += list(other)
        self.__blob = None
        return self

    def __add__(self, other):
        copy = CatalogItemList(self, store=self.store)
        copy += other
        return copy

    def __repr__(self):
        return self.output()

    def __str__(self):
        return self.output()

    def output(self, store = -1):
        if self.__list == None:
            self.__decodeList()
        inner = ''
        for item in self.__list:
            inner += ', %s' % item.output(store)

        return 'CatalogItemList([%s])' % inner[2:]
