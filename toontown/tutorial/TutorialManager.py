from direct.distributed import DistributedObject
from direct.directnotify import DirectNotifyGlobal
from toontown.hood import ZoneUtil


class TutorialManager(DistributedObject.DistributedObject):
    notify = DirectNotifyGlobal.directNotify.newCategory("TutorialManager")
    neverDisable = 1

    def generate(self):
        DistributedObject.DistributedObject.generate(self)
        # Let the cr know we have arrived.
        messenger.send("tmGenerate")
        # Wait for a tutorial request or rejection.
        self.accept("requestTutorial", self.d_requestTutorial)
        self.accept("requestSkipTutorial", self.d_requestSkipTutorial)
        self.accept("rejectTutorial", self.d_rejectTutorial)

    def disable(self):
        self.ignoreAll()
        # In case we fell asleep in the tutorial
        ZoneUtil.overrideOff()
        DistributedObject.DistributedObject.disable(self)

    def d_requestTutorial(self):
        self.sendUpdate("requestTutorial", [])

    def d_rejectTutorial(self):
        self.sendUpdate("rejectTutorial", [])

    def d_requestSkipTutorial(self):
        self.sendUpdate("requestSkipTutorial", [])

    def skipTutorialResponse(self, allOk):
        """Handle AI responding to our skip tutorial request."""
        messenger.send("skipTutorialAnswered", [allOk])

    def enterTutorial(self, branchZone, streetZone, shopZone, hqZone):
        base.localAvatar.cantLeaveGame = 1
        # Override the ZoneUtil
        ZoneUtil.overrideOn(branch=branchZone,
                            exteriorList=[streetZone],
                            interiorList=[shopZone, hqZone])
        # We start the tutorial in the gag shop.
        messenger.send("startTutorial", [shopZone])
        # Add a hook on the tutorialDone event, which will get
        # thrown when we are leaving the tutorial (by the handleEnterTunnel
        # function in TutorialStreet.py
        self.acceptOnce("stopTutorial", self.__handleStopTutorial)
        # Add a hook that the Tutorial hood will send when the toon
        # is fully in a zone.  This lets the AI know it is clear to
        # reset the toon properties in preparation for the tutorial
        # (in case they bailed halfway through before)
        self.acceptOnce("toonArrivedTutorial", self.d_toonArrived)

    def __handleStopTutorial(self):
        base.localAvatar.cantLeaveGame = 0
        self.d_allDone()
        ZoneUtil.overrideOff()

    def d_allDone(self):
        self.sendUpdate("allDone", [])

    def d_toonArrived(self):
        self.sendUpdate("toonArrived", [])
