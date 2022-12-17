from direct.distributed.ClockDelta import *

class Racer(object):
    def __init__(self,race,air,avId,zoneId):

        self.race=race
        self.air=air
        self.avId=avId
        self.zoneId=zoneId
        
        self.avatar=air.doId2do[avId]
        self.avatar.takeOutKart(zoneId)

        self.kart=self.avatar.kart

        #race necessities
        self.lapT=0
        self.times=[]
        self.totalTime = 0
        self.maxLap=0
        self.hasGag=False
        self.gagType=0
        self.startingPlace=None
        self.baseTime=0

        #racer State
        self.finished=False
        self.exited=False
        self.anvilTarget=False

        #in case of disconnect
        self.exitEvent=self.air.getAvatarExitEvent(avId)
        self.race.accept(self.exitEvent,race.unexpectedExit,extraArgs=[avId])

    def setLapT(self,numLaps,lapT,timestamp):
        self.lapT=numLaps + lapT
        if(numLaps>self.maxLap):
            lapTime = globalClockDelta.networkToLocalTime(timestamp) - self.baseTime
            self.maxLap=numLaps
            self.times.append(lapTime - self.totalTime)
            self.totalTime = lapTime
