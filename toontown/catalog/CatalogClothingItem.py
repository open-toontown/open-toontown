import CatalogItem
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import TTLocalizer
from toontown.toon import ToonDNA
import random
from direct.showbase import PythonUtil
from direct.gui.DirectGui import *
from pandac.PandaModules import *
CTArticle = 0
CTString = 1
CTBasePrice = 2
CTEmblemPrices = 3
ABoysShirt = 0
AGirlsShirt = 1
AShirt = 2
ABoysShorts = 3
AGirlsShorts = 4
AGirlsSkirt = 5
AShorts = 6
ClothingTypes = {101: (ABoysShirt, 'bss1', 40),
 102: (ABoysShirt, 'bss2', 40),
 103: (ABoysShirt, 'bss3', 40),
 105: (ABoysShirt, 'bss4', 40),
 104: (ABoysShirt, 'bss5', 40),
 106: (ABoysShirt, 'bss6', 40),
 107: (ABoysShirt, 'bss7', 40),
 108: (ABoysShirt, 'bss8', 40),
 109: (ABoysShirt, 'bss9', 40),
 111: (ABoysShirt, 'bss11', 40),
 115: (ABoysShirt, 'bss15', 40),
 116: (ABoysShirt, 'c_ss1', 80),
 117: (ABoysShirt, 'c_ss2', 80),
 118: (ABoysShirt, 'c_bss1', 80),
 119: (ABoysShirt, 'c_bss2', 80),
 120: (ABoysShirt, 'c_ss3', 80),
 121: (ABoysShirt, 'c_bss3', 80),
 122: (ABoysShirt, 'c_bss4', 80),
 123: (ABoysShirt, 'c_ss4', 120),
 124: (ABoysShirt, 'c_ss5', 120),
 125: (AShirt, 'c_ss6', 120),
 126: (AShirt, 'c_ss7', 120),
 127: (AShirt, 'c_ss8', 120),
 128: (AShirt, 'c_ss9', 120),
 129: (AShirt, 'c_ss10', 120),
 130: (AShirt, 'c_ss11', 120),
 131: (ABoysShirt, 'c_ss12', 160),
 201: (AGirlsShirt, 'gss1', 40),
 202: (AGirlsShirt, 'gss2', 40),
 203: (AGirlsShirt, 'gss3', 40),
 205: (AGirlsShirt, 'gss4', 40),
 204: (AGirlsShirt, 'gss5', 40),
 206: (AGirlsShirt, 'gss6', 40),
 207: (AGirlsShirt, 'gss7', 40),
 208: (AGirlsShirt, 'gss8', 40),
 209: (AGirlsShirt, 'gss9', 40),
 211: (AGirlsShirt, 'gss11', 40),
 215: (AGirlsShirt, 'gss15', 40),
 216: (AGirlsShirt, 'c_ss1', 80),
 217: (AGirlsShirt, 'c_ss2', 80),
 218: (AGirlsShirt, 'c_gss1', 80),
 219: (AGirlsShirt, 'c_gss2', 80),
 220: (AGirlsShirt, 'c_ss3', 80),
 221: (AGirlsShirt, 'c_gss3', 80),
 222: (AGirlsShirt, 'c_gss4', 80),
 223: (AGirlsShirt, 'c_gss5', 80),
 224: (AGirlsShirt, 'c_ss4', 120),
 225: (AGirlsShirt, 'c_ss13', 160),
 301: (ABoysShorts, 'bbs1', 50),
 302: (ABoysShorts, 'bbs2', 50),
 303: (ABoysShorts, 'bbs3', 50),
 304: (ABoysShorts, 'bbs4', 50),
 305: (ABoysShorts, 'bbs5', 50),
 308: (ABoysShorts, 'bbs8', 50),
 310: (ABoysShorts, 'c_bs1', 120),
 311: (ABoysShorts, 'c_bs2', 120),
 312: (ABoysShorts, 'c_bs3', 120),
 313: (ABoysShorts, 'c_bs4', 120),
 314: (ABoysShorts, 'c_bs5', 160),
 401: (AGirlsSkirt, 'gsk1', 50),
 403: (AGirlsSkirt, 'gsk3', 50),
 404: (AGirlsSkirt, 'gsk4', 50),
 405: (AGirlsSkirt, 'gsk5', 50),
 407: (AGirlsSkirt, 'gsk7', 50),
 408: (AGirlsSkirt, 'c_gsk1', 100),
 409: (AGirlsSkirt, 'c_gsk2', 100),
 410: (AGirlsSkirt, 'c_gsk3', 100),
 411: (AGirlsSkirt, 'c_gsk4', 120),
 412: (AGirlsSkirt, 'c_gsk5', 120),
 413: (AGirlsSkirt, 'c_gsk6', 120),
 414: (AGirlsSkirt, 'c_gsk7', 160),
 451: (AGirlsShorts, 'gsh1', 50),
 452: (AGirlsShorts, 'gsh2', 50),
 453: (AGirlsShorts, 'gsh3', 50),
 1001: (AShirt, 'hw_ss1', 200),
 1002: (AShirt, 'hw_ss2', 200),
 1100: (AShirt, 'wh_ss1', 200),
 1101: (AShirt, 'wh_ss2', 200),
 1102: (AShirt, 'wh_ss3', 200),
 1103: (AShirt, 'wh_ss4', 200),
 1104: (ABoysShorts, 'wh_bs1', 200),
 1105: (ABoysShorts, 'wh_bs2', 200),
 1106: (ABoysShorts, 'wh_bs3', 200),
 1107: (ABoysShorts, 'wh_bs4', 200),
 1108: (AGirlsSkirt, 'wh_gsk1', 200),
 1109: (AGirlsSkirt, 'wh_gsk2', 200),
 1110: (AGirlsSkirt, 'wh_gsk3', 200),
 1111: (AGirlsSkirt, 'wh_gsk4', 200),
 1112: (AShirt, 'hw_ss5', 200),
 1113: (AShirt, 'hw_ss6', 300),
 1114: (AShirt, 'hw_ss7', 200),
 1115: (AShirt, 'hw_ss8', 200),
 1116: (AShirt, 'hw_ss9', 300),
 1117: (ABoysShorts, 'hw_bs1', 200),
 1118: (ABoysShorts, 'hw_bs2', 300),
 1119: (ABoysShorts, 'hw_bs5', 200),
 1120: (ABoysShorts, 'hw_bs6', 200),
 1121: (ABoysShorts, 'hw_bs7', 300),
 1122: (AGirlsShorts, 'hw_gs1', 200),
 1123: (AGirlsShorts, 'hw_gs2', 300),
 1124: (AGirlsShorts, 'hw_gs5', 200),
 1125: (AGirlsShorts, 'hw_gs6', 200),
 1126: (AGirlsShorts, 'hw_gs7', 300),
 1127: (AGirlsSkirt, 'hw_gsk1', 300),
 1200: (AGirlsShirt, 'vd_ss1', 200),
 1201: (AShirt, 'vd_ss2', 200),
 1202: (ABoysShirt, 'vd_ss3', 200),
 1203: (AGirlsShirt, 'vd_ss4', 200),
 1204: (AGirlsSkirt, 'vd_gs1', 200),
 1205: (ABoysShorts, 'vd_bs1', 200),
 1206: (AShirt, 'vd_ss5', 200),
 1207: (AShirt, 'vd_ss6', 200),
 1208: (ABoysShorts, 'vd_bs2', 200),
 1209: (ABoysShorts, 'vd_bs3', 200),
 1210: (AGirlsSkirt, 'vd_gs2', 200),
 1211: (AGirlsSkirt, 'vd_gs3', 200),
 1212: (AShirt, 'vd_ss7', 200),
 1300: (AShirt, 'sd_ss1', 200),
 1301: (AShirt, 'sd_ss2', 225),
 1302: (AGirlsShorts, 'sd_gs1', 200),
 1303: (ABoysShorts, 'sd_bs1', 200),
 1304: (AShirt, 'sd_ss3', 25),
 1305: (ABoysShorts, 'sd_bs2', 25),
 1306: (AGirlsSkirt, 'sd_gs2', 25),
 1400: (AShirt, 'tc_ss1', 200),
 1401: (AShirt, 'tc_ss2', 200),
 1402: (AShirt, 'tc_ss3', 200),
 1403: (AShirt, 'tc_ss4', 200),
 1404: (AShirt, 'tc_ss5', 200),
 1405: (AShirt, 'tc_ss6', 200),
 1406: (AShirt, 'tc_ss7', 200),
 1500: (AShirt, 'j4_ss1', 200),
 1501: (AShirt, 'j4_ss2', 200),
 1502: (ABoysShorts, 'j4_bs1', 200),
 1503: (AGirlsSkirt, 'j4_gs1', 200),
 1600: (AShirt, 'pj_ss1', 500),
 1601: (AShirt, 'pj_ss2', 500),
 1602: (AShirt, 'pj_ss3', 500),
 1603: (ABoysShorts, 'pj_bs1', 500),
 1604: (ABoysShorts, 'pj_bs2', 500),
 1605: (ABoysShorts, 'pj_bs3', 500),
 1606: (AGirlsShorts, 'pj_gs1', 500),
 1607: (AGirlsShorts, 'pj_gs2', 500),
 1608: (AGirlsShorts, 'pj_gs3', 500),
 1700: (AShirt, 'sa_ss1', 200),
 1701: (AShirt, 'sa_ss2', 200),
 1702: (AShirt, 'sa_ss3', 200),
 1703: (AShirt, 'sa_ss4', 200),
 1704: (AShirt, 'sa_ss5', 200),
 1705: (AShirt, 'sa_ss6', 200),
 1706: (AShirt, 'sa_ss7', 200),
 1707: (AShirt, 'sa_ss8', 200),
 1708: (AShirt, 'sa_ss9', 200),
 1709: (AShirt, 'sa_ss10', 200),
 1710: (AShirt, 'sa_ss11', 200),
 1711: (ABoysShorts, 'sa_bs1', 200),
 1712: (ABoysShorts, 'sa_bs2', 200),
 1713: (ABoysShorts, 'sa_bs3', 200),
 1714: (ABoysShorts, 'sa_bs4', 200),
 1715: (ABoysShorts, 'sa_bs5', 200),
 1716: (AGirlsSkirt, 'sa_gs1', 200),
 1717: (AGirlsSkirt, 'sa_gs2', 200),
 1718: (AGirlsSkirt, 'sa_gs3', 200),
 1719: (AGirlsSkirt, 'sa_gs4', 200),
 1720: (AGirlsSkirt, 'sa_gs5', 200),
 1721: (AShirt, 'sa_ss12', 200),
 1722: (AShirt, 'sa_ss13', 200),
 1723: (AShirt, 'sa_ss14', 250),
 1724: (AShirt, 'sa_ss15', 250),
 1725: (AShirt, 'sa_ss16', 200),
 1726: (AShirt, 'sa_ss17', 200),
 1727: (AShirt, 'sa_ss18', 200),
 1728: (AShirt, 'sa_ss19', 200),
 1729: (AShirt, 'sa_ss20', 200),
 1730: (AShirt, 'sa_ss21', 200),
 1731: (AShirt, 'sa_ss22', 200),
 1732: (AShirt, 'sa_ss23', 200),
 1733: (ABoysShorts, 'sa_bs6', 200),
 1734: (ABoysShorts, 'sa_bs7', 250),
 1735: (ABoysShorts, 'sa_bs8', 250),
 1736: (ABoysShorts, 'sa_bs9', 200),
 1737: (ABoysShorts, 'sa_bs10', 200),
 1738: (AGirlsSkirt, 'sa_gs6', 200),
 1739: (AGirlsSkirt, 'sa_gs7', 250),
 1740: (AGirlsSkirt, 'sa_gs8', 250),
 1741: (AGirlsSkirt, 'sa_gs9', 200),
 1742: (AGirlsSkirt, 'sa_gs10', 200),
 1743: (AShirt, 'sa_ss24', 250),
 1744: (AShirt, 'sa_ss25', 250),
 1745: (ABoysShorts, 'sa_bs11', 250),
 1746: (ABoysShorts, 'sa_bs12', 250),
 1747: (AGirlsSkirt, 'sa_gs11', 250),
 1748: (AGirlsSkirt, 'sa_gs12', 250),
 1749: (AShirt, 'sil_1', 1),
 1750: (AShirt, 'sil_2', 1),
 1751: (AShirt, 'sil_3', 1),
 1752: (AShirt, 'sil_4', 5000),
 1753: (AShirt, 'sil_5', 5000),
 1754: (AShirt, 'sil_6', 1),
 1755: (ABoysShorts, 'sil_bs1', 1),
 1756: (AGirlsShorts, 'sil_gs1', 1),
 1757: (AShirt, 'sil_7', 20),
 1758: (AShirt, 'sil_8', 20),
 1759: (AShirt,
        'emb_us1',
        0,
        (20, 5)),
 1760: (AShirt,
        'emb_us2',
        234,
        (0, 7)),
 1761: (AShirt,
        'emb_us3',
        345,
        (8, 0)),
 1762: (AShirt, 'sa_ss26', 5000),
 1763: (AShirt, 'sb_1', 20),
 1764: (AShirt, 'sa_ss27', 5000),
 1765: (AShirt, 'sa_ss28', 5000),
 1766: (ABoysShorts, 'sa_bs13', 5000),
 1767: (AGirlsShorts, 'sa_gs13', 5000),
 1768: (AShirt, 'jb_1', 20),
 1769: (AShirt, 'jb_2', 20),
 1770: (AShirt, 'hw_ss3', 250),
 1771: (AShirt, 'hw_ss4', 250),
 1772: (ABoysShorts, 'hw_bs3', 250),
 1773: (AGirlsShorts, 'hw_gs3', 250),
 1774: (ABoysShorts, 'hw_bs4', 250),
 1775: (AGirlsShorts, 'hw_gs4', 250),
 1776: (AShirt, 'ugcms', 15000),
 1777: (AShirt, 'lb_1', 20),
 1778: (AShirt, 'sa_ss29', 5000),
 1779: (AShirt, 'sa_ss30', 5000),
 1780: (ABoysShorts, 'sa_bs14', 5000),
 1781: (AGirlsShorts, 'sa_gs14', 5000),
 1782: (AShirt, 'sa_ss31', 5000),
 1783: (ABoysShorts, 'sa_bs15', 5000),
 1784: (AGirlsSkirt, 'sa_gs15', 5000),
 1785: (AShirt, 'sa_ss32', 5000),
 1786: (AShirt, 'sa_ss33', 5000),
 1787: (AShirt, 'sa_ss34', 5000),
 1788: (AShirt, 'sa_ss35', 5000),
 1789: (AShirt, 'sa_ss36', 5000),
 1790: (AShirt, 'sa_ss37', 5000),
 1791: (ABoysShorts, 'sa_bs16', 5000),
 1792: (ABoysShorts, 'sa_bs17', 5000),
 1793: (AGirlsSkirt, 'sa_gs16', 5000),
 1794: (AGirlsSkirt, 'sa_gs17', 5000),
 1795: (AShirt, 'sa_ss38', 5000),
 1796: (AShirt, 'sa_ss39', 5000),
 1797: (ABoysShorts, 'sa_bs18', 5000),
 1798: (AGirlsSkirt, 'sa_gs18', 5000),
 1799: (AShirt, 'sa_ss40', 5000),
 1800: (AShirt, 'sa_ss41', 5000),
 1801: (AShirt, 'sa_ss42', 250),
 1802: (AGirlsShirt, 'sa_ss43', 250),
 1803: (AShirt, 'sa_ss44', 5000),
 1804: (AShirt, 'sa_ss45', 5000),
 1805: (AShirt, 'sa_ss46', 5000),
 1806: (AShirt, 'sa_ss47', 5000),
 1807: (AShirt, 'sa_ss48', 5000),
 1808: (AShirt, 'sa_ss49', 5000),
 1809: (AShirt, 'sa_ss50', 5000),
 1810: (AShirt, 'sa_ss51', 5000),
 1811: (AShirt, 'sa_ss52', 5000),
 1812: (AShirt, 'sa_ss53', 5000),
 1813: (AShirt, 'sa_ss54', 5000),
 1814: (ABoysShorts, 'sa_bs19', 5000),
 1815: (ABoysShorts, 'sa_bs20', 5000),
 1816: (ABoysShorts, 'sa_bs21', 5000),
 1817: (AGirlsSkirt, 'sa_gs19', 5000),
 1818: (AGirlsSkirt, 'sa_gs20', 5000),
 1819: (AGirlsSkirt, 'sa_gs21', 5000),
 1820: (AShirt, 'sa_ss55', 5000)}
