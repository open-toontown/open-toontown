

class RingTrackGroup:

    def __init__(self, tracks, period, trackTOffsets = None, reverseFlag = 0, tOffset = 0.0):
        if trackTOffsets == None:
            trackTOffsets = [0] * len(tracks)
        self.tracks = tracks
        self.period = period
        self.trackTOffsets = trackTOffsets
        self.reverseFlag = reverseFlag
        self.tOffset = tOffset
        return
