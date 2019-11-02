from direct.directnotify import DirectNotifyGlobal
from direct.fsm import StateData
from direct.fsm import ClassicFSM, State
from direct.fsm import State
import CogHQLobby
from toontown.hood import QuietZoneState
from toontown.hood import ZoneUtil
from toontown.town import TownBattle
from toontown.suit import Suit
from pandac.PandaModules import *

class CogHQLoader(StateData.StateData):
    notify = DirectNotifyGlobal.directNotify.newCategory('CogHQLoader')

    def __init__(self, hood, parentFSMState, doneEvent):
        StateData.StateData.__init__(self, doneEvent)
        self.hood = hood
        self.parentFSMState = parentFSMState
        self.placeDoneEvent = 'cogHQLoaderPlaceDone'
        self.townBattleDoneEvent = 'town-battle-done'
        self.fsm = ClassicFSM.ClassicFSM('CogHQLoader', [State.State('start', None, None, ['quietZone', 'cogHQExterior', 'cogHQBossBattle']),
         State.State('cogHQExterior', self.enterCogHQExterior, self.exitCogHQExterior, ['quietZone', 'cogHQLobby']),
         State.State('cogHQLobby', self.enterCogHQLobby, self.exitCogHQLobby, ['quietZone', 'cogHQExterior', 'cogHQBossBattle']),
         State.State('cogHQBossBattle', self.enterCogHQBossBattle, self.exitCogHQBossBattle, ['quietZone']),
         State.State('quietZone', self.enterQuietZone, self.exitQuietZone, ['cogHQExterior', 'cogHQLobby', 'cogHQBossBattle']),
         State.State('final', None, None, ['start'])], 'start', 'final')
        return

    def load(self, zoneId):
        self.parentFSMState.addChild(self.fsm)
        self.music = base.loadMusic(self.musicFile)
        self.battleMusic = base.loadMusic('phase_9/audio/bgm/encntr_suit_winning.mid')
        self.townBattle = TownBattle.TownBattle(self.townBattleDoneEvent)
        self.townBattle.load()
        Suit.loadSuits(3)
        self.loadPlaceGeom(zoneId)

    def loadPlaceGeom(self, zoneId):
        pass

    def unloadPlaceGeom(self):
        pass

    def unload(self):
        self.unloadPlaceGeom()
        self.parentFSMState.removeChild(self.fsm)
        del self.parentFSMState
        del self.fsm
        self.townBattle.unload()
        self.townBattle.cleanup()
        del self.townBattle
        del self.battleMusic
        Suit.unloadSuits(3)
        Suit.unloadSkelDialog()
        del self.hood
        ModelPool.garbageCollect()
        TexturePool.garbageCollect()

    def enter(self, requestStatus):
        self.fsm.enterInitialState()
        self.fsm.request(requestStatus['where'], [requestStatus])

    def exit(self):
        self.ignoreAll()

    def enterQuietZone(self, requestStatus):
        self.quietZoneDoneEvent = uniqueName('quietZoneDone')
        self.acceptOnce(self.quietZoneDoneEvent, self.handleQuietZoneDone)
        self.quietZoneStateData = QuietZoneState.QuietZoneState(self.quietZoneDoneEvent)
        self.quietZoneStateData.load()
        self.quietZoneStateData.enter(requestStatus)

    def exitQuietZone(self):
        self.ignore(self.quietZoneDoneEvent)
        del self.quietZoneDoneEvent
        self.quietZoneStateData.exit()
        self.quietZoneStateData.unload()
        self.quietZoneStateData = None
        return

    def handleQuietZoneDone(self):
        status = self.quietZoneStateData.getRequestStatus()
        self.fsm.request(status['where'], [status])

    def enterPlace(self, requestStatus):
        self.acceptOnce(self.placeDoneEvent, self.placeDone)
        self.place = self.placeClass(self, self.fsm, self.placeDoneEvent)
        base.cr.playGame.setPlace(self.place)
        self.place.load()
        self.place.enter(requestStatus)

    def exitPlace(self):
        self.ignore(self.placeDoneEvent)
        self.place.exit()
        self.place.unload()
        self.place = None
        base.cr.playGame.setPlace(self.place)
        return

    def placeDone(self):
        self.requestStatus = self.place.doneStatus
        status = self.place.doneStatus
        if status.get('shardId') == None and self.isInThisHq(status):
            self.unloadPlaceGeom()
            zoneId = status['zoneId']
            self.loadPlaceGeom(zoneId)
            self.fsm.request('quietZone', [status])
        else:
            self.doneStatus = status
            messenger.send(self.doneEvent)
        return

    def isInThisHq(self, status):
        if ZoneUtil.isDynamicZone(status['zoneId']):
            return status['hoodId'] == self.hood.hoodId
        else:
            return ZoneUtil.getHoodId(status['zoneId']) == self.hood.hoodId

    def enterCogHQExterior(self, requestStatus):
        self.placeClass = self.getExteriorPlaceClass()
        self.enterPlace(requestStatus)
        self.hood.spawnTitleText(requestStatus['zoneId'])

    def exitCogHQExterior(self):
        taskMgr.remove('titleText')
        self.hood.hideTitleText()
        self.exitPlace()
        self.placeClass = None
        return

    def enterCogHQLobby(self, requestStatus):
        self.placeClass = CogHQLobby.CogHQLobby
        self.enterPlace(requestStatus)
        self.hood.spawnTitleText(requestStatus['zoneId'])

    def exitCogHQLobby(self):
        taskMgr.remove('titleText')
        self.hood.hideTitleText()
        self.exitPlace()
        self.placeClass = None
        return

    def enterCogHQBossBattle(self, requestStatus):
        self.placeClass = self.getBossPlaceClass()
        self.enterPlace(requestStatus)

    def exitCogHQBossBattle(self):
        self.exitPlace()
        self.placeClass = None
        return
