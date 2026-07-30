from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.showbase import DirectObject, TaskThreaded

class GameServerTestSuite(DirectObject.DirectObject, TaskThreaded.TaskThreaded):
    notify = directNotify.newCategory('GarbageReport')

    def __init__(self, cr):
        self.cr = cr
        TaskThreaded.TaskThreaded.__init__(self, self.__class__.__name__)

        class TimeoutTest(DirectObject.DirectObject):
            Timeout = 10

            def _getTaskName(self, name):
                return '%s-timeout-%s' % (self.__class__.__name__, name)

            def startTimeout(self, name):
                self.stopTimeout(name)
                _taskName = self._getTaskName(name)
                taskMgr.doMethodLater(self.Timeout, Functor(self._timeout, _taskName), _taskName)

            def stopTimeout(self, name):
                _taskName = self._getTaskName(name)
                taskMgr.remove(_taskName)

            def _timeout(self, taskName, task = None):
                self.parent.notify.warning('TEST TIMED OUT: %s' % taskName)
                import pdb
                pdb.set_trace()

        class MsgHandlerTest:

            def installMsgHandler(self):
                self.oldHandler = self.parent.handler
                self.parent.handler = self.handleMsg

            def removeMsgHandler(self):
                self.parent.handler = self.oldHandler
                del self.oldHandler

            def handleMsg(self, msgType, di):
                self.parent.cr.handler(msgType, di)

        class TestGetAvatars(TaskThreaded.TaskThread, TimeoutTest, MsgHandlerTest):

            def setUp(self):
                self.state = 'request'
                self.installMsgHandler()

            def handleMsg(self, msgType, di):
                if msgType == CLIENT_GET_AVATARS_RESP:
                    self.finished()
                else:
                    MsgHandlerTest.handleMsg(self, msgType, di)

            def run(self):
                if self.state == 'request':
                    self.parent.cr.sendGetAvatarsMsg()
                    self.startTimeout('getAvatarList')
                    self.state = 'waitForList'

            def tearDown(self):
                self.stopTimeout('getAvatarList')
                self.removeMsgHandler()

        class TestInterestOpenAndClose(TaskThreaded.TaskThread, TimeoutTest):

            def setUp(self):
                self.state = 'open'

            def run(self):
                if self.state == 'open':

                    def openInterestDone():
                        self.stopTimeout(self.timeoutName)
                        self.state = 'modify'

                    doneEvent = uniqueName('openInterest')
                    self.acceptOnce(doneEvent, openInterestDone)
                    openInterestDone = None
                    self.timeoutName = 'openInterest'
                    self.startTimeout(self.timeoutName)
                    self.handle = self.parent.cr.addInterest(self.parent.cr.GameGlobalsId, 91504, 'testInterest', doneEvent)
                    self.state = 'waitOpenComplete'
                elif self.state == 'modify':

                    def modifyInterestDone():
                        self.stopTimeout(self.timeoutName)
                        self.state = 'close'

                    doneEvent = uniqueName('openInterest')
                    self.acceptOnce(doneEvent, modifyInterestDone)
                    modifyInterestDone = None
                    self.timeoutName = 'modifyInterest'
                    self.startTimeout(self.timeoutName)
                    self.parent.cr.alterInterest(self.handle, self.parent.cr.GameGlobalsId, 91506, 'testInterest', doneEvent)
                    self.state = 'waitModifyComplete'
                elif self.state == 'close':

                    def closeInterestDone():
                        self.stopTimeout(self.timeoutName)
                        self.state = 'done'

                    doneEvent = uniqueName('closeInterest')
                    self.acceptOnce(doneEvent, closeInterestDone)
                    closeInterestDone = None
                    self.timeoutName = 'closeInterest'
                    self.startTimeout(self.timeoutName)
                    self.handle = self.parent.cr.removeInterest(self.handle, doneEvent)
                    self.state = 'waitCloseComplete'
                elif self.state == 'done':
                    self.finished()
                return

        class TestNonRequiredNonSetFields(TaskThreaded.TaskThread, TimeoutTest):
            Timeout = 60

            def setUp(self):
                self.timeoutName = 'lookForObj'
                self.startTimeout(self.timeoutName)

            def run(self):
                testObj = self.parent.cr.doFind('DistributedTestObject')
                if testObj is not None:
                    self.finished()
                return

            def tearDown(self):
                self.stopTimeout(self.timeoutName)
                del self.timeoutName

        self.scheduleThread(TestInterestOpenAndClose())
        self.scheduleThread(TestNonRequiredNonSetFields())
