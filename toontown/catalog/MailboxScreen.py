from direct.directnotify.DirectNotifyGlobal import *
from direct.gui.DirectGui import *
from direct.showbase import DirectObject, PythonUtil
from pandac.PandaModules import *
from toontown.parties import PartyGlobals
from toontown.parties.InviteInfo import InviteInfoBase
from toontown.parties.PartyGlobals import InviteStatus
from toontown.parties.SimpleMailBase import SimpleMailBase
from toontown.toonbase import TTLocalizer, ToontownGlobals
from toontown.toontowngui import TTDialog
from toontown.toontowngui.TeaserPanel import TeaserPanel
from toontown.parties.InviteVisual import InviteVisual
from . import CatalogItem
from direct.showbase.PythonUtil import StackTrace

class MailboxScreen(DirectObject.DirectObject):
    notify = directNotify.newCategory('MailboxScreen')

    def __init__(self, mailbox, avatar, doneEvent = None):
        self.mailbox = mailbox
        self.avatar = avatar
        self.items = self.getItems()
        self.doneEvent = doneEvent
        self.itemIndex = 0
        self.itemPanel = None
        self.itemPicture = None
        self.ival = None
        self.itemText = None
        self.giftTag = None
        self.acceptingIndex = None
        self.numAtticAccepted = 0
        self.dialogBox = None
        self.load()
        self.hide()
        return

    def show(self):
        self.frame.show()
        self.__showCurrentItem()

    def hide(self):
        self.ignore('friendsListChanged')
        if hasattr(self, 'frame'):
            self.frame.hide()
        else:
            self.notify.warning('hide called, but frame is deleted, self.frame deleted in:')
            if hasattr(self, 'frameDelStackTrace'):
                print(self.frameDelStackTrace)
            self.notify.warning('current stackTrace =')
            print(StackTrace())
            self.notify.warning('crash averted, but root cause unknown')

    def load(self):
        self.accept('setMailboxContents-%s' % base.localAvatar.doId, self.__refreshItems)
        self.accept('setAwardMailboxContents-%s' % base.localAvatar.doId, self.__refreshItems)
        model = loader.loadModel('phase_5.5/models/gui/package_delivery_panel')
        background = model.find('**/bg')
        itemBoard = model.find('**/item_board')
        self.frame = DirectFrame(scale=1.1, relief=DGG.FLAT, frameSize=(-0.5,
         0.5,
         -0.45,
         -0.05), frameColor=(0.737, 0.573, 0.345, 1.0))
        self.background = DirectFrame(self.frame, image=background, image_scale=0.05, relief=None, pos=(0, 1, 0))
        self.itemBoard = DirectFrame(parent=self.frame, image=itemBoard, image_scale=0.05, image_color=(0.922, 0.922, 0.753, 1), relief=None, pos=(0, 1, 0))
        self.itemCountLabel = DirectLabel(parent=self.frame, relief=None, text=self.__getNumberOfItemsText(), text_wordwrap=16, pos=(0.0, 0.0, 0.7), scale=0.09)
        exitUp = model.find('**/bu_return_rollover')
        exitDown = model.find('**/bu_return_rollover')
        exitRollover = model.find('**/bu_return_rollover')
        exitUp.setP(-90)
        exitDown.setP(-90)
        exitRollover.setP(-90)
        self.DiscardButton = DirectButton(parent=self.frame, relief=None, image=(exitUp,
         exitDown,
         exitRollover,
         exitUp), pos=(-0.01, 1.0, -0.36), scale=0.048, text=('',
         TTLocalizer.MailBoxDiscard,
         TTLocalizer.MailBoxDiscard,
         ''), text_scale=1.0, text_pos=(0, -0.08), textMayChange=1, command=self.__makeDiscardInterface)
        gui2 = loader.loadModel('phase_3/models/gui/quit_button')
        self.quitButton = DirectButton(parent=self.frame, relief=None, image=(gui2.find('**/QuitBtn_UP'), gui2.find('**/QuitBtn_DN'), gui2.find('**/QuitBtn_RLVR')), pos=(0.5, 1.0, -0.42), scale=0.9, text=TTLocalizer.MailboxExitButton, text_font=ToontownGlobals.getSignFont(), text0_fg=(0.152, 0.75, 0.258, 1), text1_fg=(0.152, 0.75, 0.258, 1), text2_fg=(0.977, 0.816, 0.133, 1), text_scale=0.045, text_pos=(0, -0.01), command=self.__handleExit)
        self.gettingText = DirectLabel(parent=self.frame, relief=None, text='', text_wordwrap=10, pos=(0.0, 0.0, 0.32), scale=0.09)
        self.gettingText.hide()
        self.giftTagPanel = DirectLabel(parent=self.frame, relief=None, text='Gift TAG!!', text_wordwrap=16, pos=(0.0, 0.0, 0.01), scale=0.06)
        self.giftTagPanel.hide()
        self.itemText = DirectLabel(parent=self.frame, relief=None, text='', text_wordwrap=16, pos=(0.0, 0.0, -0.022), scale=0.07)
        self.itemText.hide()
        acceptUp = model.find('**/bu_check_up')
        acceptDown = model.find('**/bu_check_down')
        acceptRollover = model.find('**/bu_check_rollover')
        acceptUp.setP(-90)
        acceptDown.setP(-90)
        acceptRollover.setP(-90)
        self.acceptButton = DirectButton(parent=self.frame, relief=None, image=(acceptUp,
         acceptDown,
         acceptRollover,
         acceptUp), image3_color=(0.8, 0.8, 0.8, 0.6), pos=(-0.01, 1.0, -0.16), scale=0.048, text=('',
         TTLocalizer.MailboxAcceptButton,
         TTLocalizer.MailboxAcceptButton,
         ''), text_scale=1.0, text_pos=(0, -0.09), textMayChange=1, command=self.__handleAccept, state=DGG.DISABLED)
        nextUp = model.find('**/bu_next_up')
        nextUp.setP(-90)
        nextDown = model.find('**/bu_next_down')
        nextDown.setP(-90)
        nextRollover = model.find('**/bu_next_rollover')
        nextRollover.setP(-90)
        self.nextButton = DirectButton(parent=self.frame, relief=None, image=(nextUp,
         nextDown,
         nextRollover,
         nextUp), image3_color=(0.8, 0.8, 0.8, 0.6), pos=(0.31, 1.0, -0.26), scale=0.05, text=('',
         TTLocalizer.MailboxItemNext,
         TTLocalizer.MailboxItemNext,
         ''), text_scale=1, text_pos=(-0.2, 0.3), text_fg=(1, 1, 1, 1), text_shadow=(0, 0, 0, 1), textMayChange=0, command=self.__nextItem, state=DGG.DISABLED)
        prevUp = model.find('**/bu_previous_up')
        prevUp.setP(-90)
        prevDown = model.find('**/bu_previous_down')
        prevDown.setP(-90)
        prevRollover = model.find('**/bu_previous_rollover')
        prevRollover.setP(-90)
        self.prevButton = DirectButton(parent=self.frame, relief=None, image=(prevUp,
         prevDown,
         prevRollover,
         prevUp), pos=(-0.35, 1, -0.26), scale=0.05, image3_color=(0.8, 0.8, 0.8, 0.6), text=('',
         TTLocalizer.MailboxItemPrev,
         TTLocalizer.MailboxItemPrev,
         ''), text_scale=1, text_pos=(0, 0.3), text_fg=(1, 1, 1, 1), text_shadow=(0, 0, 0, 1), textMayChange=0, command=self.__prevItem, state=DGG.DISABLED)
        self.currentItem = None
        self.partyInviteVisual = InviteVisual(self.frame)
        self.partyInviteVisual.setScale(0.73)
        self.partyInviteVisual.setPos(0.0, 0.0, 0.48)
        self.partyInviteVisual.stash()
        if self.avatar:
            self.avatar.applyCheesyEffect(ToontownGlobals.CENormal)
        return

    def unload(self):
        if self.avatar:
            self.avatar.reconsiderCheesyEffect()
        self.__clearCurrentItem()
        if hasattr(self, 'frame'):
            self.frame.destroy()
            del self.frame
            self.frameDelStackTrace = StackTrace()
        else:
            self.notify.warning('unload, no self.frame')
        if hasattr(self, 'mailbox'):
            del self.mailbox
        else:
            self.notify.warning('unload, no self.mailbox')
        if self.dialogBox:
            self.dialogBox.cleanup()
            self.dialogBox = None
        for item in self.items:
            if isinstance(item, CatalogItem.CatalogItem):
                item.acceptItemCleanup()

        self.ignoreAll()
        return

    def justExit(self):
        self.__acceptExit()

    def __handleExit(self):
        if self.numAtticAccepted == 0:
            self.__acceptExit()
        elif self.numAtticAccepted == 1:
            self.dialogBox = TTDialog.TTDialog(style=TTDialog.Acknowledge, text=TTLocalizer.CatalogAcceptInAttic, text_wordwrap=15, command=self.__acceptExit)
            self.dialogBox.show()
        else:
            self.dialogBox = TTDialog.TTDialog(style=TTDialog.Acknowledge, text=TTLocalizer.CatalogAcceptInAtticP, text_wordwrap=15, command=self.__acceptExit)
            self.dialogBox.show()

    def __acceptExit(self, buttonValue = None):
        if hasattr(self, 'frame'):
            self.hide()
            self.unload()
            messenger.send(self.doneEvent)

    def __handleAccept(self):
        if base.config.GetBool('want-qa-regression', 0):
            self.notify.info('QA-REGRESSION: MAILBOX: Accept item')
        if self.acceptingIndex != None:
            return
        item = self.items[self.itemIndex]
        isAward = False
        if isinstance(item, CatalogItem.CatalogItem):
            isAward = item.isAward()
        if not base.cr.isPaid() and not (isinstance(item, InviteInfoBase) or isAward):
            TeaserPanel(pageName='clothing')
        else:
            self.acceptingIndex = self.itemIndex
            self.acceptButton['state'] = DGG.DISABLED
            self.__showCurrentItem()
            item = self.items[self.itemIndex]
            item.acceptItem(self.mailbox, self.acceptingIndex, self.__acceptItemCallback)
        return

    def __handleDiscard(self, buttonValue = None):
        if self.acceptingIndex != None:
            return
        elif buttonValue == -1:
            if self.dialogBox:
                self.dialogBox.cleanup()
            self.dialogBox = None
            self.__showCurrentItem()
        else:
            self.acceptingIndex = self.itemIndex
            self.acceptButton['state'] = DGG.DISABLED
            self.__showCurrentItem()
            item = self.items[self.itemIndex]
            item.discardItem(self.mailbox, self.acceptingIndex, self.__discardItemCallback)
        return

    def __discardItemCallback(self, retcode, item, index):
        if not hasattr(self, 'frame'):
            return
        if self.dialogBox:
            self.dialogBox.cleanup()
        self.dialogBox = None
        self.acceptingIndex = None
        self.__updateItems()
        if isinstance(item, InviteInfoBase):
            callback = self.__incIndexRemoveDialog
            self.dialogBox = TTDialog.TTDialog(style=TTDialog.Acknowledge, text=item.getDiscardItemErrorText(retcode), text_wordwrap=15, command=callback)
            self.dialogBox.show()
        return

    def __makeDiscardInterface(self):
        if self.itemIndex >= 0 and self.itemIndex < len(self.items):
            item = self.items[self.itemIndex]
            if isinstance(item, InviteInfoBase):
                itemText = TTLocalizer.MailBoxRejectVerify % self.getItemName(item)
                yesText = TTLocalizer.MailboxReject
            else:
                itemText = TTLocalizer.MailBoxDiscardVerify % self.getItemName(item)
                yesText = TTLocalizer.MailboxDiscard
            self.dialogBox = TTDialog.TTDialog(style=TTDialog.TwoChoiceCustom, text=itemText, text_wordwrap=15, command=self.__handleDiscard, buttonText=[yesText, TTLocalizer.MailboxLeave])
            self.dialogBox.show()

    def __acceptItemCallback(self, retcode, item, index):
        needtoUpdate = 0
        if self.acceptingIndex == None:
            needtoUpdate = 1
        if not hasattr(self, 'frame'):
            return
        if retcode == ToontownGlobals.P_UserCancelled:
            print('mailbox screen user canceled')
            self.acceptingIndex = None
            self.__updateItems()
            return
        if self.acceptingIndex != index:
            self.notify.warning('Got unexpected callback for index %s, expected %s.' % (index, self.acceptingIndex))
            return
        self.acceptingIndex = None
        if retcode < 0:
            self.notify.info('Could not take item %s: retcode %s' % (item, retcode))
            if retcode == ToontownGlobals.P_NoTrunk:
                self.dialogBox = TTDialog.TTDialog(style=TTDialog.Acknowledge, text=TTLocalizer.CatalogAcceptNoTrunk, text_wordwrap=15, command=self.__acceptError)
            else:
                self.dialogBox = TTDialog.TTDialog(style=TTDialog.TwoChoiceCustom, text=item.getAcceptItemErrorText(retcode), text_wordwrap=15, command=self.__handleDiscard, buttonText=[TTLocalizer.MailboxDiscard, TTLocalizer.MailboxLeave])
            self.dialogBox.show()
        elif hasattr(item, 'storedInAttic') and item.storedInAttic():
            self.numAtticAccepted += 1
            self.itemIndex += 1
            if needtoUpdate == 1:
                self.__updateItems()
        else:
            if isinstance(item, InviteInfoBase):
                self.__updateItems()
            callback = self.__incIndexRemoveDialog
            self.dialogBox = TTDialog.TTDialog(style=TTDialog.Acknowledge, text=item.getAcceptItemErrorText(retcode), text_wordwrap=15, command=callback)
            self.dialogBox.show()
        return

    def __acceptError(self, buttonValue = None):
        self.dialogBox.cleanup()
        self.dialogBox = None
        self.__showCurrentItem()
        return

    def __incIndexRemoveDialog(self, junk = 0):
        self.__incIndex()
        self.dialogBox.cleanup()
        self.dialogBox = None
        self.__showCurrentItem()
        return

    def __incIndex(self, junk = 0):
        self.itemIndex += 1

    def __acceptOk(self, index, buttonValue = None):
        self.acceptingIndex = None
        if self.dialogBox:
            self.dialogBox.cleanup()
            self.dialogBox = None
        self.items = self.getItems()
        if self.itemIndex > index or self.itemIndex >= len(self.items):
            print('adjusting item index -1')
            self.itemIndex -= 1
        if len(self.items) < 1:
            self.__handleExit()
            return
        self.itemCountLabel['text'] = (self.__getNumberOfItemsText(),)
        self.__showCurrentItem()
        return

    def __refreshItems(self):
        self.acceptingIndex = None
        self.__updateItems()
        return

    def __updateItems(self):
        if self.dialogBox:
            self.dialogBox.cleanup()
            self.dialogBox = None
        self.items = self.getItems()
        if self.itemIndex >= len(self.items):
            print('adjusting item index -1')
            self.itemIndex = len(self.items) - 1
        if len(self.items) == 0:
            print('exiting due to lack of items')
            self.__handleExit()
            return
        self.itemCountLabel['text'] = (self.__getNumberOfItemsText(),)
        self.__showCurrentItem()
        return

    def __getNumberOfItemsText(self):
        if len(self.items) == 1:
            return TTLocalizer.MailboxOneItem
        else:
            return TTLocalizer.MailboxNumberOfItems % len(self.items)

    def __clearCurrentItem(self):
        if self.itemPanel:
            self.itemPanel.destroy()
            self.itemPanel = None
        if self.ival:
            self.ival.finish()
            self.ival = None
        if not self.gettingText.isEmpty():
            self.gettingText.hide()
        if not self.itemText.isEmpty():
            self.itemText.hide()
        if not self.giftTagPanel.isEmpty():
            self.giftTagPanel.hide()
        if not self.acceptButton.isEmpty():
            self.acceptButton['state'] = DGG.DISABLED
        if self.currentItem:
            if isinstance(self.currentItem, CatalogItem.CatalogItem):
                self.currentItem.cleanupPicture()
            self.currentItem = None
        return

    def checkFamily(self, doId):
        for familyMember in base.cr.avList:
            if familyMember.id == doId:
                return familyMember

        return None

    def __showCurrentItem(self):
        self.__clearCurrentItem()
        if len(self.items) < 1:
            self.__handleExit()
            return
        self.partyInviteVisual.stash()
        if self.itemIndex + 1 > len(self.items):
            self.itemIndex = len(self.items) - 1
        item = self.items[self.itemIndex]
        if self.itemIndex == self.acceptingIndex:
            self.gettingText['text'] = TTLocalizer.MailboxGettingItem % self.getItemName(item)
            self.gettingText.show()
            return
        self.itemText['text'] = self.getItemName(item)
        self.currentItem = item
        if isinstance(item, CatalogItem.CatalogItem):
            self.acceptButton['text'] = ('',
             TTLocalizer.MailboxAcceptButton,
             TTLocalizer.MailboxAcceptButton,
             '')
            self.DiscardButton['text'] = ('',
             TTLocalizer.MailBoxDiscard,
             TTLocalizer.MailBoxDiscard,
             '')
            if item.isAward():
                self.giftTagPanel['text'] = TTLocalizer.SpecialEventMailboxStrings[item.specialEventId]
            elif item.giftTag != None:
                nameOfSender = self.getSenderName(item.giftTag)
                if item.giftCode == ToontownGlobals.GIFT_RAT:
                    self.giftTagPanel['text'] = TTLocalizer.CatalogAcceptRATBeans
                elif item.giftCode == ToontownGlobals.GIFT_partyrefund:
                    self.giftTagPanel['text'] = TTLocalizer.CatalogAcceptPartyRefund
                else:
                    self.giftTagPanel['text'] = TTLocalizer.MailboxGiftTag % nameOfSender
            else:
                self.giftTagPanel['text'] = ''
            self.itemPanel, self.ival = item.getPicture(base.localAvatar)
        elif isinstance(item, SimpleMailBase):
            self.acceptButton['text'] = ('',
             TTLocalizer.MailboxAcceptButton,
             TTLocalizer.MailboxAcceptButton,
             '')
            self.DiscardButton['text'] = ('',
             TTLocalizer.MailBoxDiscard,
             TTLocalizer.MailBoxDiscard,
             '')
            senderId = item.senderId
            nameOfSender = self.getSenderName(senderId)
            self.giftTagPanel['text'] = TTLocalizer.MailFromTag % nameOfSender
            self.itemText['text'] = item.body
        elif isinstance(item, InviteInfoBase):
            self.acceptButton['text'] = ('',
             TTLocalizer.MailboxAcceptInvite,
             TTLocalizer.MailboxAcceptInvite,
             '')
            self.DiscardButton['text'] = ('',
             TTLocalizer.MailBoxRejectInvite,
             TTLocalizer.MailBoxRejectInvite,
             '')
            partyInfo = None
            for party in self.avatar.partiesInvitedTo:
                if party.partyId == item.partyId:
                    partyInfo = party
                    break
            else:
                MailboxScreen.notify.error('Unable to find party with id %d to match invitation %s' % (item.partyId, item))

            if self.mailbox:
                if item.status == PartyGlobals.InviteStatus.NotRead:
                    self.mailbox.sendInviteReadButNotReplied(item.inviteKey)
            senderId = partyInfo.hostId
            nameOfSender = self.getSenderName(senderId)
            self.giftTagPanel['text'] = ''
            self.itemText['text'] = ''
            self.partyInviteVisual.updateInvitation(nameOfSender, partyInfo)
            self.partyInviteVisual.unstash()
            self.itemPanel = None
            self.ival = None
        else:
            self.acceptButton['text'] = ('',
             TTLocalizer.MailboxAcceptButton,
             TTLocalizer.MailboxAcceptButton,
             '')
            self.DiscardButton['text'] = ('',
             TTLocalizer.MailBoxDiscard,
             TTLocalizer.MailBoxDiscard,
             '')
            self.giftTagPanel['text'] = ' '
            self.itemPanel = None
            self.ival = None
        self.itemText.show()
        self.giftTagPanel.show()
        if self.itemPanel and item.getTypeName() != TTLocalizer.ChatTypeName:
            self.itemPanel.reparentTo(self.itemBoard, -1)
            self.itemPanel.setPos(0, 0, 0.4)
            self.itemPanel.setScale(0.21)
            self.itemText['text_wordwrap'] = 16
            self.itemText.setPos(0.0, 0.0, 0.075)
        elif isinstance(item, CatalogItem.CatalogItem) and item.getTypeName() == TTLocalizer.ChatTypeName:
            self.itemPanel.reparentTo(self.itemBoard, -1)
            self.itemPanel.setPos(0, 0, 0.35)
            self.itemPanel.setScale(0.21)
            self.itemText['text_wordwrap'] = 10
            self.itemText.setPos(0, 0, 0.3)
        else:
            self.itemText.setPos(0, 0, 0.3)
        if self.ival:
            self.ival.loop()
        if self.acceptingIndex == None:
            self.acceptButton['state'] = DGG.NORMAL
        if self.itemIndex > 0:
            self.prevButton['state'] = DGG.NORMAL
        else:
            self.prevButton['state'] = DGG.DISABLED
        if self.itemIndex + 1 < len(self.items):
            self.nextButton['state'] = DGG.NORMAL
        else:
            self.nextButton['state'] = DGG.DISABLED
        return

    def __nextItem(self):
        messenger.send('wakeup')
        if self.itemIndex + 1 < len(self.items):
            self.itemIndex += 1
            self.__showCurrentItem()

    def __prevItem(self):
        messenger.send('wakeup')
        if self.itemIndex > 0:
            self.itemIndex -= 1
            self.__showCurrentItem()

    def getItemName(self, item):
        if isinstance(item, CatalogItem.CatalogItem):
            return item.getName()
        elif isinstance(item, str):
            return TTLocalizer.MailSimpleMail
        elif isinstance(item, InviteInfoBase):
            return TTLocalizer.InviteInvitation
        else:
            return ''

    def getItems(self):
        result = []
        result = self.avatar.awardMailboxContents[:]
        result += self.avatar.mailboxContents[:]
        if self.avatar.mail:
            result += self.avatar.mail
        mailboxInvites = self.avatar.getInvitesToShowInMailbox()
        if mailboxInvites:
            result += mailboxInvites
        return result

    def getNumberOfAwardItems(self):
        result = 0
        for item in self.items:
            if isinstance(item, CatalogItem.CatalogItem) and item.specialEventId > 0:
                result += 1
            else:
                break

        return result

    def getSenderName(self, avId):
        sender = base.cr.identifyFriend(avId)
        nameOfSender = ''
        if sender:
            nameOfSender = sender.getName()
        else:
            sender = self.checkFamily(avId)
            if sender:
                nameOfSender = sender.name
            elif hasattr(base.cr, 'playerFriendsManager'):
                sender = base.cr.playerFriendsManager.getAvHandleFromId(avId)
                if sender:
                    nameOfSender = sender.getName()
        if not sender:
            nameOfSender = TTLocalizer.MailboxGiftTagAnonymous
            if hasattr(base.cr, 'playerFriendsManager'):
                base.cr.playerFriendsManager.requestAvatarInfo(avId)
                self.accept('friendsListChanged', self.__showCurrentItem)
        return nameOfSender
