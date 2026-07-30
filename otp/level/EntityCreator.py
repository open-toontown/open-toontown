from . import CutScene
from . import EntityCreatorBase
from . import BasicEntities
from direct.directnotify import DirectNotifyGlobal
from . import EditMgr
from . import EntrancePoint
from . import LevelMgr
from . import LogicGate
from . import ZoneEntity
from . import ModelEntity
from . import PathEntity
from . import VisibilityExtender
from . import PropSpinner
from . import AmbientSound
from . import LocatorEntity
from . import CollisionSolidEntity

def nothing(*args):
    return 'nothing'


def nonlocalEnt(*args):
    return 'nonlocalEnt'


class EntityCreator(EntityCreatorBase.EntityCreatorBase):

    def __init__(self, level):
        EntityCreatorBase.EntityCreatorBase.__init__(self, level)
        self.level = level
        self.privRegisterTypes({'attribModifier': nothing,
         'ambientSound': AmbientSound.AmbientSound,
         'collisionSolid': CollisionSolidEntity.CollisionSolidEntity,
         'cutScene': CutScene.CutScene,
         'editMgr': EditMgr.EditMgr,
         'entityGroup': nothing,
         'entrancePoint': EntrancePoint.EntrancePoint,
         'levelMgr': LevelMgr.LevelMgr,
         'locator': LocatorEntity.LocatorEntity,
         'logicGate': LogicGate.LogicGate,
         'model': ModelEntity.ModelEntity,
         'nodepath': BasicEntities.NodePathEntity,
         'path': PathEntity.PathEntity,
         'propSpinner': PropSpinner.PropSpinner,
         'visibilityExtender': VisibilityExtender.VisibilityExtender,
         'zone': ZoneEntity.ZoneEntity})

    def doCreateEntity(self, ctor, entId):
        return ctor(self.level, entId)
