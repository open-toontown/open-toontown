from pandac.PandaModules import *
from .ToontownAIMsgTypes import *
from direct.directnotify.DirectNotifyGlobal import *
from toontown.toon import DistributedToonAI
from direct.distributed.PyDatagram import PyDatagram
from direct.distributed.PyDatagramIterator import PyDatagramIterator
import types

class DatabaseObject:
    notify = directNotify.newCategory('DatabaseObject')
    notify.setInfo(0)

    def __init__(self, air, doId = None, doneEvent = 'DatabaseObject'):
        self.air = air
        self.doId = doId
        self.values = {}
        self.gotDataHandler = None
        self.doneEvent = doneEvent
        return

    def readToon(self, fields = None):
        toon = DistributedToonAI.DistributedToonAI(self.air)
        self.readObject(toon, fields)
        return toon

    if simbase.wantPets:

        def readPet(self):
            from toontown.pets import DistributedPetAI
            pet = DistributedPetAI.DistributedPetAI(self.air)
            self.readObject(pet, None)
            return pet

        def readPetProxy(self):
            from toontown.pets import DistributedPetProxyAI
            petProxy = DistributedPetProxyAI.DistributedPetProxyAI(self.air)
            self.readObject(petProxy, None)
            return petProxy

    def readObject(self, do, fields = None):
        self.do = do
        className = do.__class__.__name__
        self.dclass = self.air.dclassesByName[className]
        self.gotDataHandler = self.fillin
        if fields != None:
            self.getFields(fields)
        else:
            self.getFields(self.getDatabaseFields(self.dclass))
        return

    def storeObject(self, do, fields = None):
        self.do = do
        className = do.__class__.__name__
        self.dclass = self.air.dclassesByName[className]
        if fields != None:
            self.reload(self.do, self.dclass, fields)
        else:
            dbFields = self.getDatabaseFields(self.dclass)
            self.reload(self.do, self.dclass, dbFields)
        values = self.values
        if fields != None:
            values = {}
            for field in fields:
                if field in self.values:
                    values[field] = self.values[field]
                else:
                    self.notify.warning('Field %s not defined.' % field)

        self.setFields(values)
        return

    def getFields(self, fields):
        context = self.air.dbObjContext
        self.air.dbObjContext += 1
        self.air.dbObjMap[context] = self
        dg = PyDatagram()
        dg.addServerHeader(DBSERVER_ID, self.air.ourChannel, DBSERVER_GET_STORED_VALUES)
        dg.addUint32(context)
        dg.addUint32(self.doId)
        dg.addUint16(len(fields))
        for f in fields:
            dg.addString(f)

        self.air.send(dg)

    def getFieldsResponse(self, di):
        objId = di.getUint32()
        if objId != self.doId:
            self.notify.warning('Unexpected doId %d' % objId)
            return
        count = di.getUint16()
        fields = []
        for i in range(count):
            name = di.getString()
            fields.append(name)

        retCode = di.getUint8()
        if retCode != 0:
            self.notify.warning('Failed to retrieve data for object %d' % self.doId)
        else:
            values = []
            for i in range(count):
                value = di.getString()
                values.append(value)

            for i in range(count):
                found = di.getUint8()
                if not found:
                    self.notify.info('field %s is not found' % fields[i])
                    try:
                        del self.values[fields[i]]
                    except:
                        pass

                else:
                    self.values[fields[i]] = PyDatagram(values[i])

            self.notify.info('got data for %d' % self.doId)
            if self.gotDataHandler != None:
                self.gotDataHandler(self.do, self.dclass)
                self.gotDataHandler = None
        if self.doneEvent != None:
            messenger.send(self.doneEvent, [self, retCode])
        return

    def setFields(self, values):
        dg = PyDatagram()
        dg.addServerHeader(DBSERVER_ID, self.air.ourChannel, DBSERVER_SET_STORED_VALUES)
        dg.addUint32(self.doId)
        dg.addUint16(len(values))
        items = list(values.items())
        for field, value in items:
            dg.addString(field)

        for field, value in items:
            dg.addString(value.getMessage())

        self.air.send(dg)

    def getDatabaseFields(self, dclass):
        fields = []
        for i in range(dclass.getNumInheritedFields()):
            dcf = dclass.getInheritedField(i)
            af = dcf.asAtomicField()
            if af:
                if af.isDb():
                    fields.append(af.getName())

        return fields

    def fillin(self, do, dclass):
        do.doId = self.doId
        for field, value in list(self.values.items()):
            if field == 'setZonesVisited' and value.getLength() == 1:
                self.notify.warning('Ignoring broken setZonesVisited')
            else:
                dclass.directUpdate(do, field, value)

    def reload(self, do, dclass, fields):
        self.doId = do.doId
        self.values = {}
        for fieldName in fields:
            field = dclass.getFieldByName(fieldName)
            if field == None:
                self.notify.warning('No definition for %s' % fieldName)
            else:
                dg = PyDatagram()
                packOk = dclass.packRequiredField(dg, do, field)
                self.values[fieldName] = dg

        return

    def createObject(self, objectType):
        values = {}
        for key, value in list(values.items()):
            values[key] = PyDatagram(str(value))

        context = self.air.dbObjContext
        self.air.dbObjContext += 1
        self.air.dbObjMap[context] = self
        self.createObjType = objectType
        dg = PyDatagram()
        dg.addServerHeader(DBSERVER_ID, self.air.ourChannel, DBSERVER_CREATE_STORED_OBJECT)
        dg.addUint32(context)
        dg.addString('')
        dg.addUint16(objectType)
        dg.addUint16(len(values))
        for field in list(values.keys()):
            dg.addString(field)

        for value in list(values.values()):
            dg.addString(value.getMessage())

        self.air.send(dg)

    def handleCreateObjectResponse(self, di):
        retCode = di.getUint8()
        if retCode != 0:
            self.notify.warning('Database object %s create failed' % self.createObjType)
        else:
            del self.createObjType
            self.doId = di.getUint32()
        if self.doneEvent != None:
            messenger.send(self.doneEvent, [self, retCode])
        return

    def deleteObject(self):
        self.notify.warning('deleting object %s' % self.doId)
        dg = PyDatagram()
        dg.addServerHeader(DBSERVER_ID, self.air.ourChannel, DBSERVER_DELETE_STORED_OBJECT)
        dg.addUint32(self.doId)
        dg.addUint32(3735928559)
        self.air.send(dg)
