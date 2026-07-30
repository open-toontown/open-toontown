from toontown.hood import ZoneUtil
from toontown.toonbase import ToontownGlobals

class ToontownAccess:

    def canAccess(self, zoneId = None):
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
