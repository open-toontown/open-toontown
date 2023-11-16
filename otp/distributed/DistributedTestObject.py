from direct.distributed import DistributedObject


class DistributedTestObject(DistributedObject.DistributedObject):

    def setRequiredField(self, r):
        self.requiredField = r

    def setB(self, B):
        self.B = B

    def setBA(self, BA):
        self.BA = BA

    def setBO(self, BO):
        self.BO = BO

    def setBR(self, BR):
        self.BR = BR

    def setBRA(self, BRA):
        self.BRA = BRA

    def setBRO(self, BRO):
        self.BRO = BRO

    def setBROA(self, BROA):
        self.BROA = BROA

    def gotNonReqThatWasntSet(self):
        for field in ('B', 'BA', 'BO', 'BR', 'BRA', 'BRO', 'BROA'):
            if hasattr(self, field):
                return True

        return False
