from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectGlobalUD import DistributedObjectGlobalUD
from direct.distributed.PyDatagram import *

class AstronLoginManagerUD(DistributedObjectGlobalUD):
    notify = DirectNotifyGlobal.directNotify.newCategory('AstronLoginManagerUD')

    def requestLogin(self, playToken):
        # TODO SET THIS UP PROPERLY.
        # AT THE MOMENT EVERYTHING IS HARDCODED
        # THIS IS JUST TO GET TO THE PICK A TOON SCREEN

        # get the sender
        sender = self.air.getMsgSender()

        # add connection to account channel
        datagram = PyDatagram()
        datagram.addServerHeader(sender, self.air.ourChannel, CLIENTAGENT_OPEN_CHANNEL)
        datagram.addChannel(self.GetAccountConnectionChannel(1000000000))
        self.air.send(datagram)

        # set sender channel to represent account affiliation
        datagram = PyDatagram()
        datagram.addServerHeader(sender, self.air.ourChannel, CLIENTAGENT_SET_CLIENT_ID)
        datagram.addChannel(1000000000 << 32) # accountId is in high 32 bits, 0 in low (no avatar).
        self.air.send(datagram)

        # set client state to established, thus un-sandboxing the sender
        self.air.setClientState(sender, 2)

        # send dummy login response
        import json
        a = json.dumps({})
        self.sendUpdateToChannel(sender, 'loginResponse', [a])
