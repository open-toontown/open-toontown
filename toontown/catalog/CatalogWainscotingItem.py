from CatalogSurfaceItem import *
WSTTextureName = 0
WSTColor = 1
WSTBasePrice = 2
WainscotingTypes = {1000: ('phase_3.5/maps/wall_paper_b3.jpg', CTFlatColorDark, 200),
 1010: ('phase_5.5/maps/wall_paper_b4_greyscale.jpg', CTBasicWoodColorOnWhite, 200),
 1020: ('phase_5.5/maps/wainscotings_neutral.jpg', CTBasicWoodColorOnWhite, 200),
 1030: ('phase_3.5/maps/wall_paper_b3.jpg', CTValentinesColors, 200),
 1040: ('phase_3.5/maps/wall_paper_b3.jpg', CTUnderwaterColors, 200)}

class CatalogWainscotingItem(CatalogSurfaceItem):

    def makeNewItem(self, patternIndex, colorIndex):
        self.patternIndex = patternIndex
        self.colorIndex = colorIndex
        CatalogSurfaceItem.makeNewItem(self)

    def getTypeName(self):
        return TTLocalizer.SurfaceNames[STWainscoting]

    def getName(self):
        name = TTLocalizer.WainscotingNames.get(self.patternIndex)
        if name:
            return name
        return self.getTypeName()

    def getSurfaceType(self):
        return STWainscoting

    def getPicture(self, avatar):
        frame = self.makeFrame()
        sample = loader.loadModel('phase_5.5/models/estate/wallpaper_sample')
        a = sample.find('**/a')
        b = sample.find('**/b')
        c = sample.find('**/c')
        a.hide()
        b.hide()
        c.setTexture(self.loadTexture(), 1)
        c.setColorScale(*self.getColor())
        sample.reparentTo(frame)
        self.hasPicture = True
        return (frame, None)

    def output(self, store = -1):
        return 'CatalogWainscotingItem(%s, %s%s)' % (self.patternIndex, self.colorIndex, self.formatOptionalData(store))

    def getFilename(self):
        return WainscotingTypes[self.patternIndex][WSTTextureName]

    def compareTo(self, other):
        if self.patternIndex != other.patternIndex:
            return self.patternIndex - other.patternIndex
        return self.colorIndex - other.colorIndex

    def getHashContents(self):
        return (self.patternIndex, self.colorIndex)

    def getBasePrice(self):
        return WainscotingTypes[self.patternIndex][WSTBasePrice]

    def loadTexture(self):
        from pandac.PandaModules import Texture
        filename = WainscotingTypes[self.patternIndex][WSTTextureName]
        texture = loader.loadTexture(filename)
        texture.setMinfilter(Texture.FTLinearMipmapLinear)
        texture.setMagfilter(Texture.FTLinear)
        return texture

    def getColor(self):
        if self.colorIndex == None:
            colorIndex = 0
        else:
            colorIndex = self.colorIndex
        colors = WainscotingTypes[self.patternIndex][WSTColor]
        if colors:
            if colorIndex < len(colors):
                return colors[colorIndex]
            else:
                print 'Warning: colorIndex not in colors. Returning white.'
                return CT_WHITE
        else:
            return CT_WHITE
        return

    def decodeDatagram(self, di, versionNumber, store):
        CatalogAtticItem.CatalogAtticItem.decodeDatagram(self, di, versionNumber, store)
        if versionNumber < 3:
            self.patternIndex = di.getUint8()
        else:
            self.patternIndex = di.getUint16()
        self.colorIndex = di.getUint8()
        wtype = WainscotingTypes[self.patternIndex]

    def encodeDatagram(self, dg, store):
        CatalogAtticItem.CatalogAtticItem.encodeDatagram(self, dg, store)
        dg.addUint16(self.patternIndex)
        dg.addUint8(self.colorIndex)


def getWainscotings(*indexList):
    list = []
    for index in indexList:
        list.append(CatalogWainscotingItem(index))

    return list


def getAllWainscotings(*indexList):
    list = []
    for index in indexList:
        colors = WainscotingTypes[index][WSTColor]
        if colors:
            for n in range(len(colors)):
                list.append(CatalogWainscotingItem(index, n))

        else:
            list.append(CatalogWainscotingItem(index, 0))

    return list


def getWainscotingRange(fromIndex, toIndex, *otherRanges):
    list = []
    froms = [fromIndex]
    tos = [toIndex]
    i = 0
    while i < len(otherRanges):
        froms.append(otherRanges[i])
        tos.append(otherRanges[i + 1])
        i += 2

    for patternIndex in WainscotingTypes.keys():
        for fromIndex, toIndex in zip(froms, tos):
            if patternIndex >= fromIndex and patternIndex <= toIndex:
                colors = WainscotingTypes[patternIndex][WSTColor]
                if colors:
                    for n in range(len(colors)):
                        list.append(CatalogWainscotingItem(patternIndex, n))

                else:
                    list.append(CatalogWainscotingItem(patternIndex, 0))

    return list
