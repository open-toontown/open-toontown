from otp.ai.AIBase import *
from direct.distributed.ClockDelta import *
from direct.distributed import DistributedObjectAI
from . import DistributedHouseAI
from direct.fsm import ClassicFSM
from direct.fsm import State
from direct.task import Task
import random
import pickle
from . import HouseGlobals

class DistributedGardenAI(DistributedObjectAI.DistributedObjectAI):

    """
    The distributed garden will do timed things like grow gags, weeds, etc.
    It will also house some interactive elements, such as a bird feeder, etc.
    """

    notify = directNotify.newCategory("DistributedGardenAI")

    def __init__(self, air, pos=(0,0,0), rad=0):
        DistributedObjectAI.DistributedObjectAI.__init__(self, air)

        self.pos = pos
        self.radius = rad
        self.props = []

    def delete(self):
        self.notify.debug("delete")
        self.__killSproutPropTask()
        DistributedObjectAI.DistributedObjectAI.delete(self)

    def start(self):
        self.notify.debug("start")
        #self.__spawnSproutPropTask()
        
    def __spawnSproutPropTask(self):
        taskMgr.remove(self.taskName("sprout-prop"))
        taskMgr.doMethodLater(15,
                              self.sproutProp,
                              self.taskName("sprout-prop"))
        
    def sproutProp(self, task):
        self.notify.debug("sproutProp")
        # get random position within garden
        x = self.pos[0] + self.radius * (2*random.random()-1)
        y = self.pos[1] + self.radius * (2*random.random()-1)
        z = self.pos[2] + 0

        #prop = random.choice(range(HouseGlobals.NUM_PROPS))
        prop = HouseGlobals.PROP_FLOWER
        
        self.sendUpdate("sendNewProp", [prop, x, y, z])

        self.__spawnSproutPropTask()
        return Task.done
        
    def __killSproutPropTask(self):
        taskMgr.remove(self.taskName("sprout-prop"))
        
    def getProps(self):
        self.notify.debug("getProps")
        return self.props

    
