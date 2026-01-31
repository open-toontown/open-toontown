import random
from panda3d.core import Point3, Vec3
from panda3d.toontown import DNADoor
from direct.interval.IntervalGlobal import *

from direct.directnotify import DirectNotifyGlobal
from direct.distributed import DistributedObject
from . import ToonInteriorColors
from toontown.hood import ZoneUtil
from toontown.suit import SuitDNA
from toontown.suit import Suit
from toontown.quest import QuestParser


class DistributedTutorialInterior(DistributedObject.DistributedObject):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedTutorialInterior')

    def announceGenerate(self):
        DistributedObject.DistributedObject.announceGenerate(self)
        self.setup()

    def disable(self):
        self.interior.removeNode()
        del self.interior
        self.street.removeNode()
        del self.street
        self.sky.removeNode()
        del self.sky
        self.mickeyMovie.cleanup()
        del self.mickeyMovie
        self.suitWalkTrack.finish()
        del self.suitWalkTrack
        self.suit.delete()
        del self.suit
        self.ignore("enterTutotialInterior")
        DistributedObject.DistributedObject.disable(self)

    def randomDNAItem(self, category, findFunc):
        codeCount = self.dnaStore.getNumCatalogCodes(category)
        index = self.randomGenerator.randint(0, codeCount - 1)
        code = self.dnaStore.getCatalogCode(category, index)
        # findFunc will probably be findNode or findTexture
        return findFunc(code)

    def replaceRandomInModel(self, model):
        """Replace named nodes with random items.
        Here are the name     Here is
        prefixes that are     what they
        affected:             do:

        random_mox_            change the Model Only.
        random_mcx_            change the Model and the Color.
        random_mrx_            change the Model and Recurse.
        random_tox_            change the Texture Only.
        random_tcx_            change the Texture and the Color.

        x is simply a uniquifying integer because Multigen will not
        let you have multiple nodes with the same name

        """
        baseTag = "random_"
        npc = model.findAllMatches("**/" + baseTag + "???_*")
        for i in range(npc.getNumPaths()):
            np = npc.getPath(i)
            name = np.getName()

            b = len(baseTag)
            category = name[b + 4:]
            key1 = name[b]
            key2 = name[b + 1]

            assert (key1 in ["m", "t"])
            assert (key2 in ["c", "o", "r"])
            if key1 == "m":
                # ...model.
                model = self.randomDNAItem(category, self.dnaStore.findNode)
                assert (not model.isEmpty())
                newNP = model.copyTo(np)
                # room has collisions already: remove collisions from models
                c = render.findAllMatches('**/collision')
                c.stash()
                if key2 == "r":
                    self.replaceRandomInModel(newNP)
            elif key1 == "t":
                # ...texture.
                texture = self.randomDNAItem(category, self.dnaStore.findTexture)
                assert (texture)
                np.setTexture(texture, 100)
                newNP = np
            if key2 == "c":
                if (category == "TI_wallpaper") or (category == "TI_wallpaper_border"):
                    self.randomGenerator.seed(self.zoneId)
                    newNP.setColorScale(
                        self.randomGenerator.choice(self.colors[category]))
                else:
                    newNP.setColorScale(
                        self.randomGenerator.choice(self.colors[category]))

    def setup(self):
        self.dnaStore = base.cr.playGame.dnaStore
        self.randomGenerator = random.Random()

        # The math here is a little arbitrary.  I'm trying to get a
        # substantially different seed for each zondId, even on the
        # same street.  But we don't want to weigh to much on the
        # block number, because we want the same block number on
        # different streets to be different.
        # Here we use the block number and a little of the branchId:
        # seedX=self.zoneId&0x00ff
        # Here we're using only the branchId:
        # seedY=self.zoneId/100
        # Here we're using only the block number:
        # seedZ=256-int(self.block)

        self.randomGenerator.seed(self.zoneId)

        self.interior = loader.loadModel("phase_3.5/models/modules/toon_interior_tutorial")
        self.interior.reparentTo(base.render)
        node = loader.loadDNAFile(self.cr.playGame.hood.dnaStore, "phase_3.5/dna/tutorial_street.dna")
        self.street = base.render.attachNewNode(node)
        self.street.flattenMedium()
        self.street.setPosHpr(-17, 42, -0.5, 180, 0, 0)
        # Get rid of the building we are in
        self.street.find("**/tb2:toon_landmark_TT_A1_DNARoot").stash()
        # Get rid of the flashing doors on the HQ building
        self.street.find("**/tb1:toon_landmark_hqTT_DNARoot/**/door_flat_0").stash()
        # Get rid of collisions because we do not need them and they get in the way
        self.street.findAllMatches("**/+CollisionNode").stash()
        self.skyFile = "phase_3.5/models/props/TT_sky"
        self.sky = loader.loadModel(self.skyFile)
        self.sky.setScale(0.8)
        # Parent the sky to our camera, the task will counter rotate it
        self.sky.reparentTo(base.render)
        # Turn off depth tests on the sky because as the cloud layers interpenetrate
        # we do not want to see the polys cutoff. Since there is nothing behing them
        # we can get away with this.
        self.sky.setDepthTest(0)
        self.sky.setDepthWrite(0)
        self.sky.setBin("background", 100)
        # Make sure they are drawn in the correct order in the hierarchy
        # The sky should be first, then the clouds
        self.sky.find("**/Sky").reparentTo(self.sky, -1)

        # Load a color dictionary for this hood:
        hoodId = ZoneUtil.getCanonicalHoodId(self.zoneId)
        self.colors = ToonInteriorColors.colors[hoodId]
        # Replace all the "random_xxx_" nodes:
        self.replaceRandomInModel(self.interior)

        # Door:
        doorModelName = "door_double_round_ul"  # hack  zzzzzzz
        # Switch leaning of the door:
        if doorModelName[-1:] == "r":
            doorModelName = doorModelName[:-1] + "l"
        else:
            doorModelName = doorModelName[:-1] + "r"
        door = self.dnaStore.findNode(doorModelName)
        # Determine where should we put the door:
        door_origin = base.render.find("**/door_origin;+s")
        doorNP = door.copyTo(door_origin)
        assert (not doorNP.isEmpty())
        assert (not door_origin.isEmpty())
        # The rooms are too small for doors:
        door_origin.setScale(0.8, 0.8, 0.8)
        # Move the origin away from the wall so it does not shimmer
        # We do this instead of decals
        door_origin.setPos(door_origin, 0, -0.025, 0)
        color = self.randomGenerator.choice(self.colors["TI_door"])
        DNADoor.setupDoor(doorNP,
                          self.interior, door_origin,
                          self.dnaStore,
                          str(self.block), color)
        # Setting the wallpaper texture with a priority overrides
        # the door texture, if it's decalled.  So, we're going to
        # move it out from the decal, and float it in front of
        # the wall:
        doorFrame = doorNP.find("door_*_flat")
        doorFrame.wrtReparentTo(self.interior)
        doorFrame.setColor(color)

        del self.colors
        del self.dnaStore
        del self.randomGenerator

        # Get rid of any transitions and extra nodes
        self.interior.flattenMedium()

        # Ok, this is a hack, but I'm tired of this freakin tutorial.
        # The problem is the interior must be created first so the npc can find the origin
        # of where to stand, but in this case the npc must be created first so the tutorial
        # can get a handle on him. Instead, I'll let the npc be created first which means
        # he will not find his origin. We'll just do that work here again.
        npcOrigin = self.interior.find(f"**/npc_origin_{self.npc.posIndex}")
        # Now he's no longer parented to render, but no one minds.
        if not npcOrigin.isEmpty():
            self.npc.reparentTo(npcOrigin)
            self.npc.clearMat()

        self.createSuit()

        self.mickeyMovie = QuestParser.NPCMoviePlayer("tutorial_mickey", base.localAvatar, self.npc)
        place = base.cr.playGame.getPlace()
        if place and hasattr(place, 'fsm') and place.fsm.getCurrentState().getName():
            self.notify.info('Tutorial movie: Place ready.')
            self.playMovie()
        else:
            self.notify.info(f'Tutorial movie: Waiting for place={place}, has fsm={hasattr(place, "fsm")}')
            if hasattr(place, 'fsm'):
                self.notify.info(f'Tutorial movie: place state={place.fsm.getCurrentState().getName()}')
            self.acceptOnce('enterTutorialInterior', self.playMovie)

    def playMovie(self):
        self.notify.info('Tutorial movie: Play.')
        self.mickeyMovie.play()

    def createSuit(self):
        # Create a suit
        self.suit = Suit.Suit()
        suitDNA = SuitDNA.SuitDNA()
        suitDNA.newSuit('f')
        self.suit.setDNA(suitDNA)
        self.suit.loop('neutral')
        self.suit.setPosHpr(-20, 8, 0, 0, 0, 0)
        self.suit.reparentTo(self.interior)

        self.suitWalkTrack = Sequence(
            self.suit.hprInterval(0.1, Vec3(0, 0, 0)),
            Func(self.suit.loop, 'walk'),
            self.suit.posInterval(2, Point3(-20, 20, 0)),
            Func(self.suit.loop, 'neutral'),
            Wait(1.0),
            self.suit.hprInterval(0.1, Vec3(180, 0, 0)),
            Func(self.suit.loop, 'walk'),
            self.suit.posInterval(2, Point3(-20, 10, 0)),
            Func(self.suit.loop, 'neutral'),
            Wait(1.0),
        )
        self.suitWalkTrack.loop()

    def setZoneIdAndBlock(self, zoneId, block):
        self.zoneId = zoneId
        self.block = block

    def setTutorialNpcId(self, npcId):
        self.npcId = npcId
        self.npc = self.cr.doId2do[npcId]
