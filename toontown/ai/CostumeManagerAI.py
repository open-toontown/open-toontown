##############################################
# Class: CostumeManagerAI
# This class handles the loading of new
# models that will replace models in one
# or more hoods based on the holiday
# requirements.
##############################################

from toontown.ai import HolidayBaseAI
from toontown.toonbase import ToontownGlobals
from direct.directnotify import DirectNotifyGlobal
from toontown.classicchars import *
from direct.task import Task
from direct.fsm import State
from toontown.hood import *
from direct.showbase import DirectObject
from toontown.toonbase import TTLocalizer
from toontown.classicchars import *
from toontown.classicchars import DistributedVampireMickeyAI, DistributedSuperGoofyAI, DistributedWesternPlutoAI
from toontown.classicchars import DistributedWitchMinnieAI, DistributedMinnieAI, DistributedPlutoAI
from toontown.hood import MMHoodDataAI, BRHoodDataAI

class CostumeManagerAI(HolidayBaseAI.HolidayBaseAI, DirectObject.DirectObject):
    notify = DirectNotifyGlobal.directNotify.newCategory('CostumeManagerAI')

    def __init__(self, air, holidayId):
        HolidayBaseAI.HolidayBaseAI.__init__(self, air, holidayId)
        self.__classicChars = {}
        self.hoods = []

        self.runningState = 1

        self.cCharsSwitched = 0

        # For use with magic words
        self.stopForever = False

    # Overridden function
    ######################################################
    # General format: if(self.holidayId == HOLIDAY_ID)
    # Get hood and call switchChars with new hood
    #  and classicChar class.
    ######################################################
    def start(self):
        if(self.holidayId == ToontownGlobals.HALLOWEEN_COSTUMES):
            self.accept("TTHoodSpawned", self.__welcomeValleySpawned)
            self.accept("TTHoodDestroyed", self.__welcomeValleyDestroyed)
            self.accept("GSHoodSpawned", self.__welcomeValleySpawned)
            self.accept("GSHoodDestroyed", self.__welcomeValleyDestroyed)

            if hasattr(simbase.air, "holidayManager") and simbase.air.holidayManager is not None:
                if self.holidayId in simbase.air.holidayManager.currentHolidays and simbase.air.holidayManager.currentHolidays[self.holidayId] != None:
                    return

            for hood in simbase.air.hoods:
                if isinstance(hood, TTHoodDataAI.TTHoodDataAI):
                    self.hoods.append(hood)
                    self.__classicChars[str(hood)] = 1
                    hood.classicChar.transitionCostume()
                elif isinstance(hood, MMHoodDataAI.MMHoodDataAI):
                    self.hoods.append(hood)
                    self.__classicChars[str(hood)] = 1
                    hood.classicChar.transitionCostume()
                elif isinstance(hood, GSHoodDataAI.GSHoodDataAI):
                    self.hoods.append(hood)
                    self.__classicChars[str(hood)] = 1
                    hood.classicChar.transitionCostume()
                elif isinstance(hood, BRHoodDataAI.BRHoodDataAI):
                    self.hoods.append(hood)
                    self.__classicChars[str(hood)] = 1
                    hood.classicChar.transitionCostume()

        elif(self.holidayId == ToontownGlobals.APRIL_FOOLS_COSTUMES):
            self.accept("TTHoodSpawned", self.__welcomeValleySpawned)
            self.accept("TTHoodDestroyed", self.__welcomeValleyDestroyed)
            self.accept("GSHoodSpawned", self.__welcomeValleySpawned)
            self.accept("GSHoodDestroyed", self.__welcomeValleyDestroyed)

            if hasattr(simbase.air, "holidayManager"):
                if self.holidayId in simbase.air.holidayManager.currentHolidays and simbase.air.holidayManager.currentHolidays[self.holidayId] != None:
                    return

            for hood in simbase.air.hoods:
                # The character is neither transitioning or has transitioned into a different costume
                if hasattr(hood, "classicChar") and hood.classicChar.transitionToCostume == 0 and hood.classicChar.diffPath == None:
                    if isinstance(hood, TTHoodDataAI.TTHoodDataAI):
                        # import pdb; pdb.set_trace()
                        self.hoods.append(hood)
                        self.__classicChars[str(hood)] = 1
                        hood.classicChar.transitionCostume()
                    elif isinstance(hood, BRHoodDataAI.BRHoodDataAI ):
                        self.hoods.append(hood)
                        self.__classicChars[str(hood)] = 1
                        hood.classicChar.transitionCostume()
                    elif isinstance(hood, MMHoodDataAI.MMHoodDataAI ):
                        self.hoods.append(hood)
                        self.__classicChars[str(hood)] = 1
                        hood.classicChar.transitionCostume()
                    elif isinstance(hood, DGHoodDataAI.DGHoodDataAI ):
                        self.hoods.append(hood)
                        self.__classicChars[str(hood)] = 1
                        hood.classicChar.transitionCostume()
                    elif isinstance(hood, DLHoodDataAI.DLHoodDataAI ):
                        self.hoods.append(hood)
                        self.__classicChars[str(hood)] = 1
                        hood.classicChar.transitionCostume()
                    elif isinstance(hood, GSHoodDataAI.GSHoodDataAI ):
                        self.hoods.append(hood)
                        self.__classicChars[str(hood)] = 1
                        hood.classicChar.transitionCostume()

    # Overridden function
    def stop(self):
        self.ignoreAll()
        del self.__classicChars
        pass

    def goingToStop(self, stopForever=False):
        # import pdb; pdb.set_trace()
        self.notify.debug("GoingToStop")
        self.stopForever = stopForever
        self.runningState = 0
        if(self.holidayId in [ToontownGlobals.HALLOWEEN_COSTUMES, ToontownGlobals.APRIL_FOOLS_COSTUMES]):
            self.ignore("TTHoodSpawned")
            self.ignore("GSHoodSpawned")
            for hood in self.hoods:
                hood.classicChar.transitionCostume()
                self.__classicChars[str(hood)] = 0

    def getRunningState(self):
        return self.runningState

    ########################################################
    # Trigger the switching of the character
    ########################################################
    def triggerSwitch(self, curWalkNode, curChar):
        if(self.holidayId == ToontownGlobals.HALLOWEEN_COSTUMES):
            for hood in self.hoods:
                if hood.classicChar == curChar:
                    hood.classicChar.fadeAway()
                    if(curChar.getName() == TTLocalizer.VampireMickey):
                        taskMgr.doMethodLater(0.5, self.__switchChars, "SwitchChars"+str(hood), extraArgs = [DistributedMickeyAI.DistributedMickeyAI, curWalkNode, hood])
                    elif(curChar.getName() == TTLocalizer.Mickey):
                        taskMgr.doMethodLater(0.5, self.__switchChars, "SwitchChars"+str(hood), extraArgs = [DistributedVampireMickeyAI.DistributedVampireMickeyAI, curWalkNode, hood])
                    elif(curChar.getName() == TTLocalizer.WitchMinnie):
                        taskMgr.doMethodLater(0.5, self.__switchChars, "SwitchChars"+str(hood), extraArgs = [DistributedMinnieAI.DistributedMinnieAI, curWalkNode, hood])
                    elif(curChar.getName() == TTLocalizer.Minnie):
                        taskMgr.doMethodLater(0.5, self.__switchChars, "SwitchChars"+str(hood), extraArgs = [DistributedWitchMinnieAI.DistributedWitchMinnieAI, curWalkNode, hood])
                    elif(curChar.getName() == TTLocalizer.Goofy):
                        taskMgr.doMethodLater(0.5, self.__switchChars, "SwitchChars"+str(hood), extraArgs = [DistributedSuperGoofyAI.DistributedSuperGoofyAI, curWalkNode, hood])
                    elif(curChar.getName() == TTLocalizer.SuperGoofy):
                        taskMgr.doMethodLater(0.5, self.__switchChars, "SwitchChars"+str(hood), extraArgs = [DistributedGoofySpeedwayAI.DistributedGoofySpeedwayAI, curWalkNode, hood])
                    elif(curChar.getName() == TTLocalizer.Pluto):
                        taskMgr.doMethodLater(0.5, self.__switchChars, "SwitchChars"+str(hood), extraArgs = [DistributedWesternPlutoAI.DistributedWesternPlutoAI, curWalkNode, hood])
                    elif(curChar.getName() == TTLocalizer.WesternPluto):
                        taskMgr.doMethodLater(0.5, self.__switchChars, "SwitchChars"+str(hood), extraArgs = [DistributedPlutoAI.DistributedPlutoAI, curWalkNode, hood])
        elif(self.holidayId == ToontownGlobals.APRIL_FOOLS_COSTUMES):
            for hood in self.hoods:
                if hood.classicChar == curChar:
                    hood.classicChar.fadeAway()
                    if(curChar.getName() == TTLocalizer.Daisy):
                        taskMgr.doMethodLater(0.5, self.__switchChars, "SwitchChars"+str(hood), extraArgs = [DistributedMickeyAI.DistributedMickeyAI, curWalkNode, hood])
                    elif(curChar.getName() == TTLocalizer.Mickey):
                        taskMgr.doMethodLater(0.5, self.__switchChars, "SwitchChars"+str(hood), extraArgs = [DistributedDaisyAI.DistributedDaisyAI, curWalkNode, hood])
                    elif(curChar.getName() == TTLocalizer.Goofy):
                        taskMgr.doMethodLater(0.5, self.__switchChars, "SwitchChars"+str(hood), extraArgs = [DistributedDonaldAI.DistributedDonaldAI, curWalkNode, hood])
                    elif(curChar.getName() == TTLocalizer.Donald):
                        taskMgr.doMethodLater(0.5, self.__switchChars, "SwitchChars"+str(hood), extraArgs = [DistributedGoofySpeedwayAI.DistributedGoofySpeedwayAI, curWalkNode, hood])
                    elif(curChar.getName() == TTLocalizer.Pluto):
                        taskMgr.doMethodLater(0.5, self.__switchChars, "SwitchChars"+str(hood), extraArgs = [DistributedMinnieAI.DistributedMinnieAI, curWalkNode, hood])
                    elif(curChar.getName() == TTLocalizer.Minnie):
                        taskMgr.doMethodLater(0.5, self.__switchChars, "SwitchChars"+str(hood), extraArgs = [DistributedPlutoAI.DistributedPlutoAI, curWalkNode, hood])


    ########################################################
    # Switched the classic character with a new one
    # represented by class 'newChar' in 'hood'.
    ########################################################
    def __switchChars(self, newChar, walkNode, hood):
        self.notify.debug("SwitchingChars %s to %s" %(hood.classicChar, newChar))
        self.notify.debugStateCall(self)
        hood.classicChar.requestDelete()
        if hasattr(hood, "air") and hood.air:
            hood.classicChar = newChar(hood.air)
            hood.classicChar.generateWithRequired(hood.zoneId)
            hood.addDistObj(hood.classicChar)
            hood.classicChar.walk.setCurNode(walkNode)
            hood.classicChar.fsm.request('Walk')
        else:
            self.notify.warning("Hood empty during character switch")
        holidayDone = 1
        for classicChar in self.__classicChars.values():
            if classicChar == 1:
                holidayDone = 0
        if holidayDone:
            self.cCharsSwitched += 1
        if self.cCharsSwitched == len(self.__classicChars):
            simbase.air.holidayManager.delayedEnd(self.holidayId, self.stopForever)

    ########################################################
    # Function to handle the spawning of a new welcome
    # valley server
    ########################################################

    def __welcomeValleySpawned(self, newHood):
        if(self.holidayId == ToontownGlobals.HALLOWEEN_COSTUMES):
            self.__addAVampire(newHood)
        elif(self.holidayId == ToontownGlobals.APRIL_FOOLS_COSTUMES):
            self.__aprilFoolsSwap(newHood)

    def __welcomeValleyDestroyed(self, newHood):
        if(self.holidayId == ToontownGlobals.HALLOWEEN_COSTUMES):
            self.__removeAVampire(newHood)
        elif(self.holidayId == ToontownGlobals.APRIL_FOOLS_COSTUMES):
            self.__aprilFoolsRevert(newHood)

    def __aprilFoolsSwap(self, newHood):
        for hood in self.hoods:
            if hood == newHood:
                return

        self.hoods.append(newHood)
        self.__classicChars[str(newHood)] = 1
        newHood.classicChar.transitionCostume()

    def __aprilFoolsRevert(self, deadHood):
        if str(deadHood) in self.__classicChars:
            del self.__classicChars[str(deadHood)]
        for hood in self.hoods:
            if hood == deadHood:
                self.hoods.remove(hood)
                return

    def __addAVampire(self, newHood):
        for hood in self.hoods:
            if hood == newHood:
                return

        self.hoods.append(newHood)
        self.__classicChars[str(newHood)] = 1
        newHood.classicChar.transitionCostume()

    def __removeAVampire(self, deadHood):
        if str(deadHood) in self.__classicChars:
            del self.__classicChars[str(deadHood)]
        for hood in self.hoods:
            if hood == deadHood:
                self.hoods.remove(hood)
                return
