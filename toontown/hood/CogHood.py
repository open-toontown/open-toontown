from direct.directnotify import DirectNotifyGlobal
from direct.fsm import ClassicFSM, State
from direct.fsm import State
import Hood

class CogHood(Hood.Hood):
    notify = DirectNotifyGlobal.directNotify.newCategory('CogHood')

    def __init__(self, parentFSM, doneEvent, dnaStore, hoodId):
        Hood.Hood.__init__(self, parentFSM, doneEvent, dnaStore, hoodId)
        self.fsm = ClassicFSM.ClassicFSM('Hood', [State.State('start', self.enterStart, self.exitStart, ['cogHQLoader']),
         State.State('cogHQLoader', self.enterCogHQLoader, self.exitCogHQLoader, ['quietZone']),
         State.State('quietZone', self.enterQuietZone, self.exitQuietZone, ['cogHQLoader']),
         State.State('final', self.enterFinal, self.exitFinal, [])], 'start', 'final')
        self.fsm.enterInitialState()

    def load(self):
        Hood.Hood.load(self)
        skyInner = self.sky.find('**/InnerGroup')
        skyMiddle = self.sky.find('**/MiddleGroup')
        skyOuter = self.sky.find('**/OutterSky')
        if not skyOuter.isEmpty():
            skyOuter.setBin('background', 0)
        if not skyMiddle.isEmpty():
            skyMiddle.setDepthWrite(0)
            skyMiddle.setBin('background', 10)
        if not skyInner.isEmpty():
            skyInner.setDepthWrite(0)
            skyInner.setBin('background', 20)

    def loadLoader(self, requestStatus):
        loaderName = requestStatus['loader']
        if loaderName == 'cogHQLoader':
            self.loader = self.cogHQLoaderClass(self, self.fsm.getStateNamed('cogHQLoader'), self.loaderDoneEvent)
            self.loader.load(requestStatus['zoneId'])

    def enterCogHQLoader(self, requestStatus):
        self.accept(self.loaderDoneEvent, self.handleCogHQLoaderDone)
        self.loader.enter(requestStatus)

    def exitCogHQLoader(self):
        self.ignore(self.loaderDoneEvent)
        self.loader.exit()
        self.loader.unload()
        del self.loader

    def handleCogHQLoaderDone(self):
        doneStatus = self.loader.getDoneStatus()
        if self.isSameHood(doneStatus):
            self.fsm.request('quietZone', [doneStatus])
        else:
            self.doneStatus = doneStatus
            messenger.send(self.doneEvent)
