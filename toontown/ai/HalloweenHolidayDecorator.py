#################################################
# Halloween decorator class for non-dna based
# decoration changes to hoods
#################################################

# Panda3D imports
from panda3d.core import Vec4, CSDefault
from panda3d.toontown import loadDNAFile
from direct.directnotify import DirectNotifyGlobal
from direct.distributed.ClockDelta import *
from direct.interval.IntervalGlobal import *

from . import HolidayDecorator
from toontown.toonbase import ToontownGlobals
from toontown.safezone import Playground
from toontown.town import Street
from toontown.estate import Estate


class HalloweenHolidayDecorator(HolidayDecorator.HolidayDecorator):
    notify = DirectNotifyGlobal.directNotify.newCategory('HalloweenHolidayDecorator')

    def __init__(self):
        HolidayDecorator.HolidayDecorator.__init__(self)

    #####################################################
    # Function that checks the validity of a street,
    # it's loader and the geometry
    #####################################################
    def __checkStreetValidity(self):
        if hasattr(base.cr.playGame, "getPlace") and base.cr.playGame.getPlace() and \
                isinstance(base.cr.playGame.getPlace(), Street.Street) and \
                hasattr(base.cr.playGame.getPlace(), "loader") and base.cr.playGame.getPlace().loader \
                and hasattr(base.cr.playGame.getPlace().loader, "geom") and base.cr.playGame.getPlace().loader.geom:
            return True
        else:
            if hasattr(base.cr.playGame, "getPlace") and base.cr.playGame.getPlace():
                self.notify.debug("Failed Street Check %s" % base.cr.playGame.getPlace())
            else:
                self.notify.debug("Failed Street Check")
            return False

    #####################################################
    # Function that checks the validity of a hood,
    # it's loader and the geometry
    #####################################################
    def __checkHoodValidity(self):
        if hasattr(base.cr.playGame, "getPlace") and base.cr.playGame.getPlace() and \
                (isinstance(base.cr.playGame.getPlace(), Playground.Playground) or isinstance(
                    base.cr.playGame.getPlace(), Estate.Estate)) and \
                hasattr(base.cr.playGame.getPlace(), "loader") and base.cr.playGame.getPlace().loader and \
                hasattr(base.cr.playGame.getPlace().loader, "hood") and base.cr.playGame.getPlace().loader.hood and \
                hasattr(base.cr.playGame.getPlace().loader.hood,
                        "loader") and base.cr.playGame.getPlace().loader.hood.loader \
                and hasattr(base.cr.playGame.getPlace().loader.hood.loader,
                            "geom") and base.cr.playGame.getPlace().loader.hood.loader.geom:
            return True
        else:
            if hasattr(base.cr.playGame, "getPlace") and base.cr.playGame.getPlace():
                self.notify.debug("Failed Hood Check %s" % base.cr.playGame.getPlace())
            else:
                self.notify.debug("Failed Hood Check")
            return False

    #####################################################
    # This function safely calls startSpookySky
    # for the halloween holiday
    #####################################################
    def __startSpookySky(self):
        if (self.__checkHoodValidity() or self.__checkStreetValidity()) and hasattr(base.cr.playGame.hood, "sky") \
                and base.cr.playGame.hood.sky:
            base.cr.playGame.hood.startSpookySky()

    ####################################################
    # This function safely calls stopSpookySky
    # for the halloween holiday
    ####################################################
    def __stopSpookySky(self):
        if (self.__checkHoodValidity() or self.__checkStreetValidity()) and hasattr(base.cr.playGame.hood, "sky") \
                and base.cr.playGame.hood.sky:
            base.cr.playGame.hood.endSpookySky()

    def decorate(self):
        # Load the specified seasonal storage file
        self.updateHoodDNAStore()
        self.swapIval = self.getSwapVisibleIval()
        if self.swapIval:
            self.swapIval.start()

        def __lightDecorationOn__():
            # import pdb; pdb.set_trace()
            place = base.cr.playGame.getPlace()
            if hasattr(place, "halloweenLights"):
                if not self.__checkStreetValidity():
                    return
                else:
                    place.halloweenLights = place.loader.geom.findAllMatches("**/*light*")
                    place.halloweenLights += place.loader.geom.findAllMatches("**/*lamp*")
                    place.halloweenLights += place.loader.geom.findAllMatches("**/prop_snow_tree*")
                    for light in place.halloweenLights:
                        light.setColorScaleOff(0)
            else:
                if not self.__checkHoodValidity():
                    return
                else:
                    place.loader.hood.halloweenLights = place.loader.hood.loader.geom.findAllMatches("**/*light*")
                    place.loader.hood.halloweenLights += place.loader.hood.loader.geom.findAllMatches("**/*lamp*")
                    place.loader.hood.halloweenLights += place.loader.hood.loader.geom.findAllMatches(
                        "**/prop_snow_tree*")
                    for light in place.loader.hood.halloweenLights:
                        light.setColorScaleOff(0)

        holidayIds = base.cr.newsManager.getDecorationHolidayId()
        if ToontownGlobals.HALLOWEEN_COSTUMES not in holidayIds:
            return
        # Fixes transition related crashes
        if (self.__checkHoodValidity() or self.__checkStreetValidity()) and hasattr(base.cr.playGame, "hood") \
                and base.cr.playGame.hood and hasattr(base.cr.playGame.hood, "sky") \
                and base.cr.playGame.hood.sky:
            preShow = Sequence(
                Parallel(
                    LerpColorScaleInterval(
                        base.cr.playGame.hood.sky,
                        1.5, Vec4(1, 1, 1, 0.25)
                    ),
                    LerpColorScaleInterval(
                        base.cr.playGame.hood.loader.geom,
                        2.5,
                        Vec4(0.55, 0.55, 0.65, 1)
                    ),
                    Func(__lightDecorationOn__),
                ),
                Func(self.__startSpookySky),
            )

            preShow.start()

        # Replace the plane with the witch in the estate
        distributedEstate = base.cr.doFind("DistributedEstate")

        if distributedEstate:
            distributedEstate.loadWitch()

    def undecorate(self):

        # Fixes transition related crashes
        if (self.__checkHoodValidity() or self.__checkStreetValidity()) and hasattr(base.cr.playGame.hood, "sky") \
                and base.cr.playGame.hood.sky:
            postShow = Sequence(
                Parallel(
                    LerpColorScaleInterval(
                        base.cr.playGame.hood.sky,
                        1.5, Vec4(1, 1, 1, 1)
                    ),
                    LerpColorScaleInterval(
                        base.cr.playGame.hood.loader.geom,
                        2.5,
                        Vec4(1, 1, 1, 1)
                    ),
                ),
                Func(self.__stopSpookySky),
            )
            postShow.start()

        # Replace the witch with the plane
        distributedEstate = base.cr.doFind("DistributedEstate")

        if distributedEstate:
            distributedEstate.unloadWitch()

        # if there are any other decoration holidays running
        holidayIds = base.cr.newsManager.getDecorationHolidayId()
        if len(holidayIds) > 0:
            self.decorate()
            return

        # Reload the regular storage file
        storageFile = base.cr.playGame.hood.storageDNAFile
        if storageFile:
            loadDNAFile(self.dnaStore, storageFile, CSDefault)
        self.swapIval = self.getSwapVisibleIval()
        if self.swapIval:
            self.swapIval.start()
