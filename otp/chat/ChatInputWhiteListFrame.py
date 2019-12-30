from direct.fsm import FSM
from otp.otpbase import OTPGlobals
import sys
from direct.directnotify import DirectNotifyGlobal
from direct.gui.DirectGui import *
from pandac.PandaModules import *
from otp.otpbase import OTPLocalizer
from direct.task import Task
from otp.chat.ChatInputTyped import ChatInputTyped

class ChatInputWhiteListFrame(FSM.FSM, DirectFrame):
    notify = DirectNotifyGlobal.directNotify.newCategory('ChatInputWhiteList')
    ExecNamespace = None

    def __init__(self, entryOptions, parent = None, **kw):
        FSM.FSM.__init__(self, 'ChatInputWhiteListFrame')
        self.okayToSubmit = True
        self.receiverId = None
        DirectFrame.__init__(self, parent=aspect2dp, pos=(0, 0, 0.3), relief=None, image=DGG.getDefaultDialogGeom(), image_scale=(1.6, 1, 1.4), image_pos=(0, 0, -0.05), image_color=OTPGlobals.GlobalDialogColor, borderWidth=(0.01, 0.01))
        optiondefs = {'parent': self,
         'relief': DGG.SUNKEN,
         'scale': 0.05,
         'frameSize': (-0.2,
                       25.3,
                       -0.5,
                       1.2),
         'borderWidth': (0.1, 0.1),
         'frameColor': (0.9, 0.9, 0.85, 0.8),
         'pos': (-0.2, 0, 0.11),
         'entryFont': OTPGlobals.getInterfaceFont(),
         'width': 8.6,
         'numLines': 3,
         'cursorKeys': 1,
         'backgroundFocus': 0,
         'suppressKeys': 1,
         'suppressMouse': 1,
         'command': self.sendChat,
         'failedCommand': self.sendFailed,
         'focus': 0,
         'text': '',
         'sortOrder': DGG.FOREGROUND_SORT_INDEX}
        entryOptions['parent'] = self
        self.chatEntry = DirectEntry(**entryOptions)
        self.whisperId = None
        self.chatEntry.bind(DGG.OVERFLOW, self.chatOverflow)
        wantHistory = 0
        if __dev__:
            wantHistory = 1
        self.wantHistory = base.config.GetBool('want-chat-history', wantHistory)
        self.history = ['']
        self.historySize = base.config.GetInt('chat-history-size', 10)
        self.historyIndex = 0
        self.promoteWhiteList = 0
        self.checkBeforeSend = base.config.GetBool('white-list-check-before-send', 0)
        self.whiteList = None
        self.active = 0
        self.autoOff = 0
        self.sendBy = 'Mode'
        self.prefilter = 1
        from direct.gui import DirectGuiGlobals
        self.chatEntry.bind(DirectGuiGlobals.TYPE, self.applyFilter)
        self.chatEntry.bind(DirectGuiGlobals.ERASE, self.applyFilter)
        tpMgr = TextPropertiesManager.getGlobalPtr()
        Red = tpMgr.getProperties('red')
        Red.setTextColor(1.0, 0.0, 0.0, 1)
        tpMgr.setProperties('WLRed', Red)
        del tpMgr
        self.origFrameColor = self.chatEntry['frameColor']
        return

    def destroy(self):
        from direct.gui import DirectGuiGlobals
        self.chatEntry.unbind(DGG.OVERFLOW)
        self.chatEntry.unbind(DirectGuiGlobals.TYPE)
        self.chatEntry.unbind(DirectGuiGlobals.ERASE)
        self.chatEntry.ignoreAll()
        DirectFrame.destroy(self)

    def delete(self):
        self.ignore('arrow_up-up')
        self.ignore('arrow_down-up')

    def requestMode(self, mode, *args):
        return self.request(mode, *args)

    def defaultFilter(self, request, *args):
        if request == 'AllChat':
            if not base.talkAssistant.checkAnyTypedChat():
                messenger.send('Chat-Failed open typed chat test')
                self.notify.warning('Chat-Failed open typed chat test')
                return None
        elif request == 'PlayerWhisper':
            if not base.talkAssistant.checkWhisperTypedChatPlayer(self.whisperId):
                messenger.send('Chat-Failed player typed chat test')
                self.notify.warning('Chat-Failed player typed chat test')
                return None
        elif request == 'AvatarWhisper':
            if not base.talkAssistant.checkWhisperTypedChatAvatar(self.whisperId):
                messenger.send('Chat-Failed avatar typed chat test')
                self.notify.warning('Chat-Failed avatar typed chat test')
                return None
        return FSM.FSM.defaultFilter(self, request, *args)

    def enterOff(self):
        self.deactivate()
        localAvatar.chatMgr.fsm.request('mainMenu')

    def exitOff(self):
        self.activate()

    def enterAllChat(self):
        self.chatEntry['focus'] = 1
        self.show()

    def exitAllChat(self):
        pass

    def enterGuildChat(self):
        self['focus'] = 1
        self.show()

    def exitGuildChat(self):
        pass

    def enterCrewChat(self):
        self['focus'] = 1
        self.show()

    def exitCrewChat(self):
        pass

    def enterPlayerWhisper(self):
        self.tempText = self.chatEntry.get()
        self.activate()

    def exitPlayerWhisper(self):
        self.chatEntry.set(self.tempText)
        self.whisperId = None
        return

    def enterAvatarWhisper(self):
        self.tempText = self.chatEntry.get()
        self.activate()

    def exitAvatarWhisper(self):
        self.chatEntry.set(self.tempText)
        self.whisperId = None
        return

    def activateByData(self, receiverId = None, toPlayer = 0):
        self.receiverId = receiverId
        self.toPlayer = toPlayer
        result = None
        if not self.receiverId:
            result = self.requestMode('AllChat')
        elif self.receiverId and not self.toPlayer:
            self.whisperId = receiverId
            result = self.requestMode('AvatarWhisper')
        elif self.receiverId and self.toPlayer:
            self.whisperId = receiverId
            result = self.requestMode('PlayerWhisper')
        return result

    def activate(self):
        self.chatEntry['focus'] = 1
        self.show()
        self.active = 1
        self.chatEntry.guiItem.setAcceptEnabled(False)

    def deactivate(self):
        self.chatEntry.set('')
        self.chatEntry['focus'] = 0
        self.hide()
        self.active = 0

    def isActive(self):
        return self.active

    def sendChat(self, text, overflow = False):
        if not (len(text) > 0 and text[0] in ['~', '>']):
            if self.prefilter:
                words = text.split(' ')
                newwords = []
                for word in words:
                    if word == '' or self.whiteList.isWord(word) or self.promoteWhiteList:
                        newwords.append(word)
                    else:
                        newwords.append(base.whiteList.defaultWord)

                text = ' '.join(newwords)
            else:
                text = self.chatEntry.get(plain=True)

        if text:
            self.chatEntry.set('')
            if base.config.GetBool('exec-chat', 0) and text[0] == '>':
                text = self.__execMessage(text[1:])
                base.localAvatar.setChatAbsolute(text, CFSpeech | CFTimeout)
                return
            else:
                self.sendChatBySwitch(text)
            if self.wantHistory:
                self.addToHistory(text)
        else:
            localAvatar.chatMgr.deactivateChat()

        if not overflow:
            self.hide()
            if self.autoOff:
                self.requestMode('Off')

            localAvatar.chatMgr.messageSent()

    def sendChatBySwitch(self, text):
        if len(text) > 0 and text[0] == '~':
            base.talkAssistant.sendOpenTalk(text)
        elif self.sendBy == 'Mode':
            self.sendChatByMode(text)
        elif self.sendBy == 'Data':
            self.sendChatByData(text)
        else:
            self.sendChatByMode(text)

    def sendChatByData(self, text):
        if not self.receiverId:
            base.talkAssistant.sendOpenTalk(text)
        elif self.receiverId and not self.toPlayer:
            base.talkAssistant.sendWhisperTalk(text, self.receiverId)
        elif self.receiverId and self.toPlayer:
            base.talkAssistant.sendAccountTalk(text, self.receiverId)

    def sendChatByMode(self, text):
        state = self.getCurrentOrNextState()
        messenger.send('sentRegularChat')
        if state == 'PlayerWhisper':
            base.talkAssistant.sendPlayerWhisperWLChat(text, self.whisperId)
        elif state == 'AvatarWhisper':
            base.talkAssistant.sendAvatarWhisperWLChat(text, self.whisperId)
        elif state == 'GuildChat':
            base.talkAssistant.sendAvatarGuildWLChat(text)
        elif state == 'CrewChat':
            base.talkAssistant.sendAvatarCrewWLChat(text)
        elif len(text) > 0 and text[0] == '~':
            base.talkAssistant.sendOpenTalk(text)
        else:
            base.talkAssistant.sendOpenTalk(text)

    def sendFailed(self, text):
        if not self.checkBeforeSend:
            self.sendChat(text)
            return
        self.chatEntry['frameColor'] = (0.9, 0.0, 0.0, 0.8)

        def resetFrameColor(task = None):
            self.chatEntry['frameColor'] = self.origFrameColor
            return Task.done

        taskMgr.doMethodLater(0.1, resetFrameColor, 'resetFrameColor')
        self.applyFilter(keyArgs=None, strict=True)
        self.okayToSubmit = True
        self.chatEntry.guiItem.setAcceptEnabled(True)
        return

    def chatOverflow(self, overflowText):
        self.notify.debug('chatOverflow')
        self.sendChat(self.chatEntry.get(plain=True), overflow=True)

    def addToHistory(self, text):
        self.history = [text] + self.history[:self.historySize - 1]
        self.historyIndex = 0

    def getPrevHistory(self):
        self.chatEntry.set(self.history[self.historyIndex])
        self.historyIndex += 1
        self.historyIndex %= len(self.history)

    def getNextHistory(self):
        self.chatEntry.set(self.history[self.historyIndex])
        self.historyIndex -= 1
        self.historyIndex %= len(self.history)

    def importExecNamespace(self):
        pass

    def __execMessage(self, message):
        if not ChatInputTyped.ExecNamespace:
            ChatInputTyped.ExecNamespace = {}
            exec('from pandac.PandaModules import *', globals(), self.ExecNamespace)
            self.importExecNamespace()
        try:
            if not isClient():
                print('EXECWARNING ChatInputWhiteListFrame eval: %s' % message)
                printStack()
            return str(eval(message, globals(), ChatInputTyped.ExecNamespace))
        except SyntaxError:
            try:
                if not isClient():
                    print('EXECWARNING ChatInputWhiteListFrame exec: %s' % message)
                    printStack()
                exec(message, globals(), ChatInputTyped.ExecNamespace)
                return 'ok'
            except:
                exception = sys.exc_info()[0]
                extraInfo = sys.exc_info()[1]
                if extraInfo:
                    return str(extraInfo)
                else:
                    return str(exception)

        except:
            exception = sys.exc_info()[0]
            extraInfo = sys.exc_info()[1]
            if extraInfo:
                return str(extraInfo)
            else:
                return str(exception)

    def applyFilter(self, keyArgs, strict = False):
        text = self.chatEntry.get(plain=True)
        if len(text) > 0 and text[0] in ['~', '>']:
            self.okayToSubmit = True
        else:
            words = text.split(' ')
            newwords = []
            self.notify.debug('%s' % words)
            self.okayToSubmit = True
            for word in words:
                if word == '' or self.whiteList.isWord(word):
                    newwords.append(word)
                else:
                    if self.checkBeforeSend:
                        self.okayToSubmit = False
                    else:
                        self.okayToSubmit = True
                    newwords.append('\x01WLEnter\x01' + word + '\x02')

            if not strict:
                lastword = words[-1]
                if lastword == '' or self.whiteList.isPrefix(lastword):
                    newwords[-1] = lastword
                else:
                    newwords[-1] = '\x01WLEnter\x01' + lastword + '\x02'
            newtext = ' '.join(newwords)
            self.chatEntry.set(newtext)
        self.chatEntry.guiItem.setAcceptEnabled(self.okayToSubmit)
