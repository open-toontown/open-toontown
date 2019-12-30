from pandac.PandaModules import AudioSound
from direct.interval.SoundInterval import SoundInterval

class CogdoGameSfx:

    def __init__(self, audioSound, audioMgr, source = None):
        self._audioSound = audioSound
        self._audioMgr = audioMgr
        self._source = source

    def destroy(self):
        self._audioMgr.removeSound(self._audioSound)
        del self._audioSound
        del self._audioMgr
        del self._source

    def getAudioSound(self):
        return self._audioSound

    def play(self, loop = False, playRate = 1.0, volume = 1.0, source = None):
        if source is None:
            source = self._source
        self._audioMgr.playSound(self._audioSound, loop=loop, source=source, playRate=playRate, volume=volume)
        return

    def loop(self, playRate = 1.0, volume = 1.0, source = None):
        if source is None:
            source = self._source
        self.play(loop=True, source=source, playRate=playRate, volume=volume)
        return

    def stop(self):
        self._audioMgr.stopSound(self._audioSound)


class CogdoGameAudioManager:
    notify = directNotify.newCategory('CogdoGameAudioManager')

    def __init__(self, musicFiles, sfxFiles, listener, cutoff = 75):
        self._sfxFiles = sfxFiles
        self._listener = listener
        self._cutoff = cutoff
        self.currentMusic = None
        self._music = {}
        for name, filePath in list(musicFiles.items()):
            self._music[name] = base.loader.loadMusic(filePath)

        self._audioSounds = []
        self._soundIvals = {}
        base.cogdoGameAudioMgr = self
        return

    def destroy(self):
        del base.cogdoGameAudioMgr
        self.stopAll()
        self.currentMusic = None
        del self.currentMusic
        self._music.clear()
        del self._sfxFiles
        del self._audioSounds
        return

    def stopMusic(self):
        if self.currentMusic is not None:
            self.currentMusic.stop()
        return

    def playMusic(self, name, loop = True, swap = False):
        time = 0.0
        if self.currentMusic is not None:
            if swap:
                time = self.currentMusic.getTime()
            self.stopMusic()
        self.currentMusic = self._music[name]
        self.currentMusic.setTime(time)
        self.currentMusic.setLoop(loop)
        self.currentMusic.play()
        return

    def createSfx(self, name, source = None):
        sound = loader.loadSfx(self._sfxFiles[name])
        self._audioSounds.append(sound)
        gameSfx = CogdoGameSfx(sound, self, source)
        return gameSfx

    def removeSound(self, audioSound):
        self._audioSounds.remove(audioSound)

    def _cleanupSoundIval(self, audioSound):
        if audioSound in self._soundIvals:
            ival = self._soundIvals[audioSound]
            if ival.isPlaying():
                ival.finish()
            del self._soundIvals[audioSound]

    def createSfxIval(self, sfxName, volume = 1.0, duration = 0.0, startTime = 0.0, source = None, cutoff = None):
        sound = loader.loadSfx(self._sfxFiles[sfxName])
        self._audioSounds.append(sound)
        return self._createSoundIval(sound, volume=volume, startTime=startTime, duration=duration, source=source, cutoff=cutoff)

    def _createSoundIval(self, audioSound, volume = 1.0, duration = 0.0, startTime = 0.0, source = None, register = False, cutoff = None):
        if cutoff == None:
            cutoff = self._cutoff
        ival = SoundInterval(audioSound, node=source, duration=duration, startTime=startTime, cutOff=cutoff, seamlessLoop=True, listenerNode=self._listener)
        return ival

    def playSound(self, audioSound, loop = False, source = None, playRate = 1.0, volume = 1.0):
        audioSound.setPlayRate(playRate)
        if source is not None and loop:
            self._cleanupSoundIval(audioSound)
            ival = self._createSoundIval(audioSound, volume=volume, source=source)
            self._soundIvals[audioSound] = ival
            ival.loop()
        else:
            base.playSfx(audioSound, looping=loop, node=source, volume=volume, listener=self._listener, cutoff=self._cutoff)
        return

    def stopSound(self, audioSound):
        if audioSound in self._soundIvals:
            self._cleanupSoundIval(audioSound)
        elif audioSound.status() == AudioSound.PLAYING:
            audioSound.stop()

    def stopAllSfx(self):
        for audioSound in self._audioSounds:
            self.stopSound(audioSound)

    def stopAll(self):
        self.stopMusic()
        self.stopAllSfx()
