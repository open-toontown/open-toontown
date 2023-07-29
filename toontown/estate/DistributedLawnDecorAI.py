from otp.ai.AIBase import *
from direct.interval.IntervalGlobal import *
from direct.directnotify import DirectNotifyGlobal
from direct.distributed import ClockDelta
from direct.task import Task
from direct.directnotify import DirectNotifyGlobal
from direct.distributed import DistributedObjectAI
from direct.distributed import DistributedNodeAI
from toontown.estate import GardenGlobals

class DistributedLawnDecorAI(DistributedNodeAI.DistributedNodeAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedLawnDecorAi')    
                                
    def __init__(self, air, ownerIndex = 0, plot = 0):
        DistributedNodeAI.DistributedNodeAI.__init__(self, air)
        self.ownerIndex = ownerIndex
        self.plot = plot
        self.occupied = True
        self.estateId = 0
        self.occupantId = None
        self.lastMovie = None
        
        #self.node = hidden.attachNewNode('DistributedPlantAI')

        #only one toon can be interacting with it
        self.interactingToonId = 0
        
    def generate(self):
        DistributedNodeAI.DistributedNodeAI.generate(self)

    def delete(self):
        #del self.pos
        #taskMgr.remove(self.detectName)
        self.ignoreAll()
        DistributedNodeAI.DistributedNodeAI.delete(self)

    def destroy(self):
        self.notify.info('destroy entity(elevatorMaker) %s' % self.entId)
        DistributedNodeAI.DistributedNodeAI.destroy(self)
        
    def setPos(self, x,y,z):
        DistributedNodeAI.DistributedNodeAI.setPos(self, x ,y ,z )
        #self.sendUpdate("setPos", [x,y,z])
        
    def setPlot(self, plot):
        self.plot = plot
        
    def getPlot(self):
        return self.plot
        
    def setOwnerIndex(self, index):
        self.ownerIndex = index
        
    def getOwnerIndex(self):
        return self.ownerIndex
        
    def setEstateId(self, estateId):
        self.estateId = estateId
        
    def plotEntered(self, optional = None):
        self.occupantId = self.air.getAvatarIdFromSender()
        #print("entered %s" % (senderId))
        #this is called when the plot has been entered
        
    def setH(self, h):
        DistributedNodeAI.DistributedNodeAI.setH(self, h)
        #self.sendUpdate('setH', [h])
        
    def getHeading(self):
        return DistributedNodeAI.DistributedNodeAI.getH(self)
        
    def d_setH(self, h):
        #print("Sending Distributed H")
        self.sendUpdate('setHeading', [h])
        
    def b_setH(self, h):
        self.setH(h)
        self.d_setH(h)
        
    def getPosition(self):
        position = self.getPos()
        return position[0], position[1], position[2]
        
    def d_setPosition(self, x, y, z):
        self.sendUpdate('setPosition', [x,y,z])
        
    def b_setPosition(self, x, y, z):
        self.setPosition(x,y,z)
        self.d_setPosition(x,y,z)
        
        
    def setPosition(self, x, y, z):
        self.setPos(x,y,z)
        
    def removeItem(self):
        senderId = self.air.getAvatarIdFromSender()
        
        zoneId = self.zoneId
        estateOwnerDoId = simbase.air.estateMgr.zone2owner.get(zoneId)

        if not senderId == estateOwnerDoId:
            self.notify.warning("how did this happen, picking a flower you don't own")
            return

        if not self.requestInteractingToon(senderId):
            self.sendInteractionDenied(senderId)
            return        
        
        if estateOwnerDoId:
            estate = simbase.air.estateMgr.estate.get(estateOwnerDoId)
            if estate:
                #we should have a valid DistributedEstateAI at this point
                self.setMovie(GardenGlobals.MOVIE_REMOVE, senderId)
                
    def doEpoch(self, numEpochs):
        return (0, 0)

    def hasFruit(self):
        return False

    def hasGagBonus(self):
        return False    

    def setMovie(self, mode, avId, extraArgs = None):
        self.lastMovie = mode
        self.lastMovieAvId = avId
        self.lastMovieArgs = extraArgs
        self.sendUpdate("setMovie", [mode, avId])

        if (mode == GardenGlobals.MOVIE_CLEAR):
            self.clearInteractingToon()

    def movieDone(self):
        self.clearInteractingToon()
        self.notify.debug('---- got movieDone, self.lastMovie=%d lastMovieAvId=%d---')
        if self.lastMovie == GardenGlobals.MOVIE_REMOVE:
            self.lastMovie = None
            zoneId = self.zoneId
            avId = self.lastMovieAvId
            estateOwnerDoId = simbase.air.estateMgr.zone2owner.get(zoneId)
            estate = simbase.air.estateMgr.estate.get(estateOwnerDoId)
            if estate:
                itemId = estate.removePlantAndPlaceGardenPlot(self.ownerIndex, self.plot)

                # tell the gardenplot to tell the toon to finish 'removing'
                item = simbase.air.doId2do.get(itemId)
                item.setMovie(GardenGlobals.MOVIE_FINISHREMOVING, avId)
        elif self.lastMovie == GardenGlobals.MOVIE_FINISHPLANTING or\
             self.lastMovie == GardenGlobals.MOVIE_HARVEST:
            self.lastMovie = None
            zoneId = self.zoneId
            avId = self.lastMovieAvId
            estateOwnerDoId = simbase.air.estateMgr.zone2owner.get(zoneId)
            estate = simbase.air.estateMgr.estate.get(estateOwnerDoId)
            if estate:
                itemId = self.doId
                # tell the gardenplot to tell the toon to clear the movie, so the
                # results dialog doesn't come up again when he exits from his house
                item = simbase.air.doId2do.get(itemId)
                item.setMovie(GardenGlobals.MOVIE_CLEAR, avId)
                

    def requestInteractingToon(self, toonId):
        """
        if no one else is interacting with this plant, return true
        and note which toon is now interacting with it
        """
        #debug only, will cause all actions to be denied
        if simbase.config.GetBool('garden-approve-all-actions', 0):
            return True

        #debug only, will cause all actions to be denied
        if simbase.config.GetBool('garden-deny-all-actions', 0):
            return False
            
        retval = False
        if self.interactingToonId == 0:
            self.setInteractingToon(toonId)
            retval = True
            self.notify.debug('returning True in requestInteractingToon')
        else:
            self.notify.debug( 'denying interaction by %d since %s is using it' % (toonId, self.getInteractingToon()))
        
        return retval

    def clearInteractingToon(self):
        self.setInteractingToon(0)

    def setInteractingToon(self, toonId):
        """
        which toon is interacting with this plant
        """
        self.notify.debug('setting interactingToonId=%d' % toonId)
        self.interactingToonId = toonId

    def getInteractingToon(self):
        return self.interactingToonId

    def sendInteractionDenied(self, toonId):
        self.notify.debug('sending interaction denied to %d' % toonId)
        self.sendUpdate('interactionDenied', [toonId])