LoyaltyClothingItems = (1600,
 1601,
 1602,
 1603,
 1604,
 1605,
 1606,
 1607,
 1608)

class CatalogClothingItem(CatalogItem.CatalogItem):

    def makeNewItem(self, clothingType, colorIndex, loyaltyDays = 0):
        self.clothingType = clothingType
        self.colorIndex = colorIndex
        self.loyaltyDays = loyaltyDays
        CatalogItem.CatalogItem.makeNewItem(self)

    def storedInCloset(self):
        return 1

    def notOfferedTo(self, avatar):
        article = ClothingTypes[self.clothingType][CTArticle]
        if article == AShirt or article == AShorts:
            return 0
        forBoys = (article == ABoysShirt or article == ABoysShorts)
        if avatar.getStyle().getGender() == 'm':
            return not forBoys
        else:
            return forBoys

    def forBoysOnly(self):
        article = ClothingTypes[self.clothingType][CTArticle]
        if article == ABoysShirt or article == ABoysShorts:
            return 1
        else:
            return 0

    def forGirlsOnly(self):
        article = ClothingTypes[self.clothingType][CTArticle]
        if article == AGirlsShirt or article == AGirlsSkirt or article == AGirlsShorts:
            return 1
        else:
            return 0

    def getPurchaseLimit(self):
        return 1

    def reachedPurchaseLimit(self, avatar):
        if avatar.onOrder.count(self) != 0:
            return 1
        if avatar.onGiftOrder.count(self) != 0:
            return 1
        if avatar.mailboxContents.count(self) != 0:
            return 1
        if self in avatar.awardMailboxContents or self in avatar.onAwardOrder:
            return 1
        str = ClothingTypes[self.clothingType][CTString]
        dna = avatar.getStyle()
        if self.isShirt():
            defn = ToonDNA.ShirtStyles[str]
            if dna.topTex == defn[0] and dna.topTexColor == defn[2][self.colorIndex][0] and dna.sleeveTex == defn[1] and dna.sleeveTexColor == defn[2][self.colorIndex][1]:
                return 1
            l = avatar.clothesTopsList
            for i in range(0, len(l), 4):
                if l[i] == defn[0] and l[i + 1] == defn[2][self.colorIndex][0] and l[i + 2] == defn[1] and l[i + 3] == defn[2][self.colorIndex][1]:
                    return 1

        else:
            defn = ToonDNA.BottomStyles[str]
            if dna.botTex == defn[0] and dna.botTexColor == defn[1][self.colorIndex]:
                return 1
            l = avatar.clothesBottomsList
            for i in range(0, len(l), 2):
                if l[i] == defn[0] and l[i + 1] == defn[1][self.colorIndex]:
                    return 1

        return 0

    def getTypeName(self):
        return TTLocalizer.ClothingTypeName

    def getName(self):
        typeName = TTLocalizer.ClothingTypeNames.get(self.clothingType, 0)
        if typeName:
            return typeName
        else:
            article = ClothingTypes[self.clothingType][CTArticle]
            return TTLocalizer.ClothingArticleNames[article]

    def recordPurchase(self, avatar, optional):
        if avatar.isClosetFull():
            return ToontownGlobals.P_NoRoomForItem
        str = ClothingTypes[self.clothingType][CTString]
        dna = avatar.getStyle()
        if self.isShirt():
            added = avatar.addToClothesTopsList(dna.topTex, dna.topTexColor, dna.sleeveTex, dna.sleeveTexColor)
            if added:
                avatar.b_setClothesTopsList(avatar.getClothesTopsList())
                self.notify.info('Avatar %s put shirt %d,%d,%d,%d in closet.' % (avatar.doId,
                 dna.topTex,
                 dna.topTexColor,
                 dna.sleeveTex,
                 dna.sleeveTexColor))
            else:
                self.notify.warning('Avatar %s %s lost current shirt; closet full.' % (avatar.doId, dna.asTuple()))
            defn = ToonDNA.ShirtStyles[str]
            dna.topTex = defn[0]
            dna.topTexColor = defn[2][self.colorIndex][0]
            dna.sleeveTex = defn[1]
            dna.sleeveTexColor = defn[2][self.colorIndex][1]
        else:
            added = avatar.addToClothesBottomsList(dna.botTex, dna.botTexColor)
            if added:
                avatar.b_setClothesBottomsList(avatar.getClothesBottomsList())
                self.notify.info('Avatar %s put bottoms %d,%d in closet.' % (avatar.doId, dna.botTex, dna.botTexColor))
            else:
                self.notify.warning('Avatar %s %s lost current bottoms; closet full.' % (avatar.doId, dna.asTuple()))
            defn = ToonDNA.BottomStyles[str]
            dna.botTex = defn[0]
            dna.botTexColor = defn[1][self.colorIndex]
        if dna.getGender() == 'f':
            try:
                bottomPair = ToonDNA.GirlBottoms[dna.botTex]
            except:
                bottomPair = ToonDNA.GirlBottoms[0]

            if dna.torso[1] == 's' and bottomPair[1] == ToonDNA.SKIRT:
                dna.torso = dna.torso[0] + 'd'
            elif dna.torso[1] == 'd' and bottomPair[1] == ToonDNA.SHORTS:
                dna.torso = dna.torso[0] + 's'
        avatar.b_setDNAString(dna.makeNetString())
        avatar.d_catalogGenClothes()
        return ToontownGlobals.P_ItemAvailable

    def getDeliveryTime(self):
        return 60

    def getPicture(self, avatar):
        from toontown.toon import Toon
        self.hasPicture = True
        dna = ToonDNA.ToonDNA(type='t', dna=avatar.style)
        str = ClothingTypes[self.clothingType][CTString]
        if self.isShirt():
            defn = ToonDNA.ShirtStyles[str]
            dna.topTex = defn[0]
            dna.topTexColor = defn[2][self.colorIndex][0]
            dna.sleeveTex = defn[1]
            dna.sleeveTexColor = defn[2][self.colorIndex][1]
            pieceNames = ('**/1000/**/torso-top', '**/1000/**/sleeves')
        else:
            defn = ToonDNA.BottomStyles[str]
            dna.botTex = defn[0]
            dna.botTexColor = defn[1][self.colorIndex]
            pieceNames = ('**/1000/**/torso-bot',)
        toon = Toon.Toon()
        toon.setDNA(dna)
        model = NodePath('clothing')
        for name in pieceNames:
            for piece in toon.findAllMatches(name):
                piece.wrtReparentTo(model)

        model.setH(180)
        toon.delete()
        return self.makeFrameModel(model)

    def requestPurchase(self, phone, callback):
        from toontown.toontowngui import TTDialog
        avatar = base.localAvatar
        clothesOnOrder = 0
        for item in avatar.onOrder + avatar.mailboxContents:
            if item.storedInCloset():
                clothesOnOrder += 1

        if avatar.isClosetFull(clothesOnOrder):
            self.requestPurchaseCleanup()
            buttonCallback = PythonUtil.Functor(self.__handleFullPurchaseDialog, phone, callback)
            self.dialog = TTDialog.TTDialog(style=TTDialog.YesNo, text=TTLocalizer.CatalogPurchaseClosetFull, text_wordwrap=15, command=buttonCallback)
            self.dialog.show()
        else:
            CatalogItem.CatalogItem.requestPurchase(self, phone, callback)

    def requestPurchaseCleanup(self):
        if hasattr(self, 'dialog'):
            self.dialog.cleanup()
            del self.dialog

    def __handleFullPurchaseDialog(self, phone, callback, buttonValue):
        from toontown.toontowngui import TTDialog
        self.requestPurchaseCleanup()
        if buttonValue == DGG.DIALOG_OK:
            CatalogItem.CatalogItem.requestPurchase(self, phone, callback)
        else:
            callback(ToontownGlobals.P_UserCancelled, self)

    def getAcceptItemErrorText(self, retcode):
        if retcode == ToontownGlobals.P_ItemAvailable:
            if self.isShirt():
                return TTLocalizer.CatalogAcceptShirt
            elif self.isSkirt():
                return TTLocalizer.CatalogAcceptSkirt
            else:
                return TTLocalizer.CatalogAcceptShorts
        elif retcode == ToontownGlobals.P_NoRoomForItem:
            return TTLocalizer.CatalogAcceptClosetFull
        return CatalogItem.CatalogItem.getAcceptItemErrorText(self, retcode)

    def getColorChoices(self):
        str = ClothingTypes[self.clothingType][CTString]
        if self.isShirt():
            return ToonDNA.ShirtStyles[str][2]
        else:
            return ToonDNA.BottomStyles[str][1]

    def isShirt(self):
        article = ClothingTypes[self.clothingType][CTArticle]
        return article < ABoysShorts

    def isSkirt(self):
        article = ClothingTypes[self.clothingType][CTArticle]
        return article == AGirlsSkirt

    def output(self, store = -1):
        return 'CatalogClothingItem(%s, %s%s)' % (self.clothingType, self.colorIndex, self.formatOptionalData(store))

    def getFilename(self):
        str = ClothingTypes[self.clothingType][CTString]
        if self.isShirt():
            defn = ToonDNA.ShirtStyles[str]
            topTex = defn[0]
            return ToonDNA.Shirts[topTex]
        else:
            defn = ToonDNA.BottomStyles[str]
            botTex = defn[0]
            article = ClothingTypes[self.clothingType][CTArticle]
            if article == ABoysShorts:
                return ToonDNA.BoyShorts[botTex]
            else:
                return ToonDNA.GirlBottoms[botTex][0]

    def getColor(self):
        str = ClothingTypes[self.clothingType][CTString]
        if self.isShirt():
            defn = ToonDNA.ShirtStyles[str]
            topTexColor = defn[2][self.colorIndex][0]
            return ToonDNA.ClothesColors[topTexColor]
        else:
            defn = ToonDNA.BottomStyles[str]
            botTexColor = defn[1][self.colorIndex]
            return ToonDNA.ClothesColors[botTexColor]

    def compareTo(self, other):
        if self.clothingType != other.clothingType:
            return self.clothingType - other.clothingType
        return self.colorIndex - other.colorIndex

    def getHashContents(self):
        return (self.clothingType, self.colorIndex)

    def getBasePrice(self):
        return ClothingTypes[self.clothingType][CTBasePrice]

    def getEmblemPrices(self):
        result = ()
        info = ClothingTypes[self.clothingType]
        if CTEmblemPrices <= len(info) - 1:
            result = info[CTEmblemPrices]
        return result

    def decodeDatagram(self, di, versionNumber, store):
        CatalogItem.CatalogItem.decodeDatagram(self, di, versionNumber, store)
        self.clothingType = di.getUint16()
        self.colorIndex = di.getUint8()
        if versionNumber >= 6:
            self.loyaltyDays = di.getUint16()
        else:
            self.loyaltyDays = 0
        str = ClothingTypes[self.clothingType][CTString]
        if self.isShirt():
            color = ToonDNA.ShirtStyles[str][2][self.colorIndex]
        else:
            color = ToonDNA.BottomStyles[str][1][self.colorIndex]

    def encodeDatagram(self, dg, store):
        CatalogItem.CatalogItem.encodeDatagram(self, dg, store)
        dg.addUint16(self.clothingType)
        dg.addUint8(self.colorIndex)
        dg.addUint16(self.loyaltyDays)

    def isGift(self):
        if self.getEmblemPrices():
            return 0
        if self.loyaltyRequirement() > 0:
            return 0
        elif self.clothingType in LoyaltyClothingItems:
            return 0
        else:
            return 1


def getAllClothes(*clothingTypes):
    list = []
    for clothingType in clothingTypes:
        base = CatalogClothingItem(clothingType, 0)
        list.append(base)
        for n in range(1, len(base.getColorChoices())):
            list.append(CatalogClothingItem(clothingType, n))

    return list
