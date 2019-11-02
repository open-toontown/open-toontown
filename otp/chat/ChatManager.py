import string
import sys
from direct.showbase import DirectObject
from otp.otpbase import OTPGlobals
from direct.fsm import ClassicFSM
from direct.fsm import State
from otp.login import SecretFriendsInfoPanel
from otp.login import PrivacyPolicyPanel
from otp.otpbase import OTPLocalizer
from direct.directnotify import DirectNotifyGlobal
from otp.login import LeaveToPayDialog
from direct.gui.DirectGui import *
from pandac.PandaModules import *
ChatEvent = 'ChatEvent'
NormalChatEvent = 'NormalChatEvent'
SCChatEvent = 'SCChatEvent'
SCCustomChatEvent = 'SCCustomChatEvent'
SCEmoteChatEvent = 'SCEmoteChatEvent'
OnScreen = 0
OffScreen = 1
Thought = 2
ThoughtPrefix = '.'

def isThought(message):
    if len(message) == 0:
        return 0
    elif string.find(message, ThoughtPrefix, 0, len(ThoughtPrefix)) >= 0:
        return 1
    else:
        return 0


def removeThoughtPrefix(message):
    if isThought(message):
        return message[len(ThoughtPrefix):]
    else:
        return message


class ChatManager(DirectObject.DirectObject):
    notify = DirectNotifyGlobal.directNotify.newCategory('ChatManager')
    execChat = base.config.GetBool('exec-chat', 0)

    def __init__(self, cr, localAvatar):
        self.cr = cr
        self.localAvatar = localAvatar
        self.wantBackgroundFocus = 1
        self.__scObscured = 0
        self.__normalObscured = 0
        self.openChatWarning = None
        self.unpaidChatWarning = None
        self.teaser = None
        self.paidNoParentPassword = None
        self.noSecretChatAtAll = None
        self.noSecretChatAtAllAndNoWhitelist = None
        self.noSecretChatWarning = None
        self.activateChatGui = None
        self.chatMoreInfo = None
        self.chatPrivacyPolicy = None
        self.secretChatActivated = None
        self.problemActivatingChat = None
        self.leaveToPayDialog = None
        self.fsm = ClassicFSM.ClassicFSM('chatManager', [State.State('off', self.enterOff, self.exitOff),
         State.State('mainMenu', self.enterMainMenu, self.exitMainMenu),
         State.State('speedChat', self.enterSpeedChat, self.exitSpeedChat),
         State.State('normalChat', self.enterNormalChat, self.exitNormalChat),
         State.State('whisper', self.enterWhisper, self.exitWhisper),
         State.State('whisperChat', self.enterWhisperChat, self.exitWhisperChat),
         State.State('whisperChatPlayer', self.enterWhisperChatPlayer, self.exitWhisperChatPlayer),
         State.State('whisperSpeedChat', self.enterWhisperSpeedChat, self.exitWhisperSpeedChat),
         State.State('whisperSpeedChatPlayer', self.enterWhisperSpeedChatPlayer, self.exitWhisperSpeedChatPlayer),
         State.State('openChatWarning', self.enterOpenChatWarning, self.exitOpenChatWarning),
         State.State('leaveToPayDialog', self.enterLeaveToPayDialog, self.exitLeaveToPayDialog),
         State.State('unpaidChatWarning', self.enterUnpaidChatWarning, self.exitUnpaidChatWarning),
         State.State('noSecretChatAtAll', self.enterNoSecretChatAtAll, self.exitNoSecretChatAtAll),
         State.State('noSecretChatAtAllAndNoWhitelist', self.enterNoSecretChatAtAllAndNoWhitelist, self.exitNoSecretChatAtAllAndNoWhitelist),
         State.State('noSecretChatWarning', self.enterNoSecretChatWarning, self.exitNoSecretChatWarning),
         State.State('noFriendsWarning', self.enterNoFriendsWarning, self.exitNoFriendsWarning),
         State.State('otherDialog', self.enterOtherDialog, self.exitOtherDialog),
         State.State('activateChat', self.enterActivateChat, self.exitActivateChat),
         State.State('chatMoreInfo', self.enterChatMoreInfo, self.exitChatMoreInfo),
         State.State('chatPrivacyPolicy', self.enterChatPrivacyPolicy, self.exitChatPrivacyPolicy),
         State.State('secretChatActivated', self.enterSecretChatActivated, self.exitSecretChatActivated),
         State.State('problemActivatingChat', self.enterProblemActivatingChat, self.exitProblemActivatingChat),
         State.State('whiteListOpenChat', self.enterWhiteListOpenChat, self.exitWhiteListOpenChat),
         State.State('whiteListAvatarChat', self.enterWhiteListAvatarChat, self.exitWhiteListAvatarChat),
         State.State('whiteListPlayerChat', self.enterWhiteListPlayerChat, self.exitWhiteListPlayerChat),
         State.State('trueFriendTeaserPanel', self.enterTrueFriendTeaserPanel, self.exitTrueFriendTeaserPanel)], 'off', 'off')
        self.fsm.enterInitialState()
        return

    def delete(self):
        self.ignoreAll()
        del self.fsm
        if hasattr(self.chatInputNormal, 'destroy'):
            self.chatInputNormal.destroy()
        self.chatInputNormal.delete()
        del self.chatInputNormal
        self.chatInputSpeedChat.delete()
        del self.chatInputSpeedChat
        if self.openChatWarning:
            self.openChatWarning.destroy()
            self.openChatWarning = None
        if self.unpaidChatWarning:
            self.payButton = None
            self.unpaidChatWarning.destroy()
            self.unpaidChatWarning = None
        if self.teaser:
            self.teaser.cleanup()
            self.teaser.unload()
            self.teaser = None
        if self.noSecretChatAtAll:
            self.noSecretChatAtAll.destroy()
            self.noSecretChatAtAll = None
        if self.noSecretChatAtAllAndNoWhitelist:
            self.noSecretChatAtAllAndNoWhitelist.destroy()
            self.noSecretChatAtAllAndNoWhitelist = None
        if self.noSecretChatWarning:
            self.noSecretChatWarning.destroy()
            self.noSecretChatWarning = None
        if self.activateChatGui:
            self.activateChatGui.destroy()
            self.activateChatGui = None
        if self.chatMoreInfo:
            self.chatMoreInfo.destroy()
            self.chatMoreInfo = None
        if self.chatPrivacyPolicy:
            self.chatPrivacyPolicy.destroy()
            self.chatPrivacyPolicy = None
        if self.secretChatActivated:
            self.secretChatActivated.destroy()
            self.secretChatActivated = None
        if self.problemActivatingChat:
            self.problemActivatingChat.destroy()
            self.problemActivatingChat = None
        del self.localAvatar
        del self.cr
        return

    def obscure(self, normal, sc):
        self.__scObscured = sc
        if self.__scObscured:
            self.scButton.hide()
        self.__normalObscured = normal
        if self.__normalObscured:
            self.normalButton.hide()

    def isObscured(self):
        return (self.__normalObscured, self.__scObscured)

    def stop(self):
        self.fsm.request('off')
        self.ignoreAll()

    def start(self):
        self.fsm.request('mainMenu')

    def announceChat(self):
        messenger.send(ChatEvent)

    def announceSCChat(self):
        messenger.send(SCChatEvent)
        self.announceChat()

    def sendChatString(self, message):
        chatFlags = CFSpeech | CFTimeout
        if base.cr.wantSwitchboardHacks:
            from otp.switchboard import badwordpy
            badwordpy.init('', '')
            message = badwordpy.scrub(message)
        if isThought(message):
            message = removeThoughtPrefix(message)
            chatFlags = CFThought
        messenger.send(NormalChatEvent)
        self.announceChat()

    def sendWhisperString(self, message, whisperAvatarId):
        pass

    def sendSCChatMessage(self, msgIndex):
        base.talkAssistant.sendOpenSpeedChat(1, msgIndex)

    def sendSCWhisperMessage(self, msgIndex, whisperAvatarId, toPlayer):
        if toPlayer:
            base.talkAssistant.sendPlayerWhisperSpeedChat(1, msgIndex, whisperAvatarId)
        else:
            base.talkAssistant.sendAvatarWhisperSpeedChat(1, msgIndex, whisperAvatarId)

    def sendSCCustomChatMessage(self, msgIndex):
        base.talkAssistant.sendOpenSpeedChat(3, msgIndex)

    def sendSCCustomWhisperMessage(self, msgIndex, whisperAvatarId, toPlayer):
        if toPlayer:
            base.talkAssistant.sendPlayerWhisperSpeedChat(3, msgIndex, whisperAvatarId)
        else:
            base.talkAssistant.sendAvatarWhisperSpeedChat(3, msgIndex, whisperAvatarId)

    def sendSCEmoteChatMessage(self, emoteId):
        base.talkAssistant.sendOpenSpeedChat(2, emoteId)

    def sendSCEmoteWhisperMessage(self, emoteId, whisperAvatarId, toPlayer):
        if toPlayer:
            base.talkAssistant.sendPlayerWhisperSpeedChat(2, emoteId, whisperAvatarId)
        else:
            base.talkAssistant.sendAvatarWhisperSpeedChat(2, emoteId, whisperAvatarId)

    def enterOff(self):
        self.scButton.hide()
        self.normalButton.hide()
        self.ignoreAll()

    def exitOff(self):
        pass

    def enterMainMenu(self):
        self.checkObscurred()
        if self.localAvatar.canChat() or self.cr.wantMagicWords:
            if self.wantBackgroundFocus:
                self.chatInputNormal.chatEntry['backgroundFocus'] = 1
            self.acceptOnce('enterNormalChat', self.fsm.request, ['normalChat'])

    def checkObscurred(self):
        if not self.__scObscured:
            self.scButton.show()
        if not self.__normalObscured:
            self.normalButton.show()

    def exitMainMenu(self):
        self.scButton.hide()
        self.normalButton.hide()
        self.ignore('enterNormalChat')
        if self.wantBackgroundFocus:
            self.chatInputNormal.chatEntry['backgroundFocus'] = 0

    def whisperTo(self, avatarName, avatarId, playerId = None):
        self.fsm.request('whisper', [avatarName, avatarId, playerId])

    def noWhisper(self):
        self.fsm.request('mainMenu')

    def handleWhiteListSelect(self):
        self.fsm.request('whiteListOpenChat')

    def enterWhiteListOpenChat(self):
        self.checkObscurred()
        if self.wantBackgroundFocus:
            self.chatInputNormal.chatEntry['backgroundFocus'] = 0
        base.localAvatar.chatMgr.chatInputWhiteList.activateByData()

    def exitWhiteListOpenChat(self):
        pass

    def enterWhiteListAvatarChat(self, receiverId):
        if self.wantBackgroundFocus:
            self.chatInputNormal.chatEntry['backgroundFocus'] = 0
        base.localAvatar.chatMgr.chatInputWhiteList.activateByData(receiverId, 0)

    def exitWhiteListAvatarChat(self):
        pass

    def enterWhiteListPlayerChat(self, receiverId):
        if self.wantBackgroundFocus:
            self.chatInputNormal.chatEntry['backgroundFocus'] = 0
        base.localAvatar.chatMgr.chatInputWhiteList.activateByData(receiverId, 1)

    def exitWhiteListPlayerChat(self):
        pass

    def enterWhisper(self, avatarName, avatarId, playerId = None):
        self.whisperScButton['extraArgs'] = [avatarName, avatarId, playerId]
        self.whisperButton['extraArgs'] = [avatarName, avatarId, playerId]
        playerName = None
        chatToToon = 1
        online = 0
        if self.cr.doId2do.has_key(avatarId):
            online = 1
        elif self.cr.isFriend(avatarId):
            online = self.cr.isFriendOnline(avatarId)
        hasManager = hasattr(base.cr, 'playerFriendsManager')
        if hasManager:
            if base.cr.playerFriendsManager.askAvatarOnline(avatarId):
                online = 1
        avatarUnderstandable = 0
        playerUnderstandable = 0
        av = None
        if avatarId:
            av = self.cr.identifyAvatar(avatarId)
        if av != None:
            avatarUnderstandable = av.isUnderstandable()
        if playerId:
            if base.cr.playerFriendsManager.playerId2Info.has_key(playerId):
                playerInfo = base.cr.playerFriendsManager.playerId2Info.get(playerId)
                playerName = playerInfo.playerName
                online = 1
                playerUnderstandable = playerInfo.understandableYesNo
                if playerUnderstandable or not avatarId:
                    chatToToon = 0
        if chatToToon:
            chatName = avatarName
        else:
            chatName = playerName
        normalButtonObscured, scButtonObscured = self.isObscured()
        if (avatarUnderstandable or playerUnderstandable) and online and not normalButtonObscured:
            self.whisperButton['state'] = 'normal'
            self.enablewhisperButton()
        else:
            self.whisperButton['state'] = 'inactive'
            self.disablewhisperButton()
        if online:
            self.whisperScButton['state'] = 'normal'
            self.changeFrameText(OTPLocalizer.ChatManagerWhisperToName % chatName)
        else:
            self.whisperScButton['state'] = 'inactive'
            self.changeFrameText(OTPLocalizer.ChatManagerWhisperOffline % chatName)
        self.whisperFrame.show()
        self.refreshWhisperFrame()
        if avatarUnderstandable or playerUnderstandable:
            if playerId and not chatToToon:
                if self.wantBackgroundFocus:
                    self.chatInputNormal.chatEntry['backgroundFocus'] = 1
                self.acceptOnce('enterNormalChat', self.fsm.request, ['whisperChatPlayer', [avatarName, playerId]])
            elif online and chatToToon:
                if self.wantBackgroundFocus:
                    self.chatInputNormal.chatEntry['backgroundFocus'] = 1
                self.acceptOnce('enterNormalChat', self.fsm.request, ['whisperChat', [avatarName, avatarId]])
        if base.cr.config.GetBool('force-typed-whisper-enabled', 0):
            self.whisperButton['state'] = 'normal'
            self.enablewhisperButton()
        return

    def disablewhisperButton(self):
        pass

    def enablewhisperButton(self):
        pass

    def refreshWhisperFrame(self):
        pass

    def changeFrameText(self, newText):
        self.whisperFrame['text'] = newText

    def exitWhisper(self):
        self.whisperFrame.hide()
        self.ignore('enterNormalChat')
        self.chatInputNormal.chatEntry['backgroundFocus'] = 0

    def enterWhisperSpeedChat(self, avatarId):
        self.whisperFrame.show()
        if self.wantBackgroundFocus:
            self.chatInputNormal.chatEntry['backgroundFocus'] = 0
        self.chatInputSpeedChat.show(avatarId)

    def exitWhisperSpeedChat(self):
        self.whisperFrame.hide()
        self.chatInputSpeedChat.hide()

    def enterWhisperSpeedChatPlayer(self, playerId):
        self.whisperFrame.show()
        if self.wantBackgroundFocus:
            self.chatInputNormal.chatEntry['backgroundFocus'] = 0
        self.chatInputSpeedChat.show(playerId, 1)

    def exitWhisperSpeedChatPlayer(self):
        self.whisperFrame.hide()
        self.chatInputSpeedChat.hide()

    def enterWhisperChat(self, avatarName, avatarId):
        result = self.chatInputNormal.activateByData(avatarId)
        return result

    def exitWhisperChat(self):
        self.chatInputNormal.deactivate()

    def enterWhisperChatPlayer(self, avatarName, playerId):
        playerInfo = base.cr.playerFriendsManager.getFriendInfo(playerId)
        if playerInfo:
            avatarName = playerInfo.playerName
        result = self.chatInputNormal.activateByData(playerId, 1)
        return result

    def exitWhisperChatPlayer(self):
        self.chatInputNormal.deactivate()

    def enterSpeedChat(self):
        messenger.send('enterSpeedChat')
        if not self.__scObscured:
            self.scButton.show()
        if not self.__normalObscured:
            self.normalButton.show()
        if self.wantBackgroundFocus:
            self.chatInputNormal.chatEntry['backgroundFocus'] = 0
        self.chatInputSpeedChat.show()

    def exitSpeedChat(self):
        self.scButton.hide()
        self.normalButton.hide()
        self.chatInputSpeedChat.hide()

    def enterNormalChat(self):
        result = self.chatInputNormal.activateByData()
        return result

    def exitNormalChat(self):
        self.chatInputNormal.deactivate()

    def enterOpenChatWarning(self):
        self.notify.error('called enterOpenChatWarning() on parent class')

    def exitOpenChatWarning(self):
        self.notify.error('called exitOpenChatWarning() on parent class')

    def enterLeaveToPayDialog(self):
        if self.leaveToPayDialog == None:
            self.leaveToPayDialog = LeaveToPayDialog.LeaveToPayDialog(self.paidNoParentPassword)
            self.leaveToPayDialog.setCancel(self.__handleLeaveToPayCancel)
        self.leaveToPayDialog.show()
        return

    def exitLeaveToPayDialog(self):
        if self.leaveToPayDialog:
            self.leaveToPayDialog.destroy()
            self.leaveToPayDialog = None
        return

    def enterUnpaidChatWarning(self):
        self.notify.error('called enterUnpaidChatWarning() on parent class')

    def exitUnpaidChatWarning(self):
        self.notify.error('called exitUnpaidChatWarning() on parent class')

    def enterNoSecretChatAtAll(self):
        self.notify.error('called enterNoSecretChatAtAll() on parent class')

    def exitNoSecretChatAtAll(self):
        self.notify.error('called exitNoSecretChatAtAll() on parent class')

    def enterNoSecretChatAtAllAndNoWhitelist(self):
        self.notify.error('called enterNoSecretChatAtAllAndNoWhitelist() on parent class')

    def exitNoSecretChatAtAllAndNoWhitelist(self):
        self.notify.error('called exitNoSecretChatAtAllAndNoWhitelist() on parent class')

    def enterNoSecretChatWarning(self):
        self.notify.error('called enterNoSecretChatWarning() on parent class')

    def exitNoSecretChatWarning(self):
        self.notify.error('called exitNoSecretChatWarning() on parent class')

    def enterNoFriendsWarning(self):
        self.notify.error('called enterNoFriendsWarning() on parent class')

    def exitNoFriendsWarning(self):
        self.notify.error('called exitNoFriendsWarning() on parent class')

    def enterActivateChat(self):
        self.notify.error('called enterActivateChat() on parent class')

    def exitActivateChat(self):
        self.notify.error('called exitActivateChat() on parent class')

    def enterOtherDialog(self):
        pass

    def exitOtherDialog(self):
        pass

    def enterChatMoreInfo(self):
        if self.chatMoreInfo == None:
            self.chatMoreInfo = SecretFriendsInfoPanel.SecretFriendsInfoPanel('secretFriendsInfoDone')
        self.chatMoreInfo.show()
        self.accept('secretFriendsInfoDone', self.__secretFriendsInfoDone)
        return

    def exitChatMoreInfo(self):
        self.chatMoreInfo.hide()
        self.ignore('secretFriendsInfoDone')

    def enterChatPrivacyPolicy(self):
        if self.chatPrivacyPolicy == None:
            self.chatPrivacyPolicy = PrivacyPolicyPanel.PrivacyPolicyPanel('privacyPolicyDone')
        self.chatPrivacyPolicy.show()
        self.accept('privacyPolicyDone', self.__privacyPolicyDone)
        return

    def exitChatPrivacyPolicy(self):
        cleanupDialog('privacyPolicyDialog')
        self.chatPrivacyPolicy = None
        self.ignore('privacyPolicyDone')
        return

    def enterSecretChatActivated(self):
        self.notify.error('called enterSecretChatActivated() on parent class')

    def exitSecretChatActivated(self):
        self.notify.error('called exitSecretChatActivated() on parent class')

    def enterProblemActivatingChat(self):
        self.notify.error('called enterProblemActivatingChat() on parent class')

    def exitProblemActivatingChat(self):
        self.notify.error('called exitProblemActivatingChat() on parent class')

    def enterTrueFriendTeaserPanel(self):
        self.notify.error('called enterTrueFriendTeaserPanel () on parent class')

    def exitTrueFriendTeaserPanel(self):
        self.notify.error('called exitTrueFriendTeaserPanel () on parent class')

    def __handleLeaveToPayCancel(self):
        self.fsm.request('mainMenu')

    def __secretFriendsInfoDone(self):
        self.fsm.request('activateChat')

    def __privacyPolicyDone(self):
        self.fsm.request('activateChat')
