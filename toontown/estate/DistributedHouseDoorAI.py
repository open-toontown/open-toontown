""" DistributedHouseDoorAI module:  a child of the DistributedDoorAI class """


from otp.ai.AIBaseGlobal import *
from direct.distributed.ClockDelta import *

from direct.directnotify import DirectNotifyGlobal
from direct.fsm import ClassicFSM
from toontown.building import DistributedDoorAI
from direct.fsm import State


class DistributedHouseDoorAI(DistributedDoorAI.DistributedDoorAI):
    """
    DistributedHouseDoorAI class:
    Works slightly different that a normal DistributedDoor, in that
    the House's doId is passed in, so we don't have to try and figure
    out which building this door belongs to.  We know it.
    """

    if __debug__:
        notify = DirectNotifyGlobal.directNotify.newCategory('DistributedHouseDoorAI')

    def __init__(self, air, houseDoId, doorType, doorIndex=0,
                 lockValue=0, swing=3):
        """
        blockNumber: Usually the landmark building number (from the name)
        in the case of house doors, we will use it to refer to the house id
        doorIndex: Each door must have a unique index
        """
        DistributedDoorAI.DistributedDoorAI.__init__(self, air, houseDoId, doorType,
                                                     doorIndex, lockValue, swing)
        assert(self.notify.debug(str(houseDoId)+" DistributedHouseDoorAI("
                "%s, %s)" % ("the air", str(houseDoId))))
        self.houseId = houseDoId
        self.block = houseDoId

    if __debug__:
        def debugPrint(self, message):
            """for debugging"""
            return self.notify.debug(
                    str(self.__dict__.get('houseId', '?'))+' '+message)


