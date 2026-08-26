from toontown.parties.DistributedPartyJukeboxActivityBase import DistributedPartyJukeboxActivityBase
from toontown.parties import PartyGlobals

class DistributedPartyValentineJukebox40Activity(DistributedPartyJukeboxActivityBase):
    notify = directNotify.newCategory('DistributedPartyValentineJukebox40Activity')

    def __init__(self, cr):
        DistributedPartyJukeboxActivityBase.__init__(self, cr, PartyGlobals.ActivityIds.PartyValentineJukebox40, PartyGlobals.PhaseToMusicData40)

    def load(self):
        DistributedPartyJukeboxActivityBase.load(self)
        newTexture = loader.loadTexture('phase_13/maps/tt_t_ara_pty_jukeboxValentineB.jpg', 'phase_13/maps/tt_t_ara_pty_jukeboxValentineB_a.rgb')
        case = self.jukebox.find('**/jukeboxGlass')
        if not case.isEmpty():
            case.setTexture(newTexture, 1)
        body = self.jukebox.find('**/jukeboxBody')
        if not body.isEmpty():
            body.setTexture(newTexture, 1)
