from direct.showbase import DirectObject
from direct.directnotify import DirectNotifyGlobal
import Entity

def andTest(self, a, b):
    if b:
        messenger.send(self.getOutputEventName(), [a])


def orTest(self, a, b):
    if not b:
        messenger.send(self.getOutputEventName(), [a])


def xorTest(self, a, b):
    messenger.send(self.getOutputEventName(), [not (a and b) and (a or b)])


def nandTest(self, a, b):
    if b:
        messenger.send(self.getOutputEventName(), [not (a and b)])


def norTest(self, a, b):
    if not b:
        messenger.send(self.getOutputEventName(), [not (a or b)])


def xnorTest(self, a, b):
    messenger.send(self.getOutputEventName(), [(a and b) or not (a or b)])


class LogicGate(Entity.Entity, DirectObject.DirectObject):
    notify = DirectNotifyGlobal.directNotify.newCategory('LogicGate')
    logicTests = {'and': andTest,
     'or': orTest,
     'xor': xorTest,
     'nand': nandTest,
     'nor': norTest,
     'xnor': xnorTest}

    def __init__(self, level, entId):
        self.input1Event = None
        self.input2Event = None
        DirectObject.DirectObject.__init__(self)
        Entity.Entity.__init__(self, level, entId)
        self.setLogicType(self.logicType)
        self.setIsInput1(self.isInput1)
        self.setIsInput2(self.isInput2)
        self.setInput1Event(self.input1Event)
        self.setInput2Event(self.input2Event)
        return

    def destroy(self):
        self.ignore(self.input1Event)
        self.input1Event = None
        self.ignore(self.input2Event)
        self.input2Event = None
        Entity.Entity.destroy(self)
        return

    def setLogicType(self, logicType):
        self.logicType = logicType
        self.logicTest = self.logicTests[logicType]

    def setIsInput1(self, isTrue):
        if 1 or (not isTrue) != (not self.input1Event):
            self.isInput1 = isTrue
            self.logicTest(self, isTrue, self.isInput2)

    def setIsInput2(self, isTrue):
        if 1 or (not isTrue) != (not self.input2Event):
            self.isInput2 = isTrue
            self.logicTest(self, isTrue, self.isInput1)

    def setInput1Event(self, event):
        if self.input1Event:
            self.ignore(self.input1Event)
        self.input1Event = self.getOutputEventName(event)
        if self.input1Event:
            self.accept(self.input1Event, self.setIsInput1)

    def setInput2Event(self, event):
        if self.input2Event:
            self.ignore(self.input2Event)
        self.input2Event = self.getOutputEventName(event)
        if self.input2Event:
            self.accept(self.input2Event, self.setIsInput2)

    def getName(self):
        return 'switch-%s' % (self.entId,)
