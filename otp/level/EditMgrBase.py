import Entity
from direct.directnotify import DirectNotifyGlobal

class EditMgrBase(Entity.Entity):
    notify = DirectNotifyGlobal.directNotify.newCategory('EditMgr')

    def __init__(self, level, entId):
        Entity.Entity.__init__(self, level, entId)

    def destroy(self):
        Entity.Entity.destroy(self)
        self.ignoreAll()

    if __dev__:

        def setInsertEntity(self, data):
            self.level.setEntityCreatorUsername(data['entId'], data['username'])
            self.level.levelSpec.insertEntity(data['entId'], data['entType'], data['parentEntId'])
            self.level.levelSpec.doSetAttrib(self.entId, 'insertEntity', None)
            return

        def setRemoveEntity(self, data):
            self.level.levelSpec.removeEntity(data['entId'])
            self.level.levelSpec.doSetAttrib(self.entId, 'removeEntity', None)
            return
