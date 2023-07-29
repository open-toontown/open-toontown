from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.distributed.DistributedObjectGlobalUD import DistributedObjectGlobalUD
from toontown.chat.TTWhiteList import TTWhiteList

whiteList = TTWhiteList()

class ChatHandlerUD(DistributedObjectGlobalUD):
    """
    The purpose of this class is to handle chat messages from the client to the
    uberdog to filter out unwanted words. Then send it through the server.
    """
    notify = directNotify.newCategory('ChatRouterUD')

    def filterWhitelist(self, message):
        """

        this function filters out words that are not in the whitelist

        Args:
            message (string): the original message to filter

        Returns:
            mods (string): the filtered message
        """
        words = message.split(' ')
        offset = 0
        mods = []

        for word in words:
            if not whiteList.isWord(word):
                mods.append((offset, offset + len(word) - 1))

            offset += len(word) + 1

        return mods

    def chatMessage(self, message):
        """
        send a chat message through the server

        Args:
            message (string): the message to send that was typed in by the user
        """
        avId = self.air.getAvatarIdFromSender()

        if not avId:
            return

        channel = avId

        mods = self.filterWhitelist(message)

        do = self.air.dclassesByName['DistributedPlayerUD']
        args = [avId, 0, '', message, mods, 0]
        datagram = do.aiFormatUpdate('setTalk', avId, channel, self.air.ourChannel, args)
        self.air.send(datagram)

    def whisperMessage(self, message, receiverAvId):
        """
        send a whisper message through the server
        
        Args:
            message (string): the message to send that was typed in by the user
            receiverAvId (int): the avatar id of the person to send the message to
        """
        avId = self.air.getAvatarIdFromSender()

        if not avId:
            return

        mods = self.filterWhitelist(message)

        do = self.air.dclassesByName['DistributedPlayerUD']
        args = [avId, 0, '', message, mods, 0]
        datagram = do.aiFormatUpdate('setTalkWhisper', receiverAvId, receiverAvId, self.air.ourChannel, args)
        self.air.send(datagram)