from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.distributed.DistributedObjectGlobal import DistributedObjectGlobal

class ChatHandler(DistributedObjectGlobal):
    """
    The purpose of this class is to handle chat messages from the client to the
    uberdog to filter out unwanted words. Then send it through the server.
    """

    notify = directNotify.newCategory('ChatRouter')

    def sendChatMessage(self, message):
        """
        

        send a chat message to the uberdog

        Args:
            message (string): the message to send that was typed in by the user
        """
        self.sendUpdate('chatMessage', [message])

    def sendWhisperMessage(self, message, receiverAvId):
        """
        send a whisper message to the uberdog

        Args:
            message (string): the message to send that was typed in by the user
            receiverAvId (int): the avatar id of the person to send the message to
        """
        self.sendUpdate('whisperMessage', [message, receiverAvId])