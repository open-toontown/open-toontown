from pandac.PandaModules import *
from toontown.toon import Toon
from toontown.hood import Place
from toontown.hood import ZoneUtil
from toontown.toonbase import ToontownGlobals

class BattlePlace(Place.Place):

    def __init__(self, loader, doneEvent):
        Place.Place.__init__(self, loader, doneEvent)

    def load(self):
        Place.Place.load(self)
        Toon.loadBattleAnims()

    def setState(self, state, battleEvent = None):
        if battleEvent:
            if not self.fsm.request(state, [battleEvent]):
                self.notify.warning("fsm.request('%s') returned 0 (zone id %s, avatar pos %s)." % (state, self.zoneId, base.localAvatar.getPos(render)))
        elif not self.fsm.request(state):
            self.notify.warning("fsm.request('%s') returned 0 (zone id %s, avatar pos %s)." % (state, self.zoneId, base.localAvatar.getPos(render)))

    def enterWalk(self, flag = 0):
        Place.Place.enterWalk(self, flag)
        self.accept('enterBattle', self.handleBattleEntry)

    def exitWalk(self):
        Place.Place.exitWalk(self)
        self.ignore('enterBattle')

    def enterWaitForBattle(self):
        base.localAvatar.b_setAnimState('neutral', 1)

    def exitWaitForBattle(self):
        pass

    def enterBattle(self, event):
        if base.config.GetBool('want-qa-regression', 0):
            self.notify.info('QA-REGRESSION: COGBATTLE: Enter Battle')
        self.loader.music.stop()
        base.playMusic(self.loader.battleMusic, looping=1, volume=0.9)
        self.enterTownBattle(event)
        base.localAvatar.b_setAnimState('off', 1)
        self.accept('teleportQuery', self.handleTeleportQuery)
        base.localAvatar.setTeleportAvailable(1)
        base.localAvatar.cantLeaveGame = 1

    def enterTownBattle(self, event):
        self.loader.townBattle.enter(event, self.fsm.getStateNamed('battle'))

    def exitBattle(self):
        self.loader.townBattle.exit()
        self.loader.battleMusic.stop()
        base.playMusic(self.loader.music, looping=1, volume=0.8)
        base.localAvatar.cantLeaveGame = 0
        base.localAvatar.setTeleportAvailable(0)
        self.ignore('teleportQuery')

    def handleBattleEntry(self):
        self.fsm.request('battle')

    def enterFallDown(self, extraArgs = []):
        base.localAvatar.laffMeter.start()
        base.localAvatar.b_setAnimState('FallDown', callback=self.handleFallDownDone, extraArgs=extraArgs)

    def handleFallDownDone(self):
        base.cr.playGame.getPlace().setState('walk')

    def exitFallDown(self):
        base.localAvatar.laffMeter.stop()

    def enterSquished(self):
        base.localAvatar.laffMeter.start()
        base.localAvatar.b_setAnimState('Squish')
        taskMgr.doMethodLater(2.0, self.handleSquishDone, base.localAvatar.uniqueName('finishSquishTask'))

    def handleSquishDone(self, extraArgs = []):
        base.cr.playGame.getPlace().setState('walk')

    def exitSquished(self):
        taskMgr.remove(base.localAvatar.uniqueName('finishSquishTask'))
        base.localAvatar.laffMeter.stop()

    def enterZone(self, newZone):
        if isinstance(newZone, CollisionEntry):
            try:
                newZoneId = int(newZone.getIntoNode().getName())
            except:
                self.notify.warning('Invalid floor collision node in street: %s' % newZone.getIntoNode().getName())
                return

        else:
            newZoneId = newZone
        self.doEnterZone(newZoneId)

    def doEnterZone(self, newZoneId):
        if newZoneId != self.zoneId:
            if newZoneId != None:
                if base.cr.astronSupport:
                    if hasattr(self, 'zoneVisDict'):
                        visList = self.zoneVisDict[newZoneId]
                    else:
                        visList = base.cr.playGame.getPlace().loader.zoneVisDict[newZoneId]

                    base.cr.sendSetZoneMsg(newZoneId, visList)
                else:
                    base.cr.sendSetZoneMsg(newZoneId)
                self.notify.debug('Entering Zone %d' % newZoneId)
            self.zoneId = newZoneId
        return

    if config.GetBool('astron-support', True):
        def genDNAFileName(self, zoneId):
            zoneId = ZoneUtil.getCanonicalZoneId(zoneId)
            hoodId = ZoneUtil.getCanonicalHoodId(zoneId)
            hood = ToontownGlobals.dnaMap[hoodId]
            phase = ToontownGlobals.streetPhaseMap[hoodId]
            if hoodId == zoneId:
                zoneId = 'sz'

            return 'phase_%s/dna/%s_%s.dna' % (phase, hood, zoneId)
