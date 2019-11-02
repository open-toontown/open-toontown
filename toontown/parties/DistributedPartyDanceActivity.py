from toontown.parties import PartyGlobals
from toontown.parties.DistributedPartyDanceActivityBase import DistributedPartyDanceActivityBase
from toontown.toonbase import TTLocalizer

class DistributedPartyDanceActivity(DistributedPartyDanceActivityBase):
    notify = directNotify.newCategory('DistributedPartyDanceActivity')

    def __init__(self, cr):
        DistributedPartyDanceActivityBase.__init__(self, cr, PartyGlobals.ActivityIds.PartyDance, PartyGlobals.DancePatternToAnims)

    def getInstructions(self):
        return TTLocalizer.PartyDanceActivityInstructions

    def getTitle(self):
        return TTLocalizer.PartyDanceActivityTitle

    def load(self):
        DistributedPartyDanceActivityBase.load(self)
        parentGroup = self.danceFloor.find('**/discoBall_mesh')
        correctBall = self.danceFloor.find('**/discoBall_10')
        origBall = self.danceFloor.find('**/discoBall_mesh_orig')
        if not correctBall.isEmpty():
            numChildren = parentGroup.getNumChildren()
            for i in xrange(numChildren):
                child = parentGroup.getChild(i)
                if child != correctBall:
                    child.hide()
