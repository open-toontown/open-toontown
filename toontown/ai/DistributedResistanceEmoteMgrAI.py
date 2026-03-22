from direct.directnotify import DirectNotifyGlobal
from direct.distributed import DistributedObjectAI

class DistributedResistanceEmoteMgrAI(DistributedObjectAI.DistributedObjectAI):
    """Resistance emote ai implementation. This object sits in zone 9720 ('Talking in Your Sleep
    Voiceover Training' interior) and will activate the resistance emote for anyone who says
    'Do you need help?' to Whispering Willow during the promotion for Cashbot HQ."""

    notify = DirectNotifyGlobal.directNotify.newCategory(
        'DistributedResistanceEmoteMgrAI')
    
    def __init__(self, air):
        DistributedObjectAI.DistributedObjectAI.__init__(self, air)

    # do the event
    def addResistanceEmote(self):
        avId = self.air.getAvatarIdFromSender()
        av = self.air.doId2do.get(avId)
        if not av:
            DistributedResistanceEmoteMgrAI.notify.warning(
                'Tried to add resistance emote to av %s, but they left' % avId)
        else:
            DistributedResistanceEmoteMgrAI.notify.warning(
                'Activating resistance emote for av %s' % avId)
            av.setEmoteAccessId(15, 1)
            
