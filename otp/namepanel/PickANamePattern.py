

class PickANamePattern:

    def __init__(self, nameStr, gender):
        self._nameStr = nameStr
        self._namePattern = self._compute(self._nameStr, gender)

    def hasNamePattern(self):
        return self._namePattern is not None

    def getNamePattern(self):
        return self._namePattern

    def getNameString(self, pattern, gender):
        nameParts = self._getNameParts(gender)
        invNameParts = []
        for i in range(len(nameParts)):
            invNameParts.append(invertDict(nameParts[i]))

        name = ''
        for i in range(len(pattern)):
            if pattern[i] != -1:
                if len(name):
                    name += ' '
                name += invNameParts[i][pattern[i]]

        return name

    def getNamePartString(self, gender, patternIndex, partIndex):
        nameParts = self._getNameParts(gender)
        invNamePart = invertDict(nameParts[patternIndex])
        return invNamePart[partIndex]

    def _genWordListSplitPermutations(self, words):
        if not len(words):

            return
        if len(words) == 1:

            yield words
            return

        for permutation in self._genWordListSplitPermutations(words[1:]):
            yield [words[0]]+permutation
            yield [(words[0] + ' ')+permutation[0]]+permutation[1:]

    def _genNameSplitPermutations(self, name):
        for splitName in self._genWordListSplitPermutations(name.split()):
            yield splitName

    def _compute(self, nameStr, gender):
        return self._computeWithNameParts(nameStr, self._getNameParts(gender))

    def _computeWithNameParts(self, nameStr, nameParts):
        for splitPermutation in self._genNameSplitPermutations(nameStr):
            pattern = self._recursiveCompute(splitPermutation, nameParts)
            if pattern is not None:
                return pattern

        return

    def _getNameParts(self, gender):
        pass

    def _recursiveCompute(self, words, nameParts, wi = 0, nwli = 0, pattern = None):
        if wi >= len(words):
            return pattern
        if nwli >= len(nameParts):
            return
        if words[wi] in nameParts[nwli]:
            if pattern is None:
                pattern = [-1] * len(nameParts)
            word2index = nameParts[nwli]
            newPattern = pattern[:]
            newPattern[nwli] = word2index[words[wi]]
            result = self._recursiveCompute(words, nameParts, wi + 1, nwli + 1, newPattern)
            if result:
                return result
        return self._recursiveCompute(words, nameParts, wi, nwli + 1, pattern)


class PickANamePatternTwoPartLastName(PickANamePattern):

    def getNameString(self, pattern, gender):
        name = PickANamePattern.getNameString(self, pattern, gender)
        if pattern[-2] != -1:
            words = name.split()
            name = ''
            for word in words[:-2]:
                if len(name):
                    name += ' '
                name += word

            if len(name):
                name += ' '
            name += words[-2]
            if words[-2] in set(self._getLastNameCapPrefixes()):
                name += words[-1].capitalize()
            else:
                name += words[-1]
        return name

    def _getLastNameCapPrefixes(self):
        return []

    def _compute(self, nameStr, gender):
        nameParts = self._getNameParts(gender)
        combinedNameParts = nameParts[:-2]
        combinedNameParts.append({})
        combinedIndex2indices = {}
        lastNamePrefixesCapped = set(self._getLastNameCapPrefixes())
        k = 0
        for first, i in nameParts[-2].items():
            capitalize = first in lastNamePrefixesCapped
            for second, j in nameParts[-1].items():
                combinedLastName = first
                if capitalize:
                    combinedLastName += second.capitalize()
                else:
                    combinedLastName += second
                combinedNameParts[-1][combinedLastName] = k
                combinedIndex2indices[k] = (i, j)
                k += 1

        pattern = self._computeWithNameParts(nameStr, combinedNameParts)
        if pattern:
            combinedIndex = pattern[-1]
            pattern = pattern[:-1]
            pattern.append(-1)
            pattern.append(-1)
            if combinedIndex != -1:
                pattern[-2] = combinedIndex2indices[combinedIndex][0]
                pattern[-1] = combinedIndex2indices[combinedIndex][1]
        return pattern
