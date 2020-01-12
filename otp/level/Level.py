from direct.directnotify import DirectNotifyGlobal
import string
from . import LevelConstants
from direct.showbase.PythonUtil import lineInfo, uniqueElements
import types

class Level:
    notify = DirectNotifyGlobal.directNotify.newCategory('Level')

    def __init__(self):
        self.levelSpec = None
        self.initialized = 0
        return

    def initializeLevel(self, levelId, levelSpec, scenarioIndex):
        self.levelId = levelId
        self.levelSpec = levelSpec
        self.scenarioIndex = scenarioIndex
        self.levelSpec.setScenario(self.scenarioIndex)
        if __dev__:
            self.levelSpec.setLevel(self)
        self.entranceId2entity = {}
        self.entId2createCallbacks = {}
        self.createdEntIds = []
        self.nonlocalEntIds = {}
        self.nothingEntIds = {}
        self.entityCreator = self.createEntityCreator()
        self.entType2ids = self.levelSpec.getEntType2ids(self.levelSpec.getAllEntIds())
        for entType in self.entityCreator.getEntityTypes():
            self.entType2ids.setdefault(entType, [])

        self.createAllEntities(priorityTypes=['levelMgr', 'zone', 'propSpinner'])
        self.levelMgrEntity = self.getEntity(LevelConstants.LevelMgrEntId)
        self.uberZoneEntity = self.getEntity(LevelConstants.UberZoneEntId)
        self.initialized = 1

    def isInitialized(self):
        return self.initialized

    def getLevelId(self):
        return self.levelId

    def destroyLevel(self):
        self.destroyAllEntities()
        if self.initialized:
            del self.levelMgrEntity
            del self.uberZoneEntity
            del self.entityCreator
            del self.entId2createCallbacks
            del self.entranceId2entity
            self.levelSpec.destroy()
            del self.levelSpec
        self.initialized = 0
        del self.createdEntIds
        del self.nonlocalEntIds
        del self.nothingEntIds
        if hasattr(self, 'entities'):
            del self.entities
        if hasattr(self, 'levelSpec'):
            self.levelSpec.destroy()
            del self.levelSpec

    def createEntityCreator(self):
        Level.notify.error('concrete Level class must override %s' % lineInfo()[2])

    def createAllEntities(self, priorityTypes = []):
        self.entities = {}
        entTypes = self.entityCreator.getEntityTypes()
        self.onLevelPreCreate()
        for type in priorityTypes:
            self.createAllEntitiesOfType(type)
            entTypes.remove(type)

        for type in entTypes:
            self.createAllEntitiesOfType(type)

        self.onLevelPostCreate()

    def destroyAllEntities(self):
        self.nonlocalEntIds = {}
        self.nothingEntIds = {}
        if not uniqueElements(self.createdEntIds):
            Level.notify.warning('%s: self.createdEntIds is not unique: %s' % (getattr(self, 'doId', None), self.createdEntIds))
        while len(self.createdEntIds) > 0:
            entId = self.createdEntIds.pop()
            entity = self.getEntity(entId)
            if entity is not None:
                Level.notify.debug('destroying %s %s' % (self.getEntityType(entId), entId))
                entity.destroy()
            else:
                Level.notify.error('trying to destroy entity %s, but it is already gone' % entId)

        return

    def createAllEntitiesOfType(self, entType):
        self.onEntityTypePreCreate(entType)
        for entId in self.entType2ids[entType]:
            self.createEntity(entId)

        self.onEntityTypePostCreate(entType)

    def createEntity(self, entId):
        spec = self.levelSpec.getEntitySpec(entId)
        Level.notify.debug('creating %s %s' % (spec['type'], entId))
        entity = self.entityCreator.createEntity(entId)
        announce = False
        if entity == 'nonlocalEnt':
            self.nonlocalEntIds[entId] = None
        elif entity == 'nothing':
            self.nothingEntIds[entId] = None
            announce = True
        else:
            self.createdEntIds.append(entId)
            announce = True
        if announce:
            self.onEntityCreate(entId)
        return entity

    def initializeEntity(self, entity):
        entId = entity.entId
        spec = self.levelSpec.getEntitySpec(entId)
        for key, value in list(spec.items()):
            if key in ('type', 'name', 'comment'):
                continue
            entity.setAttribInit(key, value)

        self.entities[entId] = entity

    def getEntity(self, entId):
        if hasattr(self, 'entities'):
            return self.entities.get(entId)
        else:
            return None
        return None

    def getEntityType(self, entId):
        return self.levelSpec.getEntityType(entId)

    def getEntityZoneEntId(self, entId):
        return self.levelSpec.getEntityZoneEntId(entId)

    def getEntityZoneId(self, entId):
        zoneEntId = self.getEntityZoneEntId(entId)
        if not hasattr(self, 'zoneNum2zoneId'):
            return None
        return self.zoneNum2zoneId.get(zoneEntId)

    def getZoneId(self, zoneEntId):
        return self.zoneNum2zoneId[zoneEntId]

    def getZoneNumFromId(self, zoneId):
        return self.zoneId2zoneNum[zoneId]

    def getParentTokenForEntity(self, entId):
        return entId

    def getLevelPreCreateEvent(self):
        return 'levelPreCreate-%s' % self.levelId

    def getLevelPostCreateEvent(self):
        return 'levelPostCreate-%s' % self.levelId

    def getEntityTypePreCreateEvent(self, entType):
        return 'entityTypePreCreate-%s-%s' % (self.levelId, entType)

    def getEntityTypePostCreateEvent(self, entType):
        return 'entityTypePostCreate-%s-%s' % (self.levelId, entType)

    def getEntityCreateEvent(self, entId):
        return 'entityCreate-%s-%s' % (self.levelId, entId)

    def getEntityOfTypeCreateEvent(self, entType):
        return 'entityOfTypeCreate-%s-%s' % (self.levelId, entType)

    def onLevelPreCreate(self):
        messenger.send(self.getLevelPreCreateEvent())

    def onLevelPostCreate(self):
        messenger.send(self.getLevelPostCreateEvent())

    def onEntityTypePreCreate(self, entType):
        messenger.send(self.getEntityTypePreCreateEvent(entType))

    def onEntityTypePostCreate(self, entType):
        messenger.send(self.getEntityTypePostCreateEvent(entType))

    def onEntityCreate(self, entId):
        messenger.send(self.getEntityCreateEvent(entId))
        messenger.send(self.getEntityOfTypeCreateEvent(self.getEntityType(entId)), [entId])
        if entId in self.entId2createCallbacks:
            for callback in self.entId2createCallbacks[entId]:
                callback()

            del self.entId2createCallbacks[entId]

    def setEntityCreateCallback(self, entId, callback):
        ent = self.getEntity(entId)
        if ent is not None:
            callNow = True
        elif entId in self.nothingEntIds:
            callNow = True
        else:
            callNow = False
        if callNow:
            callback()
        else:
            self.entId2createCallbacks.setdefault(entId, [])
            self.entId2createCallbacks[entId].append(callback)
        return

    def getEntityDestroyEvent(self, entId):
        return 'entityDestroy-%s-%s' % (self.levelId, entId)

    def onEntityDestroy(self, entId):
        messenger.send(self.getEntityDestroyEvent(entId))
        del self.entities[entId]
        if entId in self.createdEntIds:
            self.createdEntIds.remove(entId)

    def handleVisChange(self):
        pass

    if __dev__:

        def getAttribChangeEventName(self):
            return 'attribChange-%s' % self.levelId

        def getInsertEntityEventName(self):
            return 'insertEntity-%s' % self.levelId

        def getRemoveEntityEventName(self):
            return 'removeEntity-%s' % self.levelId

        def handleAttribChange(self, entId, attrib, value, username = None):
            entity = self.getEntity(entId)
            if entity is not None:
                entity.handleAttribChange(attrib, value)
            messenger.send(self.getAttribChangeEventName(), [entId,
             attrib,
             value,
             username])
            return

        def setEntityCreatorUsername(self, entId, editUsername):
            pass

        def handleEntityInsert(self, entId):
            self.entType2ids[self.getEntityType(entId)].append(entId)
            self.createEntity(entId)
            messenger.send(self.getInsertEntityEventName(), [entId])

        def handleEntityRemove(self, entId):
            messenger.send(self.getRemoveEntityEventName(), [entId])
            if entId in self.createdEntIds:
                entity = self.getEntity(entId)
                entity.destroy()
            elif entId in self.nothingEntIds:
                del self.nothingEntIds[entId]
            elif entId in self.nonlocalEntIds:
                del self.nonlocalEntIds[entId]
            self.entType2ids[self.getEntityType(entId)].remove(entId)
