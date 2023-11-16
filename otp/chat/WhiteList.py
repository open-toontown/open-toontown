from bisect import bisect_left


class WhiteList:

    def __init__(self, wordlist):
        self.words = []
        for line in wordlist:
            self.words.append(line.strip(b'\n\r').lower())

        self.words.sort()
        self.numWords = len(self.words)

    def cleanText(self, text):
        text = text.strip('.,?!')
        text = text.lower().encode('utf-8')
        return text

    def isWord(self, text):
        text = self.cleanText(text)
        i = bisect_left(self.words, text)
        if i == self.numWords:
            return False
        return self.words[i] == text

    def isPrefix(self, text):
        text = self.cleanText(text)
        i = bisect_left(self.words, text)
        if i == self.numWords:
            return False
        return self.words[i].startswith(text)

    def prefixCount(self, text):
        text = self.cleanText(text)
        i = bisect_left(self.words, text)
        j = i
        while j < self.numWords and self.words[j].startswith(text):
            j += 1

        return j - i

    def prefixList(self, text):
        text = self.cleanText(text)
        i = bisect_left(self.words, text)
        j = i
        while j < self.numWords and self.words[j].startswith(text):
            j += 1

        return self.words[i:j]
