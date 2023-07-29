from otp.ai.AIBaseGlobal import *
from direct.distributed import DistributedObjectAI
from direct.directnotify import DirectNotifyGlobal
from direct.fsm import ClassicFSM
from direct.distributed import ClockDelta
from direct.fsm import State
import random
from . import HouseGlobals

class DistributedHouseItemAI(DistributedObjectAI.DistributedObjectAI):

    """
    This is a base class for furniture, portraits, wallpaper, and all house
    items that you can store and manipulate in your house.
    """

    notify = DirectNotifyGlobal.directNotify.newCategory("DistributedHouseItemAI")

    def __init__(self, air):
        DistributedObjectAI.DistributedObjectAI.__init__(self, air)
