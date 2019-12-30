from pandac.PandaModules import *
from . import CatalogItem
from toontown.toonbase import ToontownGlobals
from otp.otpbase import OTPLocalizer
from toontown.toonbase import TTLocalizer
bannedPhrases = [11009]

class CatalogChatItem(CatalogItem.CatalogItem):

    def makeNewItem(self, customIndex):
        self.customIndex = customIndex
        CatalogItem.CatalogItem.makeNewItem(self)

    def getPurchaseLimit(self):
        return 1

    def reachedPurchaseLimit(self, avatar):
        if self in avatar.onOrder or self in avatar.mailboxContents or self in avatar.onGiftOrder or self in avatar.awardMailboxContents or self in avatar.onAwardOrder:
            return 1
        return avatar.customMessages.count(self.customIndex) != 0

    def getTypeName(self):
        return TTLocalizer.ChatTypeName

    def getName(self):
        return TTLocalizer.ChatItemQuotes % OTPLocalizer.CustomSCStrings[self.customIndex]

    def getDisplayName(self):
        return OTPLocalizer.CustomSCStrings[self.customIndex]

    def recordPurchase(self, avatar, optional):
        if avatar.customMessages.count(self.customIndex) != 0:
            return ToontownGlobals.P_ReachedPurchaseLimit
        if len(avatar.customMessages) >= ToontownGlobals.MaxCustomMessages:
            if optional >= 0 and optional < len(avatar.customMessages):
                del avatar.customMessages[optional]
            if len(avatar.customMessages) >= ToontownGlobals.MaxCustomMessages:
                return ToontownGlobals.P_NoRoomForItem
        avatar.customMessages.append(self.customIndex)
        avatar.d_setCustomMessages(avatar.customMessages)
        return ToontownGlobals.P_ItemAvailable

    def getAcceptItemErrorText(self, retcode):
        if retcode == ToontownGlobals.P_ItemAvailable:
            return TTLocalizer.CatalogAcceptChat
        return CatalogItem.CatalogItem.getAcceptItemErrorText(self, retcode)

    def output(self, store = -1):
        return 'CatalogChatItem(%s%s)' % (self.customIndex, self.formatOptionalData(store))

    def compareTo(self, other):
        return self.customIndex - other.customIndex

    def getHashContents(self):
        return self.customIndex

    def getBasePrice(self):
        if self.customIndex >= 10000:
            return 150
        return 100

    def decodeDatagram(self, di, versionNumber, store):
        CatalogItem.CatalogItem.decodeDatagram(self, di, versionNumber, store)
        self.customIndex = di.getUint16()
        text = OTPLocalizer.CustomSCStrings[self.customIndex]

    def encodeDatagram(self, dg, store):
        CatalogItem.CatalogItem.encodeDatagram(self, dg, store)
        dg.addUint16(self.customIndex)

    def acceptItem(self, mailbox, index, callback):
        if len(base.localAvatar.customMessages) < ToontownGlobals.MaxCustomMessages:
            mailbox.acceptItem(self, index, callback)
        else:
            self.showMessagePickerOnAccept(mailbox, index, callback)

    def requestPurchase(self, phone, callback):
        if len(base.localAvatar.customMessages) < ToontownGlobals.MaxCustomMessages:
            CatalogItem.CatalogItem.requestPurchase(self, phone, callback)
        else:
            self.showMessagePicker(phone, callback)

    def showMessagePicker(self, phone, callback):
        self.phone = phone
        self.callback = callback
        from . import CatalogChatItemPicker
        self.messagePicker = CatalogChatItemPicker.CatalogChatItemPicker(self.__handlePickerDone, self.customIndex)
        self.messagePicker.show()

    def showMessagePickerOnAccept(self, mailbox, index, callback):
        self.mailbox = mailbox
        self.callback = callback
        self.index = index
        from . import CatalogChatItemPicker
        self.messagePicker = CatalogChatItemPicker.CatalogChatItemPicker(self.__handlePickerOnAccept, self.customIndex)
        self.messagePicker.show()

    def __handlePickerOnAccept(self, status, pickedMessage = None):
        print('Picker Status%s' % status)
        if status == 'pick':
            self.mailbox.acceptItem(self, self.index, self.callback, pickedMessage)
        else:
            print('picker canceled')
            self.callback(ToontownGlobals.P_UserCancelled, None, self.index)
        self.messagePicker.hide()
        self.messagePicker.destroy()
        del self.messagePicker
        del self.callback
        del self.mailbox
        return

    def __handlePickerDone(self, status, pickedMessage = None):
        if status == 'pick':
            CatalogItem.CatalogItem.requestPurchase(self, self.phone, self.callback, pickedMessage)
        self.messagePicker.hide()
        self.messagePicker.destroy()
        del self.messagePicker
        del self.callback
        del self.phone

    def getPicture(self, avatar):
        chatBalloon = loader.loadModel('phase_3/models/props/chatbox.bam')
        chatBalloon.find('**/top').setPos(1, 0, 5)
        chatBalloon.find('**/middle').setScale(1, 1, 3)
        frame = self.makeFrame()
        chatBalloon.reparentTo(frame)
        chatBalloon.setPos(-2.19, 0, -1.74)
        chatBalloon.setScale(0.4)
        self.hasPicture = True
        return (frame, None)


def getChatRange(fromIndex, toIndex, *otherRanges):
    list = []
    froms = [fromIndex]
    tos = [toIndex]
    i = 0
    while i < len(otherRanges):
        froms.append(otherRanges[i])
        tos.append(otherRanges[i + 1])
        i += 2

    for chatId in list(OTPLocalizer.CustomSCStrings.keys()):
        for fromIndex, toIndex in zip(froms, tos):
            if chatId >= fromIndex and chatId <= toIndex and chatId not in bannedPhrases:
                list.append(CatalogChatItem(chatId))

    return list
