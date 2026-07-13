"""Client-side task automation (optional dev tooling).

Registers companion autoers via task_autoer_globals. The full autoer bundle sets
those references after instantiating building/gag/boss helpers.

Quest choice UI sends a flat [questId, rewardId, toNpcId, ...] list; this module
auto-picks a non-optional task when possible (compatible with want-random-task-system).
"""
import traceback
import types
from collections import deque

from direct.directnotify import DirectNotifyGlobal
from direct.gui.DirectGui import DGG, DirectFrame, DirectLabel
from panda3d.core import TextNode

from toontown.quest import task_autoer_globals as TAG

notify = DirectNotifyGlobal.directNotify.newCategory('TaskAutoer')

from direct.interval.IntervalGlobal import *
from toontown.toon import DistributedNPCToon
from toontown.safezone import Playground
from toontown.battle import SuitBattleGlobals
from toontown.building import DistributedBuilding
from toontown.battle import DistributedBattleBldg
from toontown.suit import SuitDNA
from toontown.quest import Quests
from toontown.quest import QuestBookPoster
from toontown.toonbase import TTLocalizer
from toontown.toonbase import ToontownGlobals
from toontown.hood import ZoneUtil
from toontown.toon import ToonHead
from toontown.building import DistributedDoor
from toontown.safezone import DistributedPartyGate
from toontown.safezone import DistributedTrolley
from toontown.toon import DistributedNPCFisherman
from toontown.toon import DistributedNPCPartyPerson
from toontown.shtiker import PurchaseManager
from toontown.minigame import DistributedMinigame
from toontown.estate import Estate
from toontown.estate import House

HQZONES=[10000,11000,12000,13000]
        
