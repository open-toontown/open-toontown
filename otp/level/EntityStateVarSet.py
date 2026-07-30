from direct.fsm.StatePush import StateVar
from direct.showbase.PythonUtil import getSetterName
from otp.level.Entity import Entity

class EntityStateVarSet(Entity):

    def __init__(self, entType):
        self._entType = entType
        self._attribNames = []
        for attrib in self._entType.attribs:
            name, defaultVal, type = attrib
            self._addAttrib(name, defaultVal, type)

    def initializeEntity(self, level, entId):
        stateVars = {}
        for attribName in self._attribNames:
            stateVars[attribName] = getattr(self, attribName)

        Entity.initializeEntity(self, level, entId)
        for attribName in self._attribNames:
            stateVars[attribName].set(getattr(self, attribName))

        for attribName in self._attribNames:
            setattr(self, attribName, stateVars[attribName])

    def _getAttributeNames(self):
        return self._attribNames[:]

    def _setter(self, name, value):
        getattr(self, name).set(value)

    def _addAttrib(self, name, defaultVal, type):
        setattr(self, name, StateVar(defaultVal))
        setattr(self, getSetterName(name), Functor(self._setter, name))
        self._attribNames.append(name)
