from toontown.parties import PartyGlobals
from toontown.parties.DistributedPartyJukeboxActivityBase import DistributedPartyJukeboxActivityBase


class DistributedPartyJukeboxActivity(DistributedPartyJukeboxActivityBase):
    notify = directNotify.newCategory('DistributedPartyJukeboxActivity')

    def __init__(self, cr):
        DistributedPartyJukeboxActivityBase.__init__(self, cr, PartyGlobals.ActivityIds.PartyJukebox, PartyGlobals.PhaseToMusicData)
