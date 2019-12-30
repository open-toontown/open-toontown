from otp.level import EntityCreator
from . import FactoryLevelMgr
from . import PlatformEntity
from . import ConveyorBelt
from . import GearEntity
from . import PaintMixer
from . import GoonClipPlane
from . import MintProduct
from . import MintProductPallet
from . import MintShelf
from . import PathMasterEntity
from . import RenderingEntity

class FactoryEntityCreator(EntityCreator.EntityCreator):

    def __init__(self, level):
        EntityCreator.EntityCreator.__init__(self, level)
        nothing = EntityCreator.nothing
        nonlocalEnt = EntityCreator.nonlocalEnt
        self.privRegisterTypes({'activeCell': nonlocalEnt,
         'crusherCell': nonlocalEnt,
         'battleBlocker': nonlocalEnt,
         'beanBarrel': nonlocalEnt,
         'button': nonlocalEnt,
         'conveyorBelt': ConveyorBelt.ConveyorBelt,
         'crate': nonlocalEnt,
         'door': nonlocalEnt,
         'directionalCell': nonlocalEnt,
         'gagBarrel': nonlocalEnt,
         'gear': GearEntity.GearEntity,
         'goon': nonlocalEnt,
         'gridGoon': nonlocalEnt,
         'golfGreenGame': nonlocalEnt,
         'goonClipPlane': GoonClipPlane.GoonClipPlane,
         'grid': nonlocalEnt,
         'healBarrel': nonlocalEnt,
         'levelMgr': FactoryLevelMgr.FactoryLevelMgr,
         'lift': nonlocalEnt,
         'mintProduct': MintProduct.MintProduct,
         'mintProductPallet': MintProductPallet.MintProductPallet,
         'mintShelf': MintShelf.MintShelf,
         'mover': nonlocalEnt,
         'paintMixer': PaintMixer.PaintMixer,
         'pathMaster': PathMasterEntity.PathMasterEntity,
         'rendering': RenderingEntity.RenderingEntity,
         'platform': PlatformEntity.PlatformEntity,
         'sinkingPlatform': nonlocalEnt,
         'stomper': nonlocalEnt,
         'stomperPair': nonlocalEnt,
         'laserField': nonlocalEnt,
         'securityCamera': nonlocalEnt,
         'elevatorMarker': nonlocalEnt,
         'trigger': nonlocalEnt,
         'moleField': nonlocalEnt,
         'maze': nonlocalEnt})
