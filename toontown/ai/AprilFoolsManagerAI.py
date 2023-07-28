##############################################
# Class: LowGravManagerAI
# This class handles April Fools changes
##############################################

from toontown.ai import HolidayBaseAI
from toontown.ai import CostumeManagerAI
from toontown.toonbase import ToontownGlobals
from direct.showbase import DirectObject
from toontown.toonbase import TTLocalizer
from direct.directnotify import DirectNotifyGlobal

class AprilFoolsManagerAI(CostumeManagerAI.CostumeManagerAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('AprilFoolsManagerAI')

    def __init__(self, air, holidayId):
        CostumeManagerAI.CostumeManagerAI.__init__(self, air, holidayId)

    # Overridden function
    def start(self):
        CostumeManagerAI.CostumeManagerAI.start(self)

        estateManager = simbase.air.doFind("EstateManagerAI.EstateManagerAI")
        if estateManager != None:
            estateManager.startAprilFools()

    # Overridden function
    def stop(self):
        CostumeManagerAI.CostumeManagerAI.stop(self)

        estateManager = simbase.air.doFind("EstateManagerAI.EstateManagerAI")
        if estateManager != None:
            estateManager.stopAprilFools()
