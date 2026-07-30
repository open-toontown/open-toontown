from . import EditMgrBase
if __dev__:
    from direct.showbase.PythonUtil import list2dict
    from . import EditorGlobals

class EditMgrAI(EditMgrBase.EditMgrBase):
    if __dev__:

        def setRequestNewEntity(self, data):
            spec = self.level.levelSpec
            entIds = spec.getAllEntIds()
            entIdDict = list2dict(entIds)
            allocRange = EditorGlobals.getEntIdAllocRange()
            if not hasattr(self, 'lastAllocatedEntId'):
                self.lastAllocatedEntId = allocRange[0]
            idChosen = 0
            while not idChosen:
                for id in range(self.lastAllocatedEntId, allocRange[1]):
                    print(id)
                    if id not in entIdDict:
                        idChosen = 1
                        break
                else:
                    if self.lastAllocatedEntId != allocRange[0]:
                        self.lastAllocatedEntId = allocRange[0]
                    else:
                        self.notify.error('out of entIds')

            data.update({'entId': id})
            self.lastAllocatedEntId = id
            self.level.setAttribChange(self.entId, 'insertEntity', data)
            self.level.levelSpec.doSetAttrib(self.entId, 'requestNewEntity', None)
            return

        def getSpecSaveEvent(self):
            return 'requestSave-%s' % self.level.levelId

        def setRequestSave(self, data):
            messenger.send(self.getSpecSaveEvent())
            self.level.levelSpec.doSetAttrib(self.entId, 'requestSave', None)
            return
