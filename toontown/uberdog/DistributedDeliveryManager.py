from pandac.PandaModules import *
from direct.distributed.DistributedObject import DistributedObject
from toontown.catalog import CatalogItemList
from toontown.catalog import CatalogItem

class DistributedDeliveryManager(DistributedObject):
    neverDisable = 1

    def sendHello(self, message):
        self.sendUpdate('hello', [message])

    def rejectHello(self, message):
        print 'rejected', message

    def helloResponse(self, message):
        print 'accepted', message

    def sendAck(self):
        self.sendUpdate('requestAck', [])

    def returnAck(self):
        messenger.send('DeliveryManagerAck')

    def test(self):
        print 'Distributed Delviery Manager Stub Test'
