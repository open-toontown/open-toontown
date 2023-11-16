from otp.level import EntityCreator

from toontown.cogdominium import CogdoBoardroomGameConsts, CogdoCraneGameConsts
from toontown.cogdominium.CogdoLevelMgr import CogdoLevelMgr


class CogdoEntityCreator(EntityCreator.EntityCreator):

    def __init__(self, level):
        EntityCreator.EntityCreator.__init__(self, level)
        nothing = EntityCreator.nothing
        nonlocalEnt = EntityCreator.nonlocalEnt
        self.privRegisterTypes({'levelMgr': CogdoLevelMgr,
         'cogdoBoardroomGameSettings': Functor(self._createCogdoSettings, CogdoBoardroomGameConsts.Settings),
         'cogdoCraneGameSettings': Functor(self._createCogdoSettings, CogdoCraneGameConsts.Settings),
         'cogdoCraneCogSettings': Functor(self._createCogdoSettings, CogdoCraneGameConsts.CogSettings)})

    def _createCogdoSettings(self, ent, level, entId):
        ent.initializeEntity(level, entId)
        return ent
