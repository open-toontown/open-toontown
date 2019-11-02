from CatalogFurnitureItem import *
FTAnimRate = 6
AnimatedFurnitureItemKeys = (10020, 270, 990, 460, 470, 480, 490, 491, 492)

class CatalogAnimatedFurnitureItem(CatalogFurnitureItem):

    def loadModel(self):
        model = CatalogFurnitureItem.loadModel(self)
        self.setAnimRate(model, self.getAnimRate())
        return model

    def getAnimRate(self):
        item = FurnitureTypes[self.furnitureType]
        if FTAnimRate < len(item):
            animRate = item[FTAnimRate]
            if not animRate == None:
                return item[FTAnimRate]
            else:
                return 1
        else:
            return 1
        return

    def setAnimRate(self, model, rate):
        seqNodes = model.findAllMatches('**/seqNode*')
        for seqNode in seqNodes:
            seqNode.node().setPlayRate(rate)
