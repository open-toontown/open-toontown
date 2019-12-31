

class TelemetryLimited:
    Sng = SerialNumGen()

    def __init__(self):
        self._telemetryLimiterId = self.Sng.next()
        self._limits = set()

    def getTelemetryLimiterId(self):
        return self._telemetryLimiterId

    def addTelemetryLimit(self, limit):
        self._limits.add(limit)

    def removeTelemetryLimit(self, limit):
        if limit in self._limits:
            self._limits.remove(limit)

    def enforceTelemetryLimits(self):
        for limit in self._limits:
            limit(self)