class TaskAutoer:
    oldTeleportInPlayground=Playground.Playground.exitTeleportIn
    #oldBattleBldg=DistributedBattleBldg.DistributedBattleBldg.__init__
    #oldBuildingGenerate=DistributedBuilding.DistributedBuilding.generate
    #oldEnterToon=DistributedBuilding.DistributedBuilding.enterToon
    oldAnnounceGenerate1=DistributedMinigame.DistributedMinigame.announceGenerate
    oldAnnounceGenerate2=PurchaseManager.PurchaseManager.announceGenerate
    oldEstateTeleportIn=Estate.Estate.exitTeleportIn
    oldHouseDoorIn=House.House.exitDoorIn
    
    def __init__(self):
        DistributedMinigame.DistributedMinigame.announceGenerate=lambda newSelf: self.newAnnounceGenerate1(newSelf)
        PurchaseManager.PurchaseManager.announceGenerate=lambda newSelf: self.newAnnounceGenerate2(newSelf)
        Playground.Playground.exitTeleportIn=lambda newSelf,*args,**kwds: self.newTeleportInPlayground(newSelf,*args,**kwds)
        Estate.Estate.exitTeleportIn=lambda newSelf,*args,**kwds: self.newEstateTeleportIn(newSelf,*args,**kwds)
        House.House.exitDoorIn=lambda newSelf,*args,**kwds: self.newHouseDoorIn(newSelf,*args,**kwds)
        #DistributedBuilding.DistributedBuilding.generate=lambda newSelf,*args: self.newBuildingGenerate(newSelf,*args)
        #DistributedBuilding.DistributedBuilding.enterToon=lambda newSelf,*args: self.newEnterToon(newSelf,*args)
        base.localAvatar.setWantBattles(False)
        self.shardIds=[]
        self.isMember=True
        self.jellybeansNeeded=500
        self.questGui=QuestBookPoster.QuestBookPoster(pos=(0.95,1,0.5))
        self.questGui.mouseEnterPoster(0)
        self.questGui.mouseExitPoster=self.questGui.mouseEnterPoster
        self.oldNPCmovie=None
        self.updateQuestGuiLoop=Sequence(Func(self.updateQuestGui),Wait(0.5))
        self.updateQuestGuiLoop.loop()
        for shard in base.cr.activeDistrictMap:
            try:
                ac = base.cr.activeDistrictMap[shard].avatarCount
            except Exception:
                ac = None
            if (ac if ac is not None else 0) < 50:
                self.shardIds.append(shard)
        self.wantedTracks=[1,3]
        self.status=None
        self.buildingLevelToZoneDict={1:1000,2:5000,3:4000,4:3000,5:9000}
        self._debug_lines = deque(maxlen=18)
        self._hudRoot = None
        self._hudStatus = None
        self._hudIntent = None
        self._hudDebug = None
        self._build_task_autoer_hud()
        self.officer = None

    def _yolo_retry_seconds(self):
        try:
            return max(0.5, float(base.config.GetFloat('want-task-autoer-yolo-retry', 2.5)))
        except Exception:
            return 2.5

    def _yolo_enabled(self):
        try:
            return base.config.GetBool('want-task-autoer-yolo', True)
        except Exception:
            return True

    def set_hud_status(self, text):
        try:
            if self._hudStatus:
                self._hudStatus['text'] = 'STATUS: %s' % text
        except Exception:
            pass

    def set_hud_intent(self, text):
        try:
            if self._hudIntent:
                self._hudIntent['text'] = 'NEXT: %s' % text
        except Exception:
            pass

    def _safe_gag_trainer_start(self):
        """Run gagTrainer.start(); log completion or schedule planner retry on failure."""
        try:
            TAG.gagTrainer.start()
            self.debug_line('gagTrainer.start() returned (sync part done)')
        except Exception as e:
            self.debug_line('gagTrainer.start() failed: %s' % e)
            self._retry_check_what_to_do(2.0)

    def debug_line(self, msg):
        try:
            line = msg if len(msg) <= 160 else (msg[:157] + '...')
            self._debug_lines.append(line)
            if self._hudDebug is not None:
                self._hudDebug['text'] = '\n'.join(self._debug_lines)
        except Exception:
            pass
        try:
            notify.debug(msg)
        except Exception:
            pass
        try:
            print('[TaskAutoer] %s' % msg)
        except Exception:
            pass

    def _retry_check_what_to_do(self, delay=None):
        d = self._yolo_retry_seconds() if delay is None else max(0.3, float(delay))
        self.set_hud_intent('Planner retry in %.1fs' % d)
        self.debug_line('YOLO: scheduling checkWhatToDo in %.1fs' % d)
        Sequence(Wait(d), Func(self.checkWhatToDo)).start()

    def _is_ttc_playground_zone(self):
        """Fishing docks live on the TTC playground (canonical 2000), not on streets (2100–2300)."""
        try:
            z = base.localAvatar.getZoneId()
            return ZoneUtil.getCanonicalZoneId(z) == ToontownGlobals.ToontownCentral
        except Exception:
            return False

    def _request_safe_teleport_ttc(self):
        """Teleport to Toontown Central playground; no-op safely if place/teleport unavailable."""
        place = None
        try:
            place = base.cr.playGame.getPlace()
        except Exception:
            pass
        if place is None:
            self.debug_line('Teleport TTC: no Place — retry soon')
            self._retry_check_what_to_do(1.0)
            return
        try:
            if base.localAvatar.hasActiveBoardingGroup():
                self.debug_line('Teleport TTC: blocked (boarding group) — retry')
                self._retry_check_what_to_do(2.0)
                return
        except Exception:
            pass
        try:
            st = place.getState()
            if st == 'stickerBook':
                self.debug_line('Teleport TTC: close sticker book first — retry')
                self._retry_check_what_to_do(2.0)
                return
        except Exception:
            pass
        hood = ToontownGlobals.ToontownCentral
        try:
            place.requestTeleport(hood, hood, None, None)
            self.debug_line('Teleport TTC: issued requestTeleport(%s,%s)' % (hood, hood))
        except Exception as e:
            self.debug_line('Teleport TTC failed: %s — retry' % e)
            self._retry_check_what_to_do(2.0)

    def _ensure_ttc_playground_then_fish(self):
        """Jellybean farming uses TTC pond; streets in the same hood have no dock entry."""
        if not self._is_ttc_playground_zone():
            self.set_hud_intent('Enter TTC playground for pond')
            self.debug_line('Jellybeans: not on TTC playground (zone=%s) — teleport' % base.localAvatar.getZoneId())
            self._request_safe_teleport_ttc()
            return
        self.fishOnce()

    def _build_task_autoer_hud(self):
        self._hudRoot = DirectFrame(
            parent=aspect2d,
            frameColor=(0.05, 0.07, 0.12, 0.91),
            frameSize=(-0.55, 0.55, -0.66, 0.1),
            pos=(-0.85, 0, 0.33),
            relief=DGG.FLAT,
            sortOrder=100,
        )
        DirectFrame(
            parent=self._hudRoot,
            frameColor=(0.12, 0.78, 0.92, 1),
            frameSize=(-0.55, 0.55, 0.04, 0.08),
            pos=(0, 0, 0.088),
            relief=DGG.FLAT,
        )
        DirectLabel(
            parent=self._hudRoot,
            relief=None,
            text='\x01shadow\x01TASK AUTOER\x02',
            text_scale=0.048,
            text_align=TextNode.ALeft,
            pos=(-0.51, 0, 0.032),
            text_fg=(0.98, 1, 1, 1),
        )
        DirectLabel(
            parent=self._hudRoot,
            relief=None,
            text='YOLO',
            text_scale=0.036,
            text_align=TextNode.ARight,
            pos=(0.51, 0, 0.038),
            text_fg=(0.25, 0.95, 0.82, 1),
        )
        self._hudStatus = DirectLabel(
            parent=self._hudRoot,
            relief=None,
            text='STATUS: starting',
            text_scale=0.031,
            text_align=TextNode.ALeft,
            pos=(-0.51, 0, -0.06),
            text_fg=(0.78, 0.84, 0.96, 1),
            textMayChange=1,
        )
        self._hudIntent = DirectLabel(
            parent=self._hudRoot,
            relief=None,
            text='NEXT: —',
            text_scale=0.029,
            text_align=TextNode.ALeft,
            pos=(-0.51, 0, -0.12),
            text_fg=(0.55, 0.92, 0.72, 1),
            textMayChange=1,
        )
        self._hudDebug = DirectLabel(
            parent=self._hudRoot,
            relief=None,
            text='',
            text_scale=0.023,
            text_align=TextNode.ALeft,
            pos=(-0.51, 0, -0.2),
            text_fg=(0.42, 0.88, 0.52, 1),
            textMayChange=1,
            text_wordwrap=29,
        )
        self.debug_line('HUD online — debug feed active')

    def _clear_ba_gt_safe(self):
        ba = TAG.buildingAutoer
        gt = TAG.gagTrainer
        if ba is not None:
            try:
                ba.clearSettings()
            except Exception as e:
                self.debug_line('clearSettings buildingAutoer: %s' % e)
        if gt is not None:
            try:
                gt.clearSettings()
            except Exception as e:
                self.debug_line('clearSettings gagTrainer: %s' % e)

    def _maxer_vp_factory(self, only_last, set_only_last=True):
        m = TAG.vpMaxer
        if m is None:
            self.debug_line('vpMaxer not available (load bundle)')
            self._retry_check_what_to_do()
            return False
        try:
            if set_only_last:
                m.otherFunctions.onlyLast = only_last
            m.otherFunctions.onlyDoFactory()
            m.otherFunctions.start()
            self.debug_line('vpMaxer: factory start onlyLast=%s' % only_last)
            return True
        except Exception as e:
            self.debug_line('vpMaxer factory failed: %s' % e)
            notify.warning(traceback.format_exc())
            self._retry_check_what_to_do()
            return False

    def _maxer_cfo_mint(self, only_last, mint_type, set_mint_type_first=False):
        """Start CFO mint autoer. Order of onlyDoMint vs setType matches legacy scripts (two variants)."""
        m = TAG.cfoMaxer
        if m is None:
            self.debug_line('cfoMaxer not available (load bundle)')
            self._retry_check_what_to_do()
            return False
        try:
            m.otherFunctions.onlyLast = only_last
            if set_mint_type_first:
                m.mintAutoer.setType(mint_type)
                m.otherFunctions.onlyDoMint()
            else:
                m.otherFunctions.onlyDoMint()
                m.mintAutoer.setType(mint_type)
            m.otherFunctions.start()
            self.debug_line('cfoMaxer: mint start onlyLast=%s type=%s (typeFirst=%s)' % (only_last, mint_type, set_mint_type_first))
            return True
        except Exception as e:
            self.debug_line('cfoMaxer mint failed: %s' % e)
            notify.warning(traceback.format_exc())
            self._retry_check_what_to_do()
            return False

    def _maxer_ceo(self):
        m = TAG.ceoMaxer
        if m is None:
            self.debug_line('ceoMaxer not available (load bundle)')
            self._retry_check_what_to_do()
            return False
        try:
            m.otherFunctions.start()
            self.debug_line('ceoMaxer: started')
            return True
        except Exception as e:
            self.debug_line('ceoMaxer failed: %s' % e)
            notify.warning(traceback.format_exc())
            self._retry_check_what_to_do()
            return False

    def _require_gt(self):
        if TAG.gagTrainer is None:
            self.debug_line('gagTrainer not loaded (autoer bundle?)')
            self._retry_check_what_to_do()
            return False
        return True

    def _require_ba(self):
        if TAG.buildingAutoer is None:
            self.debug_line('buildingAutoer not loaded (autoer bundle?)')
            self._retry_check_what_to_do()
            return False
        return True

    def _safeMoney(self):
        try:
            m = base.localAvatar.getTotalMoney()
        except Exception:
            return 0
        if m is None:
            return 0
        try:
            return int(m)
        except (TypeError, ValueError):
            return 0

    def _safeJellybeansNeeded(self):
        try:
            j = self.jellybeansNeeded
        except Exception:
            return 500
        if j is None:
            return 500
        try:
            return int(j)
        except (TypeError, ValueError):
            return 500

    def _safeMaxHp(self):
        try:
            h = base.localAvatar.getMaxHp()
        except Exception:
            return 0
        if h is None:
            return 0
        try:
            return int(h)
        except (TypeError, ValueError):
            return 0

    def _safeQuestCogLevel(self, quest):
        try:
            c = quest.getCogLevel()
        except Exception:
            return 0
        if c is None:
            return 0
        try:
            return int(c)
        except (TypeError, ValueError):
            return 0
        
    def newAnnounceGenerate1(self,newSelf):
        self.oldAnnounceGenerate1(newSelf)
        messenger.send('minigameAbort')

    def newAnnounceGenerate2(self,newSelf):
        self.oldAnnounceGenerate2(newSelf)
        Sequence(Wait(10),Func(self.skipTrolley)).start()
    
    def skipTrolley(self):
        for i in range(5):
            messenger.send('doneChatPage')
        Sequence(Wait(4),Func(messenger.send,'purchaseBackToToontown')).start()
    
    def newNPCmovie(self, mode, npcId, avId, quests, timestamp):
        self.oldNPCmovie(mode, npcId, avId, quests, timestamp)
        if avId != base.localAvatar.doId:
            return
        from toontown.toon import NPCToons
        if mode != NPCToons.QUEST_MOVIE_QUEST_CHOICE:
            return
        if not quests or len(quests) % 3 != 0:
            return
        chosenId = None
        for i in range(0, len(quests), 3):
            qid = quests[i]
            rid = quests[i + 1]
            if not Quests.isQuestJustForFun(qid, rid):
                chosenId = qid
                break
        if chosenId is None:
            chosenId = quests[0]
        self.officer.sendChooseQuest(chosenId)
        self.officer.sendUpdate('setMovieDone')
        self.officer.setMovie = self.oldNPCmovie
        base.cr.playGame.getPlace().fsm.forceTransition('walk')
    
    def newBuildingGenerate(self,newSelf,*args):
        try:
            oldBuildingGenerate(newSelf,*args)
        except:
            pass
    
    def newEnterToon(self,newSelf,*args):
        try:
            oldEnterToon(newSelf,*args)
        except:
            pass
    
    def newTeleportInPlayground(self,newSelf,*args,**kwds):
        self.oldTeleportInPlayground(newSelf,*args,**kwds)
        ba = TAG.buildingAutoer
        gt = TAG.gagTrainer
        try:
            z = base.localAvatar.getZoneId()
        except Exception:
            z = None
        if ba and ba.shouldContinue:
            self.debug_line('Playground teleportIn: buildingAutoer (zone=%s)' % z)
            ba.checkStop()

            if ba.shouldContinue and not self.isQuestComplete():
                ba.killElevators.append(ba.lastElevator)
                Sequence(Wait(2),Func(ba.teleportBackToStreet)).start()
            else:
                Sequence(Wait(2),Func(self.checkWhatToDo)).start()
        elif gt and gt.shouldContinue:
            self.debug_line('Playground teleportIn: gagTrainer resume (zone=%s)' % z)
            Sequence(Wait(2),Func(gt.teleportBackToStreet)).start()
        else:
            self.debug_line('Playground teleportIn: planner checkWhatToDo (zone=%s)' % z)
            Sequence(Wait(2),Func(self.checkWhatToDo)).start()
    
    def newEstateTeleportIn(self,newSelf,*args,**kwds):
        self.oldEstateTeleportIn(newSelf,*args,**kwds)
        for door in base.cr.doFindAll('Door'):  
            if 'esHouse_1' in str(door.getBuilding()):
                door.sendUpdate('requestEnter')
           
    def newHouseDoorIn(self,newSelf,*args,**kwds):
        self.oldHouseDoorIn(newSelf,*args,**kwds)
        base.cr.doFind('phone').sendUpdate('avatarEnter')
        base.cr.doFind('phone').sendUpdate('avatarExit')
        Sequence(Wait(2),Func(self.checkWhatToDo)).start()
            
    def checkWhatToDo(self):
        try:
            self._checkWhatToDoImpl()
        except Exception as e:
            self.debug_line('checkWhatToDo exception: %s' % e)
            notify.warning(traceback.format_exc())
            if self._yolo_enabled():
                self._retry_check_what_to_do()
            else:
                try:
                    base.localAvatar.setSystemMessage(0, 'Task autoer: %s' % e)
                except Exception:
                    pass

    def _checkWhatToDoImpl(self):
        self.set_hud_status('Planning')
        self.set_hud_intent('Evaluating money, district, quests')
        self.debug_line(
            'checkWhatToDo: money=%s jellyTarget=%s status=%s shard=%s quests=%s'
            % (
                self._safeMoney(),
                self._safeJellybeansNeeded(),
                self.status,
                getattr(base.localAvatar, 'defaultShard', None),
                len(base.localAvatar.quests) if base.localAvatar.quests else 0,
            )
        )

        if self._safeMoney() > self._safeJellybeansNeeded():
            self.jellybeansNeeded = 500

        if self.shardIds and base.localAvatar.defaultShard not in self.shardIds:
            self.set_hud_intent('Switching to quieter district')
            self.debug_line('Relocating to alternate shard (population cap)')
            try:
                base.cr.playGame.getPlace().requestTeleport(
                    ToontownGlobals.ToontownCentral,
                    ToontownGlobals.ToontownCentral,
                    random.choice(self.shardIds),
                    None,
                )
            except Exception as e:
                self.debug_line('Shard switch teleport failed: %s' % e)
                self._retry_check_what_to_do(2.0)

        elif self.status == 'Fishing':
            if not self.isQuestComplete():
                self.set_hud_status('Fishing')
                self.set_hud_intent('Casting / selling fish')
                self.debug_line('Fishing loop: quest not complete')
                if not self._is_ttc_playground_zone():
                    self.debug_line('Fishing: move to TTC playground first')
                    self._request_safe_teleport_ttc()
                else:
                    self.fishOnce()
            else:
                self.set_hud_intent('Leaving docks after fish task')
                self.debug_line('Fishing done: exiting spots')
                for dock in base.cr.doFindAll('DistributedFishingSpot'):
                    dock.sendUpdate('requestExit')
                self.status = None
                self.doTask()

        elif base.localAvatar.quests:
            self.set_hud_intent('Delegate to quest runner')
            self.debug_line('Active quest(s): running doTask (quests beat idle jellybean farming)')
            self.doTask()

        elif self.jellybeansNeeded == 12000:
            self.set_hud_status('Farming jellybeans')
            self.set_hud_intent('Fish for jellybeans')
            self.debug_line('Low jellybeans: fishing for cash (no active quests)')
            self._ensure_ttc_playground_then_fish()

        elif self._safeMoney() < self._safeJellybeansNeeded():
            self.jellybeansNeeded = 12000
            self.set_hud_intent('Teleport Toontown Central for fishing')
            self.debug_line('Need jellybeans: heading to TTC pond (no quests)')
            self._request_safe_teleport_ttc()
        else:
            self.set_hud_intent('Pick up new task from HQ')
            self.debug_line('No quests: collecting new task')
            self.collectNewTask()
    
    def updateQuestGui(self):
        if base.localAvatar.quests:
            self.questGui.update(base.localAvatar.quests[0])
        else:
            self.questGui.clear()
        
    def getCurrentQuest(self):
        return Quests.getQuest(base.localAvatar.quests[0][0])
    
    def getBestZoneForCogLevel(self,level):
        try:
            level = int(level)
        except (TypeError, ValueError):
            level = 1
        if self.isMember:
            if level<3:
                return 2000
            elif level<4:
                return 1000
            elif level<5:
                return 5000
            elif level<6:
                return 4000
            elif level<7:
                return 3000
            elif level<8:
                return 9000
            elif level<9:
                return 12000
            else:
                return 13000
        else:
            return 2000
    
    def getBestZoneForBuildingLevel(self,level):
        try:
            level = int(level)
        except (TypeError, ValueError):
            level = 1
        return self.buildingLevelToZoneDict.get(level)
    
    def getSuitName(self,suitType):
        try:
            return SuitBattleGlobals.SuitAttributes[suitType].get('name')
        except:
            return suitType
    
    def getCogLevelFromCog(self,suitType):
        try:
            lv = SuitBattleGlobals.SuitAttributes[suitType].get('level')
            return (lv if lv is not None else 0) + 1
        except Exception:
            return 1
            
    
    def getSuitDepartment(self,suitType):
        return SuitDNA.getSuitDept(suitType)
    
    def getCorrectChoice(self,choices):
        if 0 in choices:
            return 0
        elif 2 in choices:
            return 2
        elif self.wantedTracks[0] in choices:
            return self.wantedTracks[0]
        else:
            return self.wantedTracks[1]
                    
    def newTask(self):
        for officer in base.cr.doFindAll('HQ Officer'):
            if officer.allowedToTalk():
                if officer.setMovie!=self.oldNPCmovie:
                    self.oldNPCmovie=officer.setMovie
                self.officer=officer
                officer.setMovie=self.newNPCmovie
                officer.sendUpdate('avatarEnter')
                break
        
    def collectNewTask(self):
        interest = base.cr.addInterest(base.localAvatar.defaultShard, 2742, '5', None)
        Sequence(Wait(1),Func(self.newTask),Wait(2),Func(base.cr.removeInterest,interest),Func(self.checkWhatToDo)).start()
    
    def nextShard(self):
        base.cr.playGame.getPlace().fsm.forceTransition('walk')
        base.cr.playGame.getPlace().requestTeleport(2000,2000,self.shardIds[0],None)
        self.shardIds.append(self.shardIds[0])
        del self.shardIds[0]
    
    def catchFish(self):
        try:
            fish = base.cr.doFindAll("FishingTarget")[0]
            for fp in base.cr.doFindAll("FishingPond"):
                fp.d_hitTarget(fish)
        except:
            pass
    
    def fishOnce(self):
        entered=False
        for spot in reversed(base.cr.doFindAll('DistributedFishingSpot')):
            if spot.allowedToEnter():
                entered=True
                spot.sendUpdate('requestEnter')
                usedSpot=spot
                break
        if entered:
            catchFishSeq=Sequence()
            catchFishSeq.append(Wait(1))
            for i in range(23):
                catchFishSeq.append(Func(self.catchFish))
                catchFishSeq.append(Wait(0.05))
            catchFishSeq.append(Wait(1))
            catchFishSeq.append(Func(self.sellFish))
            catchFishSeq.append(Wait(0.5))
            catchFishSeq.append(Func(self.checkWhatToDo))
            catchFishSeq.start()
        else:
            Sequence(Wait(2),Func(self.fishOnce)).start()
            
    def sellFish(self):
        base.cr.doFind('Fisherman').sendUpdate('avatarEnter')
        base.cr.doFind('Fisherman').sendUpdate('completeSale',[1])
        
    def speakToNpc(self,name):
        if base.cr.doFind(name):
            for npc in base.cr.doFindAllInstances(DistributedNPCToon.DistributedNPCToon):
                if npc.getName()==name:
                    if npc.allowedToTalk():
                        npc.sendUpdate('avatarEnter')
                        npc.sendUpdate('setMovieDone')
                        base.cr.removeInterest(self.interest)
                        Sequence(Wait(1),Func(self.checkWhatToDo)).start()
                        found=True
                        foundNPC=True
                        break
                    else:
                        found=False
                        foundNPC=True
                else:
                    foundNPC=False
            if not foundNPC:
                Sequence(Func(base.cr.removeInterest,self.interest),Wait(0.5),Func(self.nextShard)).start()
            elif not found:
                Sequence(Wait(5),Func(self.speakToNpc,name)).start()
        else:
            Sequence(Func(base.cr.removeInterest,self.interest),Wait(0.5),Func(self.nextShard)).start()
    
    def chooseTrack(self,name):
        if base.cr.doFind(name):
            for npc in base.cr.doFindAllInstances(DistributedNPCToon.DistributedNPCToon):
                if npc.getName()==name:
                    if npc.allowedToTalk():
                        npc.sendUpdate('avatarEnter')
                        try:
                            npc.sendChooseTrack(self.getCorrectChoice(self.getCurrentQuest().getChoices()))
                            npc.sendUpdate('setMovieDone')
                        except:
                            pass
                        base.cr.removeInterest(self.interest)
                        Sequence(Wait(0.5),Func(self.checkWhatToDo)).start()
                        found=True
                        foundNPC=True
                        break
                    else:
                        found=False
                        foundNPC=True
                else:
                    foundNPC=False
            if not foundNPC:
                Sequence(Func(base.cr.removeInterest,self.interest),Wait(0.5),Func(self.nextShard)).start()
            elif not found:
                Sequence(Wait(5),Func(self.chooseTrack,name)).start()
        else:
            Sequence(Func(base.cr.removeInterest,self.interest),Wait(0.5),Func(self.nextShard)).start()
        
    def doTrolleyTask(self):
        if base.localAvatar.getZoneId()==2000:
            if base.cr.doFind('Trolley').allowedToEnter():
                base.cr.playGame.getPlace().fsm.forceTransition('walk')
                base.localAvatar.setPos(-133.548, -71.1069, 0.525)
            else:
                Sequence(Wait(2),Func(self.doTrolleyTask)).start()
        else:
            base.cr.playGame.getPlace().requestTeleport(2000,2000,None,None)

        
    def doNPCTask(self, isTrackTask=False):
        """Resolve target NPC from the 5-field quest row: [questId, fromNpc, toNpc, reward, progress]."""
        try:
            quests = base.localAvatar.quests
            if not quests:
                self.debug_line('doNPCTask: no quests')
                self._retry_check_what_to_do(1.0)
                return
            row = quests[0]
            if not isinstance(row, (list, tuple)):
                self.debug_line('doNPCTask: bad quest row type %s' % type(row).__name__)
                self._retry_check_what_to_do(1.0)
                return
            if len(row) < 5:
                self.debug_line('doNPCTask: quest row len=%s (need 5: id,from,to,reward,progress)' % len(row))
                self._retry_check_what_to_do(1.0)
                return
            toNpcId = row[2]
            zoneId = Quests.NPCToons.getNPCZone(toNpcId)
            if zoneId in (None, -1):
                if toNpcId in (Quests.ToonHQ, Quests.Any):
                    zoneId = 2742
                else:
                    qe = Quests.QuestDict.get(row[0])
                    if qe:
                        alt = Quests.NPCToons.getNPCZone(qe[Quests.QuestDictToNpcIndex])
                        if alt not in (None, -1):
                            zoneId = alt
                    if zoneId in (None, -1):
                        zoneId = 2742
                    self.debug_line('doNPCTask: fallback zone 2742 for npcId=%s' % toNpcId)
            npcName = Quests.NPCToons.getNPCName(toNpcId)
            if not npcName:
                npcName = 'HQ Officer'
            self.debug_line('doNPCTask: npcId=%s name=%s zoneId=%s' % (toNpcId, npcName, zoneId))
            self.interest = base.cr.addInterest(base.localAvatar.defaultShard, zoneId, '5', None)
            if not isTrackTask:
                Sequence(Wait(2), Func(self.speakToNpc, npcName)).start()
            else:
                Sequence(Wait(2), Func(self.chooseTrack, npcName)).start()
        except Exception as e:
            self.debug_line('doNPCTask failed: %s' % e)
            try:
                notify.warning(''.join(traceback.format_exception_only(type(e), e)))
            except Exception:
                notify.warning('doNPCTask error: %s' % e)
            self._retry_check_what_to_do(0.75)

    def doTask(self):
        try:
            self._doTaskImpl()
        except Exception as e:
            self.debug_line('doTask exception: %s' % e)
            try:
                notify.warning('doTask: %s' % (e,))
                if e.__traceback__:
                    notify.warning(''.join(traceback.format_tb(e.__traceback__)[-12:]))
            except Exception:
                pass
            if self._yolo_enabled():
                self._retry_check_what_to_do()
            else:
                try:
                    base.localAvatar.setSystemMessage(0, 'Task autoer: %s' % e)
                except Exception:
                    pass

    def _doTaskImpl(self):
        self.set_hud_status('Quest runner')
        if not base.localAvatar.quests:
            self.debug_line('doTask: no quests on avatar')
            self._retry_check_what_to_do()
            return
        try:
            quest = Quests.getQuest(base.localAvatar.quests[0][0])
        except Exception as e:
            self.debug_line('doTask: getQuest failed: %s' % e)
            self._retry_check_what_to_do()
            return
        try:
            qt = quest.getType()
        except Exception as e:
            self.debug_line('doTask: getType failed: %s' % e)
            self._retry_check_what_to_do()
            return

        self.debug_line('doTask: questId=%s type=%s' % (base.localAvatar.quests[0][0], qt))

        if self.isQuestComplete() or qt == Quests.VisitQuest:
            self.set_hud_intent('Visit / turn in to NPC')
            self.debug_line('Route: VisitQuest or complete')
            self.doNPCTask()

        elif qt == Quests.DeliverItemQuest:
            self.set_hud_intent('Deliver item')
            self.debug_line('Route: DeliverItemQuest')
            self.doNPCTask()

        elif isinstance(quest, Quests.CogQuest):
            self.set_hud_intent('Cog combat / HQ / building')
            self.debug_line(
                'Route: Cog quest class=%s loc=%s'
                % (quest.__class__.__name__, quest.getLocation())
            )
            self._clear_ba_gt_safe()
            if quest.getLocation() == 11500:
                if not self._maxer_vp_factory(False, set_only_last=False):
                    return
            elif isinstance(quest, Quests.CogTrackQuest):
                if not self._require_gt():
                    return
                loc = quest.getLocation()
                if loc == Quests.Anywhere or loc == 1:
                    track = quest.getCogTrack()
                    if track == 'c' or self._safeMaxHp() < 30:
                        location = 2000
                    elif track == 's':
                        location = 11200
                    elif track == 'm':
                        location = 12000
                    else:
                        location = 13000
                    self.debug_line('CogTrack: target HQ/street zone %s (track=%s)' % (location, track))
                    TAG.gagTrainer.setLocation(location)
                else:
                    self.debug_line('CogTrack: fixed zone %s' % loc)
                    TAG.gagTrainer.setLocation(loc)
                TAG.gagTrainer.setCogType(quest.getCogTrack())
                self.debug_line('Starting gagTrainer (CogTrack)')
                self._safe_gag_trainer_start()

            elif isinstance(quest, Quests.CogLevelQuest):
                if not base.localAvatar.getTrackAccess()[2] or quest.getLocation() in HQZONES or self._safeQuestCogLevel(quest) < 11:
                    if not self._require_gt():
                        return
                    if quest.getLocation() == 1:
                        TAG.gagTrainer.setLocation(self.getBestZoneForCogLevel(self._safeQuestCogLevel(quest) + 1))
                    else:
                        if quest.getLocation() in range(12500, 12701, 1000):
                            if not self._maxer_cfo_mint(False, quest.getLocation()):
                                return
                        elif quest.getLocation() == 11500:
                            if not self._maxer_vp_factory(False, set_only_last=True):
                                return
                        else:
                            TAG.gagTrainer.setLocation(quest.getLocation())

                    if quest.getCogType() == 1:
                        TAG.gagTrainer.setCogLevel(self._safeQuestCogLevel(quest))
                    else:
                        TAG.gagTrainer.setCogName(self.getSuitName(quest.getCogType()))
                    self._safe_gag_trainer_start()
                else:
                    if not self._require_ba():
                        return
                    if quest.getCogType() == 1:
                        TAG.buildingAutoer.setBuildingType('')
                        TAG.buildingAutoer.setNumFloors(4)
                    else:
                        TAG.buildingAutoer.setBuildingType(self.getSuitDepartment(self.getCogType()))
                        TAG.buildingAutoer.setNumFloors(4)

                    if quest.getLocation() != 1:
                        TAG.buildingAutoer.setLocation(quest.getLocation())
                    else:
                        if self._safeMaxHp() > 70:
                            TAG.buildingAutoer.setLocation(self.getBestZoneForBuildingLevel(5))
                        else:
                            TAG.buildingAutoer.setLocation(self.getBestZoneForBuildingLevel(4))
                    TAG.buildingAutoer.start()
            else:
                if not base.localAvatar.getTrackAccess()[2] or quest.getLocation() in HQZONES or self.getCogLevelFromCog(quest.getCogType()) + 4 < 11:

                    if not self._require_gt():
                        return
                    if quest.getLocation() == 1:
                        if self._safeMaxHp() > 30 and quest.getCogType() == 1:
                            TAG.gagTrainer.setLocation(11200)
                        else:
                            TAG.gagTrainer.setLocation(self.getBestZoneForCogLevel(self.getCogLevelFromCog(quest.getCogType()) + 1))
                    else:
                        TAG.gagTrainer.setLocation(quest.getLocation())

                    if quest.getCogType() == 1:
                        TAG.gagTrainer.setCogName(None)
                    else:
                        TAG.gagTrainer.setCogName(self.getSuitName(quest.getCogType()))
                    self._safe_gag_trainer_start()
                else:
                    if not self._require_ba():
                        return
                    if quest.getCogType() == 1:
                        TAG.buildingAutoer.setBuildingType('')
                        TAG.buildingAutoer.setNumFloors(4)
                    else:
                        TAG.buildingAutoer.setBuildingType(self.getSuitDepartment(quest.getCogType()))
                        TAG.buildingAutoer.setNumFloors(4)

                    if quest.getLocation() != 1:
                        TAG.buildingAutoer.setLocation(quest.getLocation())
                    else:
                        if self._safeMaxHp() > 70:
                            TAG.buildingAutoer.setLocation(self.getBestZoneForBuildingLevel(5))
                        else:
                            TAG.buildingAutoer.setLocation(self.getBestZoneForBuildingLevel(4))
                    TAG.buildingAutoer.start()

        elif qt == Quests.BuildingQuest:
            self.set_hud_intent('Building takeover')
            self.debug_line('Route: BuildingQuest')
            if not self._require_ba():
                return
            TAG.buildingAutoer.clearSettings()
            if quest.getLocation() == 1:
                TAG.buildingAutoer.setLocation(self.getBestZoneForBuildingLevel(quest.getNumFloors()))
            else:
                TAG.buildingAutoer.setLocation(quest.getLocation())
            TAG.buildingAutoer.setNumFloors(quest.getNumFloors())
            if quest.getBuildingTrack() == 1:
                TAG.buildingAutoer.setBuildingType('')
            else:
                TAG.buildingAutoer.setBuildingType(quest.getBuildingTrack())

            TAG.buildingAutoer.start()

        elif qt == Quests.RecoverItemQuest:
            self.set_hud_intent('Recover / fish / route combat')
            self.debug_line('Route: RecoverItemQuest holder=%s loc=%s' % (quest.getHolder(), quest.getLocation()))
            if quest.getHolder() == 4:
                self.set_hud_status('Fishing (recover item)')
                if quest.getLocation() == 1:
                    if base.localAvatar.getZoneId() != 2000:
                        self.debug_line('Recover fish: teleport TTC')
                        base.cr.playGame.getPlace().requestTeleport(2000, 2000, None, None)
                        self.status = 'Fishing'
                    else:
                        self.status = 'Fishing'
                        self.checkWhatToDo()

                else:
                    if base.localAvatar.getZoneId() != quest.getLocation():
                        self.debug_line('Recover fish: teleport zone %s' % quest.getLocation())
                        base.cr.playGame.getPlace().requestTeleport(quest.getLocation(), quest.getLocation(), None, None)
                        self.status = 'Fishing'
                    else:
                        self.status = 'Fishing'
                        self.checkWhatToDo()
            else:
                self._clear_ba_gt_safe()
                if not self.isSuitOnlyBldg(quest.getHolder()) or quest.getHolderType() == 'track':
                    if not self._require_gt():
                        return
                    if quest.getLocation() == 1:
                        if type(quest.getHolder()) == int:
                            TAG.gagTrainer.setLocation(self.getBestZoneForCogLevel(quest.getHolder() + 1))
                        elif quest.getHolderType() == 'track':
                            TAG.gagTrainer.setLocation(2000)
                        else:
                            TAG.gagTrainer.setLocation(self.getBestZoneForCogLevel(self.getCogLevelFromCog(quest.getHolder()) + 1))
                    else:
                        TAG.gagTrainer.setLocation(quest.getLocation())

                    if type(quest.getHolder()) == int:
                        TAG.gagTrainer.setCogLevel(quest.getHolder())
                    elif quest.getHolderType() == 'track':
                        TAG.gagTrainer.setCogType(quest.getHolder())
                    else:
                        TAG.gagTrainer.setCogName(self.getSuitName(quest.getHolder()))
                    self._safe_gag_trainer_start()

                elif quest.getLocation() == 12000:
                    if not self._maxer_cfo_mint(True, 12500):
                        return

                elif quest.getLocation() == 11000:
                    if not self._maxer_vp_factory(True, set_only_last=True):
                        return

                else:
                    if not self._require_ba():
                        return
                    if quest.getLocation() == 1:
                        TAG.buildingAutoer.setLocation(self.getBestZoneForBuildingLevel(4))
                    else:
                        TAG.buildingAutoer.setLocation(quest.getLocation())
                    if quest.getHolder() == 1:
                        TAG.buildingAutoer.setBuildingType('')
                    else:
                        TAG.buildingAutoer.setBuildingType(self.getSuitDepartment(quest.getHolder()))
                    TAG.buildingAutoer.start()

        elif qt == Quests.DeliverGagQuest:
            self.set_hud_intent('Restock gag then NPC')
            self.debug_line('Route: DeliverGagQuest')
            gt = TAG.gagTrainer
            if gt is None:
                self.debug_line('DeliverGag: gagTrainer missing')
                self._retry_check_what_to_do()
                return
            Sequence(Func(gt.restock.restockGags, quest.getGagType()), Wait(2), Func(self.doNPCTask)).start()

        elif qt == Quests.SkelecogLevelQuest:
            self.set_hud_intent('Skelecog HQ task')
            self.debug_line('Route: SkelecogLevelQuest loc=%s' % quest.getLocation())
            if quest.getLocation() == 11000:
                if not self._maxer_vp_factory(False, set_only_last=True):
                    return
            elif quest.getLocation() == 12000:
                if not self._maxer_cfo_mint(False, 12500, set_mint_type_first=True):
                    return
            elif quest.getLocation() == 13000:
                cj = TAG.cjMaxer
                if cj is None:
                    self.debug_line('Skelecog: CJ maxer not loaded — add CJMaxer.py or retry')
                    try:
                        base.localAvatar.setSystemMessage(0, 'Task autoer: load CJ maxer for this task.')
                    except Exception:
                        pass
                    self._retry_check_what_to_do(5.0)
                    return
                try:
                    cj.otherFunctions.onlyDoDa()
                    cj.otherFunctions.start()
                    self.debug_line('CJ DA maxer started')
                except Exception as e:
                    self.debug_line('CJ maxer start failed: %s' % e)
                    self._retry_check_what_to_do()
            elif quest.getLocation() == 1:
                if self._safeQuestCogLevel(quest) < 9:
                    if not self._maxer_vp_factory(False, set_only_last=True):
                        return
                else:
                    if not self._maxer_cfo_mint(False, 12500, set_mint_type_first=True):
                        return

        elif qt in (Quests.FactoryQuest, Quests.ForemanQuest):
            self.set_hud_intent('VP factory')
            self.debug_line('Route: Factory/Foreman')
            if not self._maxer_vp_factory(True, set_only_last=True):
                return

        elif qt == Quests.SupervisorQuest:
            self.set_hud_intent('CFO supervisor')
            self.debug_line('Route: SupervisorQuest')
            if not self._maxer_cfo_mint(True, quest.getLocation()):
                return

        elif qt == Quests.SkeleReviveQuest:
            self.set_hud_intent('CEO revive')
            self.debug_line('Route: SkeleReviveQuest')
            if not self._maxer_ceo():
                return

        elif qt == Quests.TrackChoiceQuest:
            self.set_hud_intent('Choose track (NPC)')
            self.debug_line('Route: TrackChoiceQuest')
            self.doNPCTask(isTrackTask=True)

        elif qt == Quests.TrolleyQuest:
            self.set_hud_intent('Trolley minigame')
            self.debug_line('Route: TrolleyQuest')
            self.doTrolleyTask()

        elif qt == Quests.PhoneQuest:
            self.set_hud_intent('Clarabelle / phone')
            self.debug_line('Route: PhoneQuest')
            base.localAvatar._LocalToon__handleClarabelleButton()

        else:
            self.debug_line('Unknown quest type %s — YOLO reschedule' % qt)
            try:
                base.localAvatar.setSystemMessage(0, 'Task autoer: unknown quest type (will retry)')
            except Exception:
                pass
            if self._yolo_enabled():
                self._retry_check_what_to_do(4.0)
            
                
    def isQuestComplete(self):
        try:
            base.localAvatar.book.pages[4].updatePage()
            return base.localAvatar.book.pages[4].questFrames[0].headline['text'] == TTLocalizer.QuestPosterComplete
        except Exception:
            return False
    
    def isSuitOnlyBldg(self,suitType):
        try:
            lv = SuitBattleGlobals.SuitAttributes[suitType].get('level')
            if (lv if lv is not None else 0) + 1 > 6:
                return True
            else:
                return False
        except KeyError:
            return False

    def revert(self):
        try:
            self.updateQuestGuiLoop.finish()
        except Exception:
            pass
        try:
            if getattr(self, 'questGui', None):
                self.questGui.destroy()
                self.questGui = None
        except Exception:
            pass
        try:
            if getattr(self, '_hudRoot', None):
                self._hudRoot.destroy()
        except Exception:
            pass
        self._hudRoot = None
        self._hudStatus = None
        self._hudIntent = None
        self._hudDebug = None
        DistributedMinigame.DistributedMinigame.announceGenerate = TaskAutoer.oldAnnounceGenerate1
        PurchaseManager.PurchaseManager.announceGenerate = TaskAutoer.oldAnnounceGenerate2
        Playground.Playground.exitTeleportIn = TaskAutoer.oldTeleportInPlayground
        Estate.Estate.exitTeleportIn = TaskAutoer.oldEstateTeleportIn
        House.House.exitDoorIn = TaskAutoer.oldHouseDoorIn
        try:
            for npc in base.cr.doFindAllInstances(DistributedNPCToon.DistributedNPCToon):
                if 'Officer' in npc.getName():
                    npc.setMovie = types.MethodType(DistributedNPCToon.DistributedNPCToon.setMovie, npc)
        except Exception:
            pass
        self.officer = None
        if base.localAvatar:
            base.localAvatar.setWantBattles(True)


taskAutoer = None


def bootstrap_task_autoer():
    global taskAutoer
    if taskAutoer is not None:
        return taskAutoer
    taskAutoer = TaskAutoer()
    return taskAutoer


def revert_task_autoer():
    global taskAutoer
    if taskAutoer is None:
        return
    taskAutoer.revert()
    taskAutoer = None
