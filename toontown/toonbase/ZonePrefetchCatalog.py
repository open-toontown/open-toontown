"""
Curated model paths for background async prefetch during quiet-zone transitions.

Paths are best-effort; the loader uses okMissing so missing assets are skipped.
Profile real zone loads and append heavy models that still hit the disk here.
"""

from toontown.hood import ZoneUtil
from toontown.toonbase import ToontownGlobals as TG


def _uniq(seq):
    out = []
    seen = set()
    for p in seq:
        if not p or p in seen:
            continue
        seen.add(p)
        out.append(p)
    return out


def paths_for_quiet_zone(request_status):
    if not request_status:
        return []
    loader = request_status.get('loader')
    hood_id = int(request_status.get('hoodId', 0) or 0)
    try:
        cz = ZoneUtil.getCanonicalZoneId(hood_id)
    except Exception:
        cz = hood_id

    core = [
        'phase_3.5/models/gui/inventory_gui',
        'phase_3/models/gui/dialog_box_gui',
        'phase_3/models/props/drop_shadow',
        'phase_3/models/gui/chat_button_gui',
    ]

    extra = []
    if loader == 'safeZoneLoader':
        if cz == TG.ToontownCentral:
            extra.append('phase_4/models/modules/trolley_station_TT')
        elif cz == TG.GoofySpeedway:
            extra.append('phase_6/models/golf/golf_hub2')
        elif cz == TG.OutdoorZone:
            extra.append('phase_6/models/golf/golf_geyser_model')
    elif loader == 'townLoader':
        extra.append('phase_4/models/modules/trolley_station_TT')

    return _uniq(core + extra)
