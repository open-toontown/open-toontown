from toontown.estate import DistributedStatuaryAI

class DistributedChangingStatuaryAI(DistributedStatuaryAI.DistributedStatuaryAI):
    """
    Regular statues and toon statues don't change once planted.
    This class does, initially created for the melting snowman
    """
    notify = directNotify.newCategory("DistributedChangingStatuaryAI")

    def __init__(self, typeIndex = 201, waterLevel = 0, growthLevel = 0, optional = None, ownerIndex = 0, plot = 0):
        DistributedStatuaryAI.DistributedStatuaryAI.__init__(self, typeIndex,
                                                             waterLevel, growthLevel,
                                                             optional, ownerIndex, plot)
    def doEpoch(self, numEpochs):
        """Make the changing statue 'grow'."""
        growthLevel = 0
        waterLevel = 0
        for i in range(numEpochs):
            growthLevel = self.getGrowthLevel()
            # since we can't water the statue, always make it grow
            self.notify.debug( "growing changing statue")
            # grow the plant
            growthLevel += 1
            self.b_setGrowthLevel(growthLevel, False)
        return (growthLevel, waterLevel)

    def getGrowthLevel(self):
        return self.growthLevel

    def setGrowthLevel(self, growthLevel, finalize):
        self.growthLevel = growthLevel
        self.updateEstate(growthLevel=growthLevel, finalize=finalize)
        
    def d_setGrowthLevel(self,growthLevel):
        self.sendUpdate('setGrowthLevel' , [growthLevel])
        
    def b_setGrowthLevel(self,growthLevel, finalize=True):
        if growthLevel > 127:
            growthLevel = 127 #range clamping
        self.setGrowthLevel(growthLevel, finalize)
        self.d_setGrowthLevel(growthLevel)
        
    def updateEstate(self, waterLevel=None, growthLevel=-1, variety=-1, finalize=True):
        if self.estateId:
            estate = simbase.air.doId2do.get(self.estateId)
            if estate:
                if finalize:
                    func = estate.b_setOneItem
                else:
                    func = estate.setOneItem

                func(self.ownerIndex, self.plot,
                     waterLevel=waterLevel,
                     growthLevel=growthLevel,
                     variety=variety)
