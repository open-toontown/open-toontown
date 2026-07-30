from direct.showbase.DirectObject import DirectObject
from direct.showbase.PythonUtil import lineInfo
from direct.directnotify import DirectNotifyGlobal

class Entity(DirectObject):
    notify = DirectNotifyGlobal.directNotify.newCategory('Entity')

    def __init__(self, level = None, entId = None):
        self.initializeEntity(level, entId)

    def initializeEntity(self, level, entId):
        self.level = level
        self.entId = entId
        if self.level is not None and self.entId is not None:
            self.level.initializeEntity(self)
        return

    def __str__(self):
        if hasattr(self, 'level') and self.level:
            return 'ent%s(%s)' % (self.entId, self.level.getEntityType(self.entId))
        elif hasattr(self, 'name'):
            return self.name
        elif hasattr(self, 'entId'):
            return '%s-%s' % (self.__class__.__name__, self.entId)
        else:
            return self.__class__.__name__

    def destroy(self):
        Entity.notify.debug('Entity.destroy() %s' % self.entId)
        if self.level:
            if self.level.isInitialized():
                self.level.onEntityDestroy(self.entId)
            else:
                Entity.notify.warning('Entity %s destroyed after level??' % self.entId)
        self.ignoreAll()
        del self.level
        del self.entId

    def getUniqueName(self, name, entId = None):
        if entId is None:
            entId = self.entId
        return '%s-%s-%s' % (name, self.level.levelId, entId)

    def getParentToken(self):
        return self.level.getParentTokenForEntity(self.entId)

    def getOutputEventName(self, entId = None):
        if entId is None:
            entId = self.entId
        return self.getUniqueName('entityOutput', entId)

    def getZoneEntId(self):
        return self.level.getEntityZoneEntId(self.entId)

    def getZoneEntity(self):
        return self.level.getEntity(self.getZoneEntId())

    def getZoneNode(self):
        return self.getZoneEntity().getNodePath()

    def privGetSetter(self, attrib):
        setFuncName = 'set%s%s' % (attrib[0].upper(), attrib[1:])
        if hasattr(self, setFuncName):
            return getattr(self, setFuncName)
        return None

    def callSetters(self, *attribs):
        self.privCallSetters(0, *attribs)

    def callSettersAndDelete(self, *attribs):
        self.privCallSetters(1, *attribs)

    def privCallSetters(self, doDelete, *attribs):
        for attrib in attribs:
            if hasattr(self, attrib):
                setter = self.privGetSetter(attrib)
                if setter is not None:
                    value = getattr(self, attrib)
                    if doDelete:
                        delattr(self, attrib)
                    setter(value)

        return

    def setAttribInit(self, attrib, value):
        self.__dict__[attrib] = value

    if __dev__:

        def handleAttribChange(self, attrib, value):
            setter = self.privGetSetter(attrib)
            if setter is not None:
                setter(value)
            else:
                self.__dict__[attrib] = value
                self.attribChanged(attrib, value)
            return

        def attribChanged(self, attrib, value):
            pass
