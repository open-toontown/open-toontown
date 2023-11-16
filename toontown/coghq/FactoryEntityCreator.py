from otp.level import EntityCreator

from . import (ConveyorBelt, FactoryLevelMgr, GearEntity, GoonClipPlane, MintProduct, MintProductPallet, MintShelf,
               PaintMixer, PathMasterEntity, PlatformEntity, RenderingEntity)


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
