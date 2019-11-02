from toontown.parties import PartyGlobals
from toontown.parties.DistributedPartyDanceActivityBase import DistributedPartyDanceActivityBase
from toontown.toonbase import TTLocalizer

class DistributedPartyDance20Activity(DistributedPartyDanceActivityBase):
    notify = directNotify.newCategory('DistributedPartyDanceActivity')

    def __init__(self, cr):
        DistributedPartyDanceActivityBase.__init__(self, cr, PartyGlobals.ActivityIds.PartyDance20, PartyGlobals.DancePatternToAnims20)

    def getInstructions(self):
        return TTLocalizer.PartyDanceActivity20Instructions

    def getTitle(self):
        return TTLocalizer.PartyDanceActivity20Title

    def load(self):
        DistributedPartyDanceActivityBase.load(self)
        parentGroup = self.danceFloor.find('**/discoBall_mesh')
        correctBall = self.danceFloor.find('**/discoBall_20')
        if not correctBall.isEmpty():
            numChildren = parentGroup.getNumChildren()
            for i in xrange(numChildren):
                child = parentGroup.getChild(i)
                if child != correctBall:
                    child.hide()
