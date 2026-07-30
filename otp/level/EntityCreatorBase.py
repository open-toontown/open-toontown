from direct.directnotify import DirectNotifyGlobal

class EntityCreatorBase:
    notify = DirectNotifyGlobal.directNotify.newCategory('EntityCreator')

    def __init__(self, level):
        self.level = level
        self.entType2Ctor = {}

    def createEntity(self, entId):
        entType = self.level.getEntityType(entId)
        if entType not in self.entType2Ctor:
            self.notify.error('unknown entity type: %s (ent%s)' % (entType, entId))
        ent = self.doCreateEntity(self.entType2Ctor[entType], entId)
        return ent

    def getEntityTypes(self):
        return list(self.entType2Ctor.keys())

    def privRegisterType(self, entType, ctor):
        if entType in self.entType2Ctor:
            self.notify.debug('replacing %s ctor %s with %s' % (entType, self.entType2Ctor[entType], ctor))
        self.entType2Ctor[entType] = ctor

    def privRegisterTypes(self, type2ctor):
        for entType, ctor in list(type2ctor.items()):
            self.privRegisterType(entType, ctor)
