from pandac.PandaModules import NodePath
from toontown.toonbase import TTLocalizer
from toontown.parties.DistributedPartyCatchActivity import DistributedPartyCatchActivity
from toontown.parties import PartyGlobals
from toontown.parties import WinterPartyCatchActivityToonSD

class DistributedPartyWinterCatchActivity(DistributedPartyCatchActivity):

    def __init__(self, cr):
        DistributedPartyCatchActivity.__init__(self, cr)

    def getInstructions(self):
        return TTLocalizer.WinterPartyCatchActivityInstructions % {'badThing': self.DropObjectPlurals['anvil']}

    def load(self):
        DistributedPartyCatchActivity.load(self, loadModels=0, arenaModel='tt_m_ara_pty_partyCatchTreeWinter')
        self.__loadDropModels()

    def __loadDropModels(self):
        for objType in PartyGlobals.DropObjectTypes:
            model = None
            if not objType == PartyGlobals.Name2DropObjectType['anvil']:
                model = loader.loadModel('phase_13/models/parties/tt_m_ara_pty_winterPresent')
                model.setScale(0.5)
            else:
                model = loader.loadModel(objType.modelPath)
            self.dropObjModels[objType.name] = model
            model.flattenStrong()

        return

    def handleToonJoined(self, toonId):
        if not self.toonSDs.has_key(toonId):
            toonSD = WinterPartyCatchActivityToonSD.WinterPartyCatchActivityToonSD(toonId, self)
            self.toonSDs[toonId] = toonSD
            toonSD.load()
        self.notify.debug('handleToonJoined : currentState = %s' % self.activityFSM.state)
        self.cr.doId2do[toonId].useLOD(500)
        if self.activityFSM.state == 'Active':
            if self.toonSDs.has_key(toonId):
                self.toonSDs[toonId].enter()
            if base.localAvatar.doId == toonId:
                base.localAvatar.b_setParent(self._avatarNodePathParentToken)
                self.putLocalAvatarInActivity()
            if self.toonSDs.has_key(toonId):
                self.toonSDs[toonId].fsm.request('rules')
