from panda3d.core import ModelPool, TexturePool, ConfigVariableBool
from direct.directnotify.DirectNotifyGlobal import directNotify
from toontown.toonbase import ToontownGlobals

notify = directNotify.newCategory('ZonePrefetchCatalog')

ZONE_ASSETS_MAP = {
    2000: [
        'phase_4/models/neighborhoods/toontown_central',
        'phase_3.5/models/modules/skys/TT_sky',
        'phase_4/models/props/tt_m_prp_ext_fountain',
        'phase_3.5/models/props/tunnel_sign_toontown',
    ],
    1000: [
        'phase_6/models/neighborhoods/donalds_dock',
        'phase_3.5/models/modules/skys/cloud_sky',
        'phase_6/models/props/dock_boat',
    ],
    3000: [
        'phase_6/models/neighborhoods/minnies_melody_land',
        'phase_6/models/modules/skys/mml_sky',
    ],
    4000: [
        'phase_8/models/neighborhoods/daisys_garden',
        'phase_3.5/models/modules/skys/TT_sky',
    ],
    5000: [
        'phase_6/models/neighborhoods/the_brrrgh',
        'phase_6/models/modules/skys/brrrgh_sky',
    ],
    9000: [
        'phase_8/models/neighborhoods/donalds_dreamland',
        'phase_8/models/modules/skys/night_sky',
    ],
    8000: [
        'phase_6/models/karting/speedway_hub',
        'phase_3.5/models/modules/skys/TT_sky',
    ],
    6000: [
        'phase_6/models/golf/chip_n_dales_acorn_acres',
    ],
    11000: [
        'phase_9/models/cogHQ/SellbotHQ_outer',
        'phase_9/models/cogHQ/SellbotHQ_inner',
    ],
    12000: [
        'phase_10/models/cogHQ/CashbotHQExterior',
    ],
    13000: [
        'phase_11/models/lawbotHQ/LawbotHQExterior',
    ],
    10000: [
        'phase_12/models/bossbotHQ/BossbotHQExterior',
    ],
    500: [
        'phase_5.5/models/estate/estate_house',
    ],
}

class ZonePrefetchManager:
    def __init__(self):
        self._prefetched_zones = set()
        self._cached_models = {}
        self._enabled = ConfigVariableBool('want-async-zone-prefetch', True).value

    def prefetch_zone(self, zoneId, loader=None):
        if not self._enabled:
            return
        base_zone = (zoneId // 1000) * 1000
        if base_zone == 0:
            base_zone = zoneId
        if base_zone in self._prefetched_zones:
            return
        assets = ZONE_ASSETS_MAP.get(base_zone) or ZONE_ASSETS_MAP.get(zoneId)
        if not assets:
            return
        if loader is None:
            try:
                loader = base.loader
            except Exception:
                return
        self._prefetched_zones.add(base_zone)
        notify.info('Prefetching zone %s assets (%d models)...' % (zoneId, len(assets)))
        for path in assets:
            if path in self._cached_models:
                continue
            try:
                if hasattr(loader, 'loadModel'):
                    model = loader.loadModel(path, okMissing=True)
                    if model and not model.isEmpty():
                        self._cached_models[path] = model
                        ModelPool.addModel(path, model.node())
            except Exception as e:
                notify.debug('Prefetch failed for %s: %s' % (path, e))

    def is_zone_prefetched(self, zoneId):
        base_zone = (zoneId // 1000) * 1000
        return (base_zone in self._prefetched_zones) or (zoneId in self._prefetched_zones)

    def clear_cache(self):
        self._cached_models.clear()
        self._prefetched_zones.clear()

zonePrefetchManager = ZonePrefetchManager()
