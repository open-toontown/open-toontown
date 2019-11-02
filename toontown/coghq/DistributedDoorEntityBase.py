

def stubFunction(*args):
    pass


class LockBase:
    stateNames = ['off',
     'locking',
     'locked',
     'unlocking',
     'unlocked']
    stateDurations = [None,
     3.5,
     None,
     4.0,
     None]


class DistributedDoorEntityBase:
    stateNames = ['off',
     'opening',
     'open',
     'closing',
     'closed']
    stateDurations = [None,
     5.0,
     1.0,
     6.0,
     None]
