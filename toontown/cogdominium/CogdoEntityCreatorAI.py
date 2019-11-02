from direct.showbase.PythonUtil import Functor
from otp.level import EntityCreatorAI
from toontown.cogdominium.CogdoLevelMgrAI import CogdoLevelMgrAI
from toontown.cogdominium import CogdoBoardroomGameConsts
from toontown.cogdominium import CogdoCraneGameConsts

class CogdoEntityCreatorAI(EntityCreatorAI.EntityCreatorAI):

    def __init__(self, level):
        EntityCreatorAI.EntityCreatorAI.__init__(self, level)
        cDE = EntityCreatorAI.createDistributedEntity
        cLE = EntityCreatorAI.createLocalEntity
        nothing = EntityCreatorAI.nothing
        self.privRegisterTypes({
            'levelMgr': Functor(cLE, CogdoLevelMgrAI),
            'cogdoBoardroomGameSettings': Functor(cLE, Functor(self._createCogdoSettings, CogdoBoardroomGameConsts.Settings)),
            'cogdoCraneGameSettings': Functor(cLE, Functor(self._createCogdoSettings, CogdoCraneGameConsts.Settings)),
            'cogdoCraneCogSettings': Functor(cLE, Functor(self._createCogdoSettings, CogdoCraneGameConsts.CogSettings))})

    def _createCogdoSettings(self, ent, level, entId):
        ent.initializeEntity(level, entId)
        return ent
