from toontown.building.DistributedElevatorInt import DistributedElevatorInt

class DistributedCogdoElevatorInt(DistributedElevatorInt):

    def _getDoorsClosedInfo(self):
        return ('cogdoInterior', 'cogdoInterior')
