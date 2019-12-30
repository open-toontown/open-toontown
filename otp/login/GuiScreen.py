from pandac.PandaModules import *
from otp.otpbase import OTPGlobals
from direct.gui.DirectGui import *
from otp.otpgui import OTPDialog
from direct.directnotify import DirectNotifyGlobal
from otp.otpbase import OTPLocalizer
from direct.task.Task import Task

class GuiScreen:
    notify = DirectNotifyGlobal.directNotify.newCategory('GuiScreen')
    DGG.ENTERPRESS_ADVANCE = 0
    DGG.ENTERPRESS_ADVANCE_IFNOTEMPTY = 1
    DGG.ENTERPRESS_DONT_ADVANCE = 2
    DGG.ENTERPRESS_REMOVE_FOCUS = 3
    ENTRY_WIDTH = 20

    def __init__(self):
        self.waitingForDatabase = None
        self.focusIndex = None
        self.suppressClickSound = 0
        return

    def startFocusMgmt(self, startFocus = 0, enterPressBehavior = DGG.ENTERPRESS_ADVANCE_IFNOTEMPTY, overrides = {}, globalFocusHandler = None):
        GuiScreen.notify.debug('startFocusMgmt:\nstartFocus=%s,\nenterPressBehavior=%s\noverrides=%s' % (startFocus, enterPressBehavior, overrides))
        self.accept('tab', self.__handleTab)
        self.accept('shift-tab', self.__handleShiftTab)
        self.accept('enter', self.__handleEnter)
        self.__startFrameStartTask()
        self.userGlobalFocusHandler = globalFocusHandler
        self.focusHandlerAbsorbCounts = {}
        for i in range(len(self.focusList)):
            item = self.focusList[i]
            if isinstance(item, DirectEntry):
                self.focusHandlerAbsorbCounts[item] = 0

        self.userFocusHandlers = {}
        self.userCommandHandlers = {}
        for i in range(len(self.focusList)):
            item = self.focusList[i]
            if isinstance(item, DirectEntry):
                self.userFocusHandlers[item] = (item['focusInCommand'], item['focusInExtraArgs'])
                item['focusInCommand'] = self.__handleFocusChangeAbsorb
                item['focusInExtraArgs'] = [i]
                self.userCommandHandlers[item] = (item['command'], item['extraArgs'])
                item['command'] = None
                item['extraArgs'] = []
            elif isinstance(item, DirectScrolledList):
                self.userCommandHandlers[item] = (item['command'], item['extraArgs'])
                item['command'] = self.__handleDirectScrolledListCommand
                item['extraArgs'] = [i]

        self.enterPressHandlers = {}
        for i in range(len(self.focusList)):
            item = self.focusList[i]
            behavior = enterPressBehavior
            if item in overrides:
                behavior = overrides[item]
            if callable(behavior):
                self.enterPressHandlers[item] = behavior
            else:
                if not isinstance(item, DirectEntry) and behavior == GuiScreen_ENTERPRESS_ADVANCE_IFNOTEMPTY:
                    behavior = GuiScreen_ENTERPRESS_ADVANCE
                commandHandlers = (self.__alwaysAdvanceFocus,
                 self.__advanceFocusIfNotEmpty,
                 self.__neverAdvanceFocus,
                 self.__ignoreEnterPress)
                self.enterPressHandlers[item] = commandHandlers[behavior]

        self.setFocus(startFocus)
        return

    def focusMgmtActive(self):
        return self.focusIndex != None

    def stopFocusMgmt(self):
        GuiScreen.notify.debug('stopFocusMgmt')
        if not self.focusMgmtActive():
            return
        self.ignore('tab')
        self.ignore('shift-tab')
        self.ignore('enter')
        self.__stopFrameStartTask()
        self.userGlobalFocusHandler = None
        self.focusIndex = None
        self.focusHandlerAbsorbCounts = {}
        for item in self.focusList:
            if isinstance(item, DirectEntry):
                userHandler, userHandlerArgs = self.userFocusHandlers[item]
                item['focusInCommand'] = userHandler
                item['focusInExtraArgs'] = userHandlerArgs
                userHandler, userHandlerArgs = self.userCommandHandlers[item]
                item['command'] = userHandler
                item['extraArgs'] = userHandlerArgs
            elif isinstance(item, DirectScrolledList):
                userHandler, userHandlerArgs = self.userCommandHandlers[item]
                item['command'] = userHandler
                item['extraArgs'] = userHandlerArgs

        self.userFocusHandlers = {}
        self.userCommandHandlers = {}
        self.enterPressHandlers = {}
        return

    def setFocus(self, arg, suppressSound = 1):
        if type(arg) == type(0):
            index = arg
        else:
            index = self.focusList.index(arg)
        if suppressSound:
            self.suppressClickSound += 1
        self.__setFocusIndex(index)

    def advanceFocus(self, condition = 1):
        index = self.getFocusIndex()
        if condition:
            index += 1
        self.setFocus(index, suppressSound=0)

    def getFocusIndex(self):
        if not self.focusMgmtActive():
            return None
        return self.focusIndex

    def getFocusItem(self):
        if not self.focusMgmtActive():
            return None
        return self.focusList[self.focusIndex]

    def removeFocus(self):
        focusItem = self.getFocusItem()
        if isinstance(focusItem, DirectEntry):
            focusItem['focus'] = 0
        if self.userGlobalFocusHandler:
            self.userGlobalFocusHandler(None)
        return

    def restoreFocus(self):
        self.setFocus(self.getFocusItem())

    def __setFocusIndex(self, index):
        focusIndex = index % len(self.focusList)
        focusItem = self.focusList[focusIndex]
        if isinstance(focusItem, DirectEntry):
            focusItem['focus'] = 1
            self.focusHandlerAbsorbCounts[focusItem] += 1
        self.__handleFocusChange(focusIndex)

    def __chainToUserCommandHandler(self, item):
        userHandler, userHandlerArgs = self.userCommandHandlers[item]
        if userHandler:
            if isinstance(item, DirectEntry):
                enteredText = item.get()
                userHandler(*[enteredText] + userHandlerArgs)
            elif isinstance(item, DirectScrolledList):
                userHandler(*userHandlerArgs)

    def __chainToUserFocusHandler(self, item):
        if isinstance(item, DirectEntry):
            userHandler, userHandlerArgs = self.userFocusHandlers[item]
            if userHandler:
                userHandler(*userHandlerArgs)

    def __handleTab(self):
        self.tabPressed = 1
        self.focusDirection = 1
        self.__setFocusIndex(self.getFocusIndex() + self.focusDirection)

    def __handleShiftTab(self):
        self.tabPressed = 1
        self.focusDirection = -1
        self.__setFocusIndex(self.getFocusIndex() + self.focusDirection)

    def __handleFocusChangeAbsorb(self, index):
        item = self.focusList[index]
        if self.focusHandlerAbsorbCounts[item] > 0:
            self.focusHandlerAbsorbCounts[item] -= 1
        else:
            self.__handleFocusChange(index)

    def playFocusChangeSound(self):
        base.playSfx(DGG.getDefaultClickSound())

    def __handleFocusChange(self, index):
        if index != self.focusIndex:
            self.removeFocus()
        self.__focusChangedThisFrame = 1
        if hasattr(self, 'tabPressed'):
            del self.tabPressed
        else:
            self.focusDirection = 1
        self.focusIndex = index
        if self.suppressClickSound > 0:
            self.suppressClickSound -= 1
        else:
            self.playFocusChangeSound()
        focusItem = self.getFocusItem()
        if self.userGlobalFocusHandler:
            self.userGlobalFocusHandler(focusItem)
        if self.getFocusItem() != focusItem:
            GuiScreen.notify.debug('focus changed by global focus handler')
        if self.focusMgmtActive():
            self.__chainToUserFocusHandler(focusItem)

    def __startFrameStartTask(self):
        self.__focusChangedThisFrame = 0
        self.frameStartTaskName = 'GuiScreenFrameStart'
        taskMgr.add(self.__handleFrameStart, self.frameStartTaskName, -100)

    def __stopFrameStartTask(self):
        taskMgr.remove(self.frameStartTaskName)
        del self.frameStartTaskName
        del self.__focusChangedThisFrame

    def __handleFrameStart(self, task):
        self.__focusChangedThisFrame = 0
        return Task.cont

    def __handleDirectScrolledListCommand(self, index):
        self.__chainToUserCommandHandler(self.focusList[index])
        self.setFocus(index, suppressSound=self.getFocusIndex() == index)

    def __handleEnter(self):
        if self.__focusChangedThisFrame:
            return
        focusItem = self.getFocusItem()
        if isinstance(focusItem, DirectEntry):
            self.__chainToUserCommandHandler(focusItem)
        if self.focusMgmtActive() and focusItem == self.getFocusItem():
            self.enterPressHandlers[focusItem]()

    def __alwaysAdvanceFocus(self):
        self.advanceFocus()

    def __advanceFocusIfNotEmpty(self):
        focusItem = self.getFocusItem()
        enteredText = focusItem.get()
        if enteredText != '':
            self.advanceFocus()
        else:
            self.setFocus(self.getFocusIndex())

    def __neverAdvanceFocus(self):
        self.setFocus(self.getFocusIndex())

    def __ignoreEnterPress(self):
        pass

    def waitForDatabaseTimeout(self, requestName = 'unknown'):
        GuiScreen.notify.debug('waiting for database timeout %s at %s' % (requestName, globalClock.getFrameTime()))
        globalClock.tick()
        taskMgr.doMethodLater(OTPGlobals.DatabaseDialogTimeout, self.__showWaitingForDatabase, 'waitingForDatabase', extraArgs=[requestName])

    def __showWaitingForDatabase(self, requestName):
        GuiScreen.notify.info('timed out waiting for %s at %s' % (requestName, globalClock.getFrameTime()))
        dialogClass = OTPGlobals.getDialogClass()
        self.waitingForDatabase = dialogClass(text=OTPLocalizer.GuiScreenToontownUnavailable, dialogName='WaitingForDatabase', buttonTextList=[OTPLocalizer.GuiScreenCancel], style=OTPDialog.Acknowledge, command=self.__handleCancelWaiting)
        self.waitingForDatabase.show()
        taskMgr.doMethodLater(OTPGlobals.DatabaseGiveupTimeout, self.__giveUpWaitingForDatabase, 'waitingForDatabase', extraArgs=[requestName])
        return Task.done

    def __giveUpWaitingForDatabase(self, requestName):
        GuiScreen.notify.info('giving up waiting for %s at %s' % (requestName, globalClock.getFrameTime()))
        self.cleanupWaitingForDatabase()
        messenger.send(self.doneEvent, [{'mode': 'failure'}])
        return Task.done

    def cleanupWaitingForDatabase(self):
        if self.waitingForDatabase != None:
            self.waitingForDatabase.cleanup()
            self.waitingForDatabase = None
        taskMgr.remove('waitingForDatabase')
        return

    def __handleCancelWaiting(self, value):
        self.cleanupWaitingForDatabase()
        messenger.send(self.doneEvent, [{'mode': 'quit'}])
