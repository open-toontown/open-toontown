from direct.directnotify import DirectNotifyGlobal
from toontown.toonbase import ToontownBattleGlobals
from toontown.suit import SuitDNA
BattleExperienceAINotify = DirectNotifyGlobal.directNotify.newCategory('BattleExprienceAI')

def getSkillGained(toonSkillPtsGained, toonId, track):
    exp = 0
    expList = toonSkillPtsGained.get(toonId, None)
    if expList != None:
        exp = expList[track]
    return int(exp + 0.5)


def getBattleExperience(numToons, activeToons, toonExp, toonSkillPtsGained, toonOrigQuests, toonItems, toonOrigMerits, toonMerits, toonParts, suitsKilled, helpfulToonsList=None):
    if helpfulToonsList == None:
        BattleExperienceAINotify.warning('=============\nERROR ERROR helpfulToons=None in assignRewards , tell Red')
    p = []
    for k in range(numToons):
        toon = None
        if k < len(activeToons):
            toonId = activeToons[k]
            toon = simbase.air.doId2do.get(toonId)
        if toon == None:
            p.append(-1)
            p.append([0, 0, 0, 0, 0, 0, 0])
            p.append([0, 0, 0, 0, 0, 0, 0])
            p.append([])
            p.append([])
            p.append([])
            p.append([0, 0, 0, 0])
            p.append([0, 0, 0, 0])
            p.append([0, 0, 0, 0])
        else:
            p.append(toonId)
            origExp = toonExp[toonId]
            earnedExp = []
            for i in range(len(ToontownBattleGlobals.Tracks)):
                earnedExp.append(getSkillGained(toonSkillPtsGained, toonId, i))

            p.append(origExp)
            p.append(earnedExp)
            origQuests = toonOrigQuests.get(toonId, [])
            p.append(origQuests)
            items = toonItems.get(toonId, ([], []))
            p.append(items[0])
            p.append(items[1])
            origMerits = toonOrigMerits.get(toonId, [])
            p.append(origMerits)
            merits = toonMerits.get(toonId, [0, 0, 0, 0])
            p.append(merits)
            parts = toonParts.get(toonId, [0, 0, 0, 0])
            p.append(parts)

    deathList = []
    toonIndices = {}
    for i in range(len(activeToons)):
        toonIndices[activeToons[i]] = i

    for deathRecord in suitsKilled:
        level = deathRecord['level']
        type = deathRecord['type']
        if deathRecord['isVP'] or deathRecord['isCFO']:
            level = 0
            typeNum = SuitDNA.suitDepts.index(deathRecord['track'])
        else:
            typeNum = SuitDNA.suitHeadTypes.index(type)
        involvedToonIds = deathRecord['activeToons']
        toonBits = 0
        for toonId in involvedToonIds:
            if toonId in toonIndices:
                toonBits |= 1 << toonIndices[toonId]

        flags = 0
        if deathRecord['isSkelecog']:
            flags |= ToontownBattleGlobals.DLF_SKELECOG
        if deathRecord['isForeman']:
            flags |= ToontownBattleGlobals.DLF_FOREMAN
        if deathRecord['isVP']:
            flags |= ToontownBattleGlobals.DLF_VP
        if deathRecord['isCFO']:
            flags |= ToontownBattleGlobals.DLF_CFO
        if deathRecord['isSupervisor']:
            flags |= ToontownBattleGlobals.DLF_SUPERVISOR
        if deathRecord['isVirtual']:
            flags |= ToontownBattleGlobals.DLF_VIRTUAL
        if 'hasRevies' in deathRecord and deathRecord['hasRevives']:
            flags |= ToontownBattleGlobals.DLF_REVIVES
        deathList.extend([typeNum, level, toonBits, flags])

    p.append(deathList)
    uberStats = getToonUberStatus(activeToons, numToons)
    p.append(uberStats)
    if helpfulToonsList == None:
        helpfulToonsList = []
    p.append(helpfulToonsList)
    return p


def getToonUberStatus(toons, numToons):
    fieldList = []
    uberIndex = ToontownBattleGlobals.LAST_REGULAR_GAG_LEVEL + 1
    for toonId in toons:
        toonList = []
        toon = simbase.air.doId2do.get(toonId)
        if toon == None:
            fieldList.append(-1)
        else:
            for trackIndex in range(ToontownBattleGlobals.MAX_TRACK_INDEX + 1):
                toonList.append(toon.inventory.numItem(trackIndex, uberIndex))

            fieldList.append(ToontownBattleGlobals.encodeUber(toonList))

    lenDif = numToons - len(toons)
    if lenDif > 0:
        for index in range(lenDif):
            fieldList.append(-1)

    return fieldList


def assignRewards(activeToons, toonSkillPtsGained, suitsKilled, zoneId, helpfulToons = None):
    if helpfulToons == None:
        BattleExperienceAINotify.warning('=============\nERROR ERROR helpfulToons=None in assignRewards , tell Red')
    activeToonList = []
    for t in activeToons:
        toon = simbase.air.doId2do.get(t)
        if toon != None:
            activeToonList.append(toon)

    for toon in activeToonList:
        for i in range(len(ToontownBattleGlobals.Tracks)):
            uberIndex = ToontownBattleGlobals.LAST_REGULAR_GAG_LEVEL + 1
            exp = getSkillGained(toonSkillPtsGained, toon.doId, i)
            needed = ToontownBattleGlobals.Levels[i][ToontownBattleGlobals.LAST_REGULAR_GAG_LEVEL + 1] + ToontownBattleGlobals.UberSkill
            hasUber = 0
            totalExp = exp + toon.experience.getExp(i)
            if toon.inventory.numItem(i, uberIndex) > 0:
                hasUber = 1
            if totalExp >= needed or totalExp >= ToontownBattleGlobals.MaxSkill:
                if toon.inventory.totalProps < toon.getMaxCarry() and not hasUber:
                    uberLevel = ToontownBattleGlobals.LAST_REGULAR_GAG_LEVEL + 1
                    toon.inventory.addItem(i, uberLevel)
                    toon.experience.setExp(i, ToontownBattleGlobals.Levels[i][ToontownBattleGlobals.LAST_REGULAR_GAG_LEVEL + 1])
                else:
                    toon.experience.setExp(i, ToontownBattleGlobals.MaxSkill)
            else:
                if exp > 0:
                    newGagList = toon.experience.getNewGagIndexList(i, exp)
                    toon.experience.addExp(i, amount=exp)
                    toon.inventory.addItemWithList(i, newGagList)
        toon.b_setExperience(toon.experience.makeNetString())
        toon.d_setInventory(toon.inventory.makeNetString())
        toon.b_setAnimState('victory', 1)

        if simbase.air.config.GetBool('battle-passing-no-credit', True):
            if helpfulToons and toon.doId in helpfulToons:
                simbase.air.questManager.toonKilledCogs(toon, suitsKilled, zoneId, activeToonList)
                simbase.air.cogPageManager.toonKilledCogs(toon, suitsKilled, zoneId)
            else:
                BattleExperienceAINotify.debug('toon=%d unhelpful not getting killed cog quest credit' % toon.doId)
        else:
            simbase.air.questManager.toonKilledCogs(toon, suitsKilled, zoneId, activeToonList)
            simbase.air.cogPageManager.toonKilledCogs(toon, suitsKilled, zoneId)

    return
