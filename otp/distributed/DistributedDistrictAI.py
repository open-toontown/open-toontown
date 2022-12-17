

from direct.distributed.DistributedObjectAI import DistributedObjectAI
from direct.directnotify.DirectNotifyGlobal import directNotify

from direct.task import Task

class DistributedDistrictAI(DistributedObjectAI):
    notify = directNotify.newCategory("DistributedDistrictAI")
    
    def __init__(self, air, name="untitled"):
        DistributedObjectAI.__init__(self, air)
        self.air = air
        self.name=name
        self.available = 0
        
    def delete(self):
        self.ignoreAll()
        self.b_setAvailable(0)
        DistributedObjectAI.delete(self)        
    
    def getAvailable(self):
        return self.available
    
    def getName(self):
        return self.name
    
    # available value
    def setAvailable(self, available):
        self.available=available
    
    def d_setAvailable(self, available):
        self.sendUpdate("setAvailable", [available])

    def b_setAvailable(self, available):
         self.setAvailable(available)
         self.d_setAvailable(available)
      
    # set name      
    def setName(self, name):
        self.name=name
               
    def d_setName(self, name):
        self.sendUpdate("setName", [name])

    def b_setName(self, name):
        self.setName(name)
        self.d_setName(name)
        
