from toontown.hood import ZoneUtil
from toontown.toonbase import ToontownGlobals
import builtins

class ToontownAccess:

    def canAccess(self, zoneId = None):
        # Don't restrict travel for avatars that haven't acknowledged/finished the tutorial yet.
        # (Works for existing toons that got stuck with tutorialAck == 0.)
        base = getattr(builtins, 'base', None)
        if base and getattr(base, 'localAvatar', None) and getattr(base.localAvatar, 'tutorialAck', 1) == 0:
            return True
        if base.cr.isPaid():
            return True
        allowed = False
        allowedZones = [ToontownGlobals.ToontownCentral,
         ToontownGlobals.MyEstate,
         ToontownGlobals.GoofySpeedway,
         ToontownGlobals.Tutorial]
        specialZones = [ToontownGlobals.SellbotLobby]
        if hasattr(base.cr, 'newsManager') and base.cr.newsManager:
            holidayIds = base.cr.newsManager.getHolidayIdList()
            if ToontownGlobals.SELLBOT_NERF_HOLIDAY in holidayIds:
                specialZones.append(ToontownGlobals.SellbotHQ)
        place = base.cr.playGame.getPlace()
        if zoneId:
            myHoodId = ZoneUtil.getCanonicalHoodId(zoneId)
        else:
            myHoodId = ZoneUtil.getCanonicalHoodId(place.zoneId)
        if hasattr(place, 'id'):
            myHoodId = place.id
        if myHoodId in allowedZones:
            allowed = True
        elif zoneId and zoneId in specialZones:
            allowed = True
        return allowed
