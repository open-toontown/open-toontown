from toontown.toonbase import ToontownBattleGlobals

def genRewardDicts(entries):
    toonRewardDicts = []
    for toonId, origExp, earnedExp, origQuests, items, missedItems, origMerits, merits, parts in entries:
        if toonId != -1:
            dict = {}
            toon = base.cr.doId2do.get(toonId)
            if toon == None:
                continue
            dict['toon'] = toon
            dict['origExp'] = origExp
            dict['earnedExp'] = earnedExp
            dict['origQuests'] = origQuests
            dict['items'] = items
            dict['missedItems'] = missedItems
            dict['origMerits'] = origMerits
            dict['merits'] = merits
            dict['parts'] = parts
            toonRewardDicts.append(dict)

    return toonRewardDicts
